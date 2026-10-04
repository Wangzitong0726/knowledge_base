# -*- coding: utf-8 -*-
"""
全库向量化（带检查点，可断点续跑）

**为什么另写一个，而不是改 build_vectors.py**：`build_vectors.py` 是阶段 0 的
验收脚本，它的三关数值（0.7862/0.3498/0.2121）是本项目的基准，不能动。
而它有个**致命的结构问题**：`--save-every` 参数声明了却**从未被使用**，
主流程是一句 `e.encode(整库)`，全部算完才写盘。

后果实测过：第一次全库跑，跑到 **81,344 / 81,895（99.3%）** 时 CUDA OOM，
**约 60 分钟的 GPU 全部作废，一个文件都没留下**
（81,344 块 ÷ 累计 22.7 块/秒 ≈ 3,583 秒）。
`--save-every` 给了「有检查点」的错觉，实际没有——**声明了却没接线的开关，
比没有这个开关更危险**，因为它会让人放弃另做备份。

本脚本三条硬改进：
1. **真检查点**：先建 `(N,1024)` 的 memmap，每批算完**直接写进盘**，
   进度另存 json。中途崩了，重跑自动从断点接上。
2. **按 token 预算分批**，不按条数。块长差别大（中位 432 token、最大 2057），
   按条数分批会让「一批 64 条」在长块段变成「一批 6.5 万 token」——OOM 就是这么来的。
3. **OOM 就地折半重试**，不整库重来。
4. `expandable_segments:True`：报错信息自己点名了这个（8.28GB 保留却未分配 = 碎片）。

结果与 `build_vectors.py` 同构（同一 `Embedder`、同一 last-token pooling、
同一 fp32、同一归一化），只是**分片落盘**，语义完全一致。
"""
import os

# ⚠️ 必须在 import torch **之前**设，否则不生效
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

DIM = 1024
TOKEN_BUDGET = 16384      # 每批的 token 上限（实测 64 条长块 ≈ 6.5 万 token 会 OOM）
MAX_BS = 128


def shard(texts, budget=TOKEN_BUDGET, max_bs=MAX_BS, order=None):
    """按 token 预算切批。返回 [(原始下标数组, 文本列表), ...]。

    调用方应先按长度排序（order），这样每批内部长度相近，padding 浪费最小，
    且**长块集中在少数几批**——真撑不住时只折半那几批，不牵连全库。
    """
    order = order if order is not None else list(range(len(texts)))
    out, cur, curtok = [], [], 0
    for i in order:
        n = max(1, len(texts[i]) // 2)          # 用字数粗估 token，够切批用了
        if cur and (curtok + n > budget or len(cur) >= max_bs):
            out.append(cur)
            cur, curtok = [], 0
        cur.append(i)
        curtok += n
    if cur:
        out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=str(ROOT / "knowledge_base" / "chunks.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "knowledge_base" / "vectors.npy"))
    ap.add_argument("--budget", type=int, default=TOKEN_BUDGET)
    ap.add_argument("--max-length", type=int, default=2048,
                    help="模型支持 32768；实测只有 69 块超 1024 个 token，"
                         "默认放到 2048 即全覆盖。注意 argparse 会把 help 里的 "
                         "百分号当格式符，写数字别带百分号")
    ap.add_argument("--restart", action="store_true", help="丢弃进度从头跑")
    args = ap.parse_args()

    from embed import Embedder

    chunks, out = Path(args.chunks), Path(args.out)
    if out.suffix.lower() != ".npy":
        out = out.parent / (out.name + ".npy")
    prog_p = out.parent / (out.stem + ".progress.json")

    rows = []
    with open(chunks, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    texts = [r["text"] for r in rows]
    N = len(texts)
    print(f"块 {N:,}  平均 {sum(map(len,texts))/N:.0f} 字")

    # 进度：只认「同一份 chunks」的进度，换语料就从头来
    import hashlib
    h = hashlib.sha256()
    with open(chunks, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    fp = h.hexdigest()
    prog = {}
    if prog_p.exists() and not args.restart:
        prog = json.loads(prog_p.read_text())
        if prog.get("chunks_sha256") != fp or prog.get("n") != N:
            print("  语料变了，进度作废，从头跑")
            prog = {}

    already = int(prog.get("done", 0))
    # 长度升序：同批长度相近，padding 不浪费；长块集中到最后
    order = sorted(range(N), key=lambda i: len(texts[i]))
    batches = shard(texts, args.budget, MAX_BS, order)
    print(f"分 {len(batches):,} 批（token 预算 {args.budget:,}，每批 ≤{MAX_BS} 条）")

    e = Embedder()
    ml = args.max_length
    if out.exists() and already:
        mm = np.lib.format.open_memmap(out, mode="r+")
    else:
        mm = np.lib.format.open_memmap(out, mode="w+", dtype=np.float32, shape=(N, DIM))
        already = 0

    # 找到断点所在的批号
    # ⚠️ start 初值必须是 len(batches) 而不是 0：若 already == N（已全跑完），
    # 循环里没有任何一批满足「已做 + 本批 > N」，于是 break 永不触发、
    # start 停在 0 —— **一跑完就自动从头重跑一遍**。空跑两小时还看不出错。
    done_items, start = 0, len(batches)
    for bi, idxs in enumerate(batches):
        if done_items + len(idxs) > already:
            start = bi
            break
        done_items += len(idxs)

    t0 = time.time()
    written = already
    for bi in range(start, len(batches)):
        idxs = batches[bi]
        # OOM 就地折半重试，不整库重来
        stack = [idxs]
        while stack:
            cur = stack.pop()
            try:
                v = e.encode([texts[i] for i in cur], batch_size=len(cur),
                             length_bucket=False, max_length=ml, verbose=False)
                mm[cur] = v
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                if len(cur) == 1:
                    raise
                mid = len(cur) // 2
                stack.append(cur[mid:])
                stack.append(cur[:mid])
                print(f"  ⚠️ OOM，批 {bi} 折半为 {mid}+{len(cur)-mid} 重试")
        written += len(idxs)
        if bi % 20 == 0 or written == N:
            mm.flush()
            prog_p.write_text(json.dumps(
                {"chunks_sha256": fp, "n": N, "done": written,
                 "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=2))
            el = time.time() - t0
            rate = (written - already) / el if el > 0 else 0
            eta = (N - written) / rate if rate > 0 else 0
            print(f"  {written:,}/{N:,}  {rate:.1f} 块/秒  剩 {eta/60:.1f} 分钟", flush=True)

    mm.flush()
    prog_p.write_text(json.dumps(
        {"chunks_sha256": fp, "n": N, "done": N,
         "updated": time.strftime("%Y-%m-%d %H:%M:%S"), "complete": True}, indent=2))

    # 落盘后回读抽查（不是重读全库——8 万个 1024 维读一遍没必要）
    back = np.load(out, mmap_mode="r")
    norms = np.array([np.linalg.norm(np.asarray(back[i])) for i in
                      np.linspace(0, N - 1, 200).astype(int)])
    print(f"\n✓ {out}  shape={back.shape}  抽查范数 "
          f"min={norms.min():.6f} max={norms.max():.6f}（应均≈1.0）")


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    main()

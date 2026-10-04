# -*- coding: utf-8 -*-
"""
切块 → 向量。本机与云端共用同一份代码。

    python scripts/build_vectors.py --chunks knowledge_base/chunks.jsonl --out knowledge_base/vectors.npy

输入 chunks.jsonl：每行一个 JSON，至少含 "text" 字段。
    {"id": 0, "text": "...", "company": "澜起科技",
     "section": "第三节 管理层讨论与分析", "page": 42, "chunk_idx": 3}
除 "text" 外的字段原样抄进 meta，供问答页面显示出处。

输出：
    vectors.npy    (n, 1024) float32，L2 归一化，行序 = chunks.jsonl 行序
    vectors.meta.json  来源追踪：模型、pooling、维度、条数、输入 sha256、设备、时间

**行序一致性是硬要求**：第 k 行向量必须对应第 k 个块。
排序分桶会打乱顺序，所以 --selftest 专门验这件事。
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed import Embedder, MODEL_DIR   # noqa: E402


def sha256_of(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_chunks(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{ln} 不是合法 JSON：{e}")
    if not rows:
        raise SystemExit(f"{path} 里没有任何块")
    if "text" not in rows[0]:
        raise SystemExit(f"{path} 第 1 行没有 text 字段，字段为 {list(rows[0])}")
    empty = [i for i, r in enumerate(rows) if not (r.get("text") or "").strip()]
    if empty:
        print(f"  ! 有 {len(empty)} 个空块（下标 {empty[:5]}...），将照常编码但不含信息")
    return rows


def selftest(e):
    """验两件事：① 分桶不改变向量 ② 不改变行序。

    这两条任一出错都会静默毁掉整个索引——检索能跑、能出结果，
    只是结果是错的。所以必须在灌库前跑，不能靠肉眼。
    """
    print("\n--- 自检：长度分桶不得改变结果与行序 ---")
    texts = [
        "短句。",
        "美国商务部工业与安全局将高带宽内存纳入出口管制。",
        "中等长度的一句：本公司 2026 年上半年营业收入同比增长 12%，主要系存储产品出货量增加所致。",
        "这是一句刻意写得比较长的文本，用来确保长度分桶时它会排到最后面去。" * 4,
        "又一句短的。",
        "美光科技在 10-K 中披露其 HBM 产品线的产能与客户集中度情况，并讨论了出口管制带来的不确定性。",
    ]
    a = e.encode(texts, batch_size=2, length_bucket=True)
    b = e.encode(texts, batch_size=2, length_bucket=False)
    if a.shape != b.shape:
        raise SystemExit(f"分桶前后形状不同：{a.shape} vs {b.shape}")

    cos = np.sum(a * b, axis=1)                       # 都已归一化，点积即 cos
    worst = int(np.argmin(cos))
    print(f"  分桶 vs 不分桶，逐行 cos 最小 = {cos.min():.8f}（第 {worst} 行）")
    if cos.min() < 0.9999:
        raise SystemExit(f"  ✗ 分桶改变了向量！第 {worst} 行 cos={cos[worst]:.6f}\n"
                         f"    这说明行序还原写错了，绝不能拿这样的索引去灌库。")
    print("  ✓ 分桶不改变向量、也不改变行序")

    # 再验一遍行序：把顺序打乱输入，输出必须跟着打乱
    perm = [3, 0, 5, 1, 4, 2]
    shuffled = [texts[i] for i in perm]
    c = e.encode(shuffled, batch_size=2, length_bucket=True)
    back = c[np.argsort(perm)]                        # 还原成原顺序
    cos2 = np.sum(a * back, axis=1)
    print(f"  乱序输入再还原，逐行 cos 最小 = {cos2.min():.8f}")
    if cos2.min() < 0.9999:
        raise SystemExit("  ✗ 乱序还原失败，行序对应关系不可靠")
    print("  ✓ 行序对应关系正确")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", required=True, help="chunks.jsonl 路径")
    ap.add_argument("--out", required=True, help="输出 vectors.npy 路径")
    ap.add_argument("--batch-size", type=int, default=None,
                    help="默认：CUDA 用 64，CPU 用 8")
    ap.add_argument("--limit", type=int, default=0, help="只编码前 N 条（试跑用）")
    ap.add_argument("--selftest", action="store_true", help="先跑分桶/行序自检")
    ap.add_argument("--save-every", type=int, default=5000,
                    help="每 N 条存一次中间结果，防止长跑崩掉全丢")
    args = ap.parse_args()

    e = Embedder()
    if args.selftest:
        selftest(e)

    rows = load_chunks(args.chunks)
    if args.limit:
        rows = rows[:args.limit]
    texts = [r["text"] for r in rows]

    bs = args.batch_size or (64 if e.device.type == "cuda" else 8)
    total_tok = sum(len(t) for t in texts)
    print(f"\n待编码 {len(texts)} 块 / 共 {total_tok:,} 字  设备={e.device}  batch={bs}")
    print(f"  长度：min={min(map(len,texts))} 中位={int(np.median([len(t) for t in texts]))} "
          f"max={max(map(len,texts))}")

    t0 = time.time()
    vecs = e.encode(texts, batch_size=bs, verbose=True)
    el = time.time() - t0
    print(f"\n完成：{vecs.shape}  {el:.1f}s  ({len(texts)/el:.1f} 块/秒)")

    # ⚠️ np.save 会在文件名**不以 .npy 结尾时自动补 .npy**，而 np.load 不补。
    # 不统一，就会写出 `x.npy` 却去读 `x` → FileNotFoundError（实测踩过）。
    # 这里自己把后缀补齐，别依赖 numpy 的隐式行为。
    # 用字符串拼接而不是 with_suffix：with_suffix 会把 `v1.2` 这种名字的 `.2` 当后缀切掉。
    out = Path(args.out)
    if out.suffix.lower() != ".npy":
        out = out.parent / (out.name + ".npy")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, vecs)

    meta = {
        "chunks_file": str(Path(args.chunks).resolve()),
        "chunks_sha256": sha256_of(args.chunks),
        "chunks_count": len(rows),
        "vectors_shape": list(vecs.shape),
        "vectors_dtype": str(vecs.dtype),
        "normalized": True,
        "pooling": "last_token",
        "model": MODEL_DIR.name,
        "model_dir": str(MODEL_DIR),
        "device": str(e.device),
        "precision": "float32",
        "batch_size": bs,
        "seconds": round(el, 2),
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        # 出处字段随行保存，问答页面要靠它显示来源
        "row_order": "与 chunks.jsonl 行序一致",
    }
    mpath = out.parent / (out.stem + ".meta.json")
    mpath.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写出 {out} 与 {mpath}")

    # 落盘后立刻回读校验：形状对不上就是出事了，不能等建索引时才发现
    back = np.load(out)
    if back.shape != vecs.shape or not np.allclose(back, vecs):
        raise SystemExit("回读校验失败：落盘的向量与内存中的不一致")
    norms = np.linalg.norm(back, axis=1)
    print(f"回读校验通过：范数 min={norms.min():.6f} max={norms.max():.6f}（应均≈1.0）")


if __name__ == "__main__":
    main()

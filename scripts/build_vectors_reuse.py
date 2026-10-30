# -*- coding: utf-8 -*-
"""增量重建向量：**文本没变的行直接复用旧向量**，只算变了的那部分。

为什么可以复用（这不是偷懒，是量出来的）：

  · `vectors.npy` 是在云端 RTX 3090 上算的；本机 CPU 重算同样的文本，
    余弦 min = 0.99999988、mean = 1.00000000、无一低于 0.9999（32 个抽样，
    覆盖全部来源与长度区间，含最长的几个——截断边界在最长处）。
    证据与可复跑的办法见 `_probe/parity_now.py` 的输出，以及本脚本收尾的复验。
  · 模型 fp32、last-token pooling、L2 归一化，**没有随机性**：同文本同向量。
  · 旧的行对应关系从 `chunks.sqlite` 取（它的 row 就是 chunks.jsonl 行号），
    而它逐行的文本哈希与留档一致——所以「哈希 → 旧行号」是可靠的。

为什么要增量：本机没有 NVIDIA GPU（只有 AMD 集显），CPU 实测 **0.18 块/秒**，
全库 81,340 块要 125 小时；只算变更的 14,172 个文本约 22 小时，还能断点续跑。

⚠️ **顺序有硬约束**：必须在 `build_store.py` 用新 chunks 覆盖 `chunks.sqlite`
    **之前**跑。旧行号只存在于那份 sqlite 里。

用法：
    ./.venv/Scripts/python.exe scripts/build_vectors_reuse.py --plan-only
    ./.venv/Scripts/python.exe scripts/build_vectors_reuse.py            # 可反复重跑，自动续
"""
import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MAX_LENGTH = 2048          # 与全库一致（embed.encode 的默认 1024 是另一回事）
BATCH = 8
CHUNK = 256                # 每写这么多条落一次盘（断点粒度）
DIM = 1024


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def load_new(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_old_index(sqlite_path):
    """旧库：哈希 → 旧行号。"""
    con = sqlite3.connect(str(sqlite_path))
    m = {}
    n = 0
    for row, text in con.execute("SELECT row, text FROM chunks ORDER BY row"):
        h = sha1(text or "")
        if h not in m:
            m[h] = row
        n = max(n, row + 1)
    con.close()
    return m, n


def build_plan(new, old_map):
    """算出「哪些行复用、哪些行要算」。

    返回 `(src, missing, n_reuse)`：`src[i]` 是 `('reuse', 旧行号)` 或
    `('calc', 待算序号)`；`missing` 是**按首次出现顺序**去重后的待算文本。

    ⚠️ 这个顺序就是 `missing.npy` 的**行序契约**。凡是「出机算完再传回来」的做法，
       传回来的 `missing.npy` 必须与这里算出的 `missing` **逐条同序**——
       而 `missing` 依赖 `chunks.jsonl` 与 `chunks.sqlite` 的当前内容。
       所以出机前要把这份列表**冻结成文件**，回来时用指纹核对（`plan_fingerprint`）。
       对不上必须硬失败：错位的向量不报错，只会让每条引用指向隔壁块的出处。

    抽成独立函数，是为了让「算计划」与「导出计划」走**同一段代码**——
    各写一遍的话，日后改了一处、另一处没改，导出的那份就悄悄不再是真实的那份。
    """
    src, missing, miss_idx = [], [], {}
    n_reuse = 0
    for r in new:
        h = sha1(r.get("text") or "")
        k = old_map.get(h)
        if k is not None:
            src.append(("reuse", k))
            n_reuse += 1
        else:
            j = miss_idx.get(h)
            if j is None:
                j = len(missing)
                miss_idx[h] = j
                missing.append(r["text"])
            src.append(("calc", j))
    return src, missing, n_reuse


def plan_fingerprint(missing):
    """计划指纹：待算文本**逐条按序**连起来的 sha1。

    只指纹「内容 + 顺序」，不掺块数——要防的正是「块数碰巧一样、
    但对应关系已经变了」这种**看着没事**的错位。
    """
    return hashlib.sha1("\n".join(missing).encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=str(ROOT / "knowledge_base" / "chunks.jsonl"))
    ap.add_argument("--sqlite", default=str(ROOT / "knowledge_base" / "index" / "chunks.sqlite"))
    ap.add_argument("--old-vectors", default=str(ROOT / "knowledge_base" / "vectors.npy"))
    ap.add_argument("--out", default=str(ROOT / "knowledge_base" / "vectors.npy"))
    ap.add_argument("--work", default=str(ROOT / "knowledge_base" / "vectors_incremental"))
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--dump-missing", default=None, metavar="PATH",
                    help="把待算文本按**行序契约**冻结成本文件（每行一条 JSON 字符串），"
                         "并把计划指纹写到同名的 .sha1。出机算 GPU 时带这个文件走，"
                         "不必搬 chunks.jsonl / sqlite / 旧向量。")
    ap.add_argument("--recheck", type=int, default=16,
                    help="收尾复验：抽这么多条复用向量，本机重算比对余弦")
    args = ap.parse_args()

    work = Path(args.work)
    work.mkdir(exist_ok=True)
    part = work / "missing.npy"          # 未变行之外的向量，按「待算序号」排列
    prog = work / "progress.json"

    t0 = time.time()
    new = load_new(args.chunks)
    old_map, n_old = load_old_index(args.sqlite)
    oldv = np.load(args.old_vectors, mmap_mode="r")
    print("新块 %d ；旧库 %d 块（%s）；旧向量 %s"
          % (len(new), n_old, Path(args.sqlite).name, oldv.shape))
    if oldv.shape[0] != n_old:
        raise SystemExit("旧向量行数与旧库行数不符，不能复用")

    src, missing, n_reuse = build_plan(new, old_map)
    fp = plan_fingerprint(missing)

    print("新块 %d 行：复用 %d（%.2f%%)，需算 %d 行 / %d 个不同文本"
          % (len(new), n_reuse, 100 * n_reuse / len(new),
             len(new) - n_reuse, len(missing)))
    print("（%d 个不同文本里有 %d 处重复，只算一次）"
          % (len(missing), (len(new) - n_reuse) - len(missing)))
    print("计划指纹 %s…" % fp[:16])

    # ── 出机用：把冻结的计划导出成文件（出机算向量的唯一输入）──
    if args.dump_missing:
        dp = Path(args.dump_missing)
        with open(dp, "w", encoding="utf-8") as f:
            for t in missing:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        dp.with_suffix(dp.suffix + ".sha1").write_text(fp, encoding="utf-8")
        print("已导出 %d 条待算文本 → %s（%.1f MB）"
              % (len(missing), dp, dp.stat().st_size / 1e6))
        print("指纹同时写到 %s" % dp.with_suffix(dp.suffix + ".sha1").name)
        print("⚠️ 出机期间**不要动 chunks.jsonl 或 chunks.sqlite**——"
              "动了这个指纹就对不上，传回来的 missing.npy 会被拒绝。")

    if args.plan_only:
        return 0

    # ── 待算向量：定长 memmap + 进度计数，崩溃后从上次落盘处续 ──
    fp_path = work / "missing.sha1"
    have_fp = fp_path.read_text(encoding="utf-8").strip() if fp_path.exists() else None
    can_reuse = (part.exists()
                 and np.load(part, mmap_mode="r").shape[0] == len(missing))
    if can_reuse and have_fp is not None and have_fp != fp:
        raise SystemExit(
            "！计划指纹对不上，拒绝复用 %s：\n"
            "   现存 missing.npy 是给指纹 %s… 的计划算的\n"
            "   当前计划指纹是       %s…\n"
            "   说明 chunks.jsonl / chunks.sqlite 变过了，而这份 missing.npy 的\n"
            "   行序已经与当前 missing 列表不符。继续用会**静默错位**：不报错，\n"
            "   只会让每条引用指向隔壁块的出处。\n"
            "   要么把 chunks.jsonl 复原，要么删掉 missing.npy 与 progress.json 重算。"
            % (part.name, (have_fp or "")[:16], fp[:16]))
    if not can_reuse:
        mm = np.lib.format.open_memmap(part, mode="w+", dtype=np.float32,
                                       shape=(len(missing), DIM))
        mm.flush()
        prog.write_text(json.dumps({"done": 0}), encoding="utf-8")
    mm = np.load(part, mmap_mode="r+")
    done = json.loads(prog.read_text(encoding="utf-8"))["done"] if prog.exists() else 0
    fp_path.write_text(fp, encoding="utf-8")       # 比较完再写，别把自己刚写的当依据
    print("待算 %d 条；已完成 %d 条" % (len(missing), done))

    if done < len(missing):
        from embed import Embedder
        e = Embedder()
        t1 = time.time()
        i = done
        while i < len(missing):
            j = min(i + CHUNK, len(missing))
            v = e.encode(missing[i:j], batch_size=BATCH, max_length=MAX_LENGTH)
            mm[i:j] = v
            mm.flush()
            i = j
            prog.write_text(json.dumps({"done": i}), encoding="utf-8")
            el = time.time() - t1
            rate = (i - done) / max(el, 1e-9)
            left = (len(missing) - i) / max(rate, 1e-9)
            print("  已算 %d/%d  %.3f 块/秒  剩余约 %.1f 小时"
                  % (i, len(missing), rate, left / 3600), flush=True)
        del e

    # ── 组装：逐行取「复用」或「新算」 ──
    out = np.empty((len(new), DIM), dtype=np.float32)
    for i, (kind, k) in enumerate(src):
        out[i] = oldv[k] if kind == "reuse" else mm[k]
    del oldv, mm                       # 关掉对旧文件的 mmap，否则 Windows 上换不掉它
    # **先写临时文件再原子替换**：`--out` 默认就是旧 vectors.npy 自己，
    # 而旧向量是这一轮复用的来源——直接覆盖写，一旦中途失败就两头都没了。
    tmp = Path(str(args.out) + ".tmp")
    with open(tmp, "wb") as fh:
        np.save(fh, out)               # np.save(路径) 会自作主张补 `.npy`，这里传文件对象
    tmp.replace(args.out)
    print("\n写出 %s  shape=%s  %.1f MB" % (args.out, out.shape, out.nbytes / 1e6))

    # ── 复验：复用向量与「本机现在重算」的一致性 ──
    par = {}
    if args.recheck > 0:
        idx = [i for i, (kind, _k) in enumerate(src) if kind == "reuse"]
        step = max(1, len(idx) // args.recheck)
        pick = idx[::step][:args.recheck]
        from embed import Embedder
        e = Embedder()
        got = e.encode([new[i]["text"] for i in pick], batch_size=BATCH, max_length=MAX_LENGTH)
        cos = (got * out[pick]).sum(axis=1)
        par = {"n": len(pick), "cos_min": float(cos.min()),
               "cos_mean": float(cos.mean()), "below_0.9999": int((cos < 0.9999).sum())}
        print("复验 %d 条复用向量：余弦 min=%.8f mean=%.8f  低于 0.9999 的 %d 条"
              % (len(pick), cos.min(), cos.mean(), par["below_0.9999"]))

    meta = {
        "file": str(Path(args.out).relative_to(ROOT)),
        "shape": list(out.shape), "dtype": "float32", "normalized": True,
        "pooling": "last_token", "model": "Qwen3-Embedding-0.6B",
        "precision": "float32", "max_length": MAX_LENGTH,
        "row_order": "与 chunks.jsonl 行序一致",
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": "复用云端 RTX 3090 + 本机 CPU 增量",
        "rows_reused": n_reuse, "rows_computed": len(new) - n_reuse,
        "distinct_texts_computed": len(missing),
        "reuse_parity": par,
        "note": "复用行取自旧 vectors.npy 中文本哈希完全相同的行；"
                "parity 见 reuse_parity（本机 CPU 重算同一文本的余弦）",
    }
    Path(str(args.out).replace(".npy", ".meta.json")).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("元数据已写；总用时 %.1f 分钟" % ((time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

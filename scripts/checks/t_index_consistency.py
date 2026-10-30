# -*- coding: utf-8 -*-
"""验收：四份产物说的是不是**同一个语料**（块 / 向量 / sqlite / BM25 索引）。

**为什么要这个脚本**（2026-10-30 实测撞到的真事故）：
去重（`dedupe_sources.py --apply`）把 81,340 块改成 67,210 块，向量与 sqlite 都跟着重建了，
**只有 BM25 索引没重建**（还停在 2026-10-04 的 81,895 块）。
后果不是报错，而是：
  · 索引里 14,948 个 `chunk_id` 在 sqlite 里已经不存在（去重掉的 szse）；
  · 现行语料里有 263 块**根本不进 BM25 通道**——字面检索永远看不见它们。
于是「10/10」是这样跑出来的：**旧文本的 BM25** 配 **新语料的向量**，
两路融合时各自看到的库不是同一个。这类错在页面上完全正常，只能靠对账发现。

**四份产物必须同时成立**（行号是绑死的，顺序错一位就全错）：

    chunks.jsonl 的行序 = vectors.npy 的行序 = chunks.sqlite 的 row
    bm25_docs.json 的 chunk_id 集合 = chunks.jsonl 的 chunk_id 集合

用法（系统 py 即可，只要 numpy/sqlite3）：
    C:/Python314/python.exe scripts/checks/t_index_consistency.py
退出码 0 = 四份一致；1 = 有不一致（打印该重建哪个）。
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]   # scripts/checks/ → 项目根
KB = ROOT / "knowledge_base"
CHUNKS = KB / "chunks.jsonl"
VECTORS = KB / "vectors.npy"
DB = KB / "index" / "chunks.sqlite"
IDX = KB / "index"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    problems = []

    # ── ① chunks.jsonl：块数 + chunk_id 集合 ──
    cids, n_chunk = [], 0
    with open(CHUNKS, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if "__meta__" in r:
                continue
            n_chunk += 1
            cids.append(r["chunk_id"])
    print(f"chunks.jsonl      : {n_chunk:,} 块")

    # ── ② vectors.npy：行数必须等于块数（否则块-向量错配）──
    m = np.load(VECTORS, mmap_mode="r")
    print(f"vectors.npy       : {m.shape[0]:,} 行 × {m.shape[1]} 维 {m.dtype}")
    if m.shape[0] != n_chunk:
        problems.append("向量行数 %d ≠ 块数 %d → 重跑 embed_corpus.py"
                        % (m.shape[0], n_chunk))

    # ── ③ chunks.sqlite：行数 + chunk_id 集合 ──
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    n_row = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    db_ids = {r[0] for r in con.execute("SELECT chunk_id FROM chunks")}
    con.close()
    print(f"chunks.sqlite     : {n_row:,} 行")
    if n_row != n_chunk:
        problems.append("sqlite 行数 %d ≠ 块数 %d → 重跑 build_store.py --force"
                        % (n_row, n_chunk))
    if db_ids != set(cids):
        problems.append("sqlite 与 chunks.jsonl 的 chunk_id 集合不同（差 %d）"
                        % len(set(cids) ^ db_ids))

    # ── ④ BM25：n_doc + chunk_id 集合 ──
    meta = json.loads((IDX / "bm25_meta.json").read_text(encoding="utf-8"))
    bm_ids = set(json.loads((IDX / "bm25_docs.json").read_text(encoding="utf-8")))
    print(f"bm25 索引         : n_doc={meta['n_doc']:,}，docs={len(bm_ids):,}，"
          f"built_at={meta.get('built_at')}")
    if meta["n_doc"] != n_chunk:
        problems.append("BM25 n_doc %d ≠ 块数 %d → 重跑 bm25.py build --force"
                        % (meta["n_doc"], n_chunk))
    only_idx, only_corpus = bm_ids - set(cids), set(cids) - bm_ids
    if only_idx:
        problems.append("BM25 里有 %d 个块已不在语料（去重/重切后没重建索引）"
                        % len(only_idx))
    if only_corpus:
        problems.append("语料里有 %d 个块不在 BM25 里（这些块字面检索永远召不回）"
                        % len(only_corpus))

    print()
    if problems:
        for p in problems:
            print("❌ " + p)
        return 1
    print("✅ 四份产物一致：块 / 向量 / sqlite / BM25 是同一个语料，行序绑定成立")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

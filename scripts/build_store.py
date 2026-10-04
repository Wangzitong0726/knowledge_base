# -*- coding: utf-8 -*-
"""
阶段 4 前置 · 把 chunks.jsonl 装进 sqlite

**为什么必须建这一步，而不是每次现读 jsonl**：
检索返回的是「第 i 行」，而向量文件的第 i 行是同一个块。这条对应关系是
**按行号**绑的，不是按 chunk_id 查的。Python 里重读 jsonl 建 dict 会吃掉几百 MB，
再想按行号取回原文又得整份扫一遍。sqlite 一次建好，之后按 row 或按 chunk_id 都是 O(1)。

⚠️ **row 主键 = chunks.jsonl 的行序号（从 0 起）**，与 `vectors.npy` 的行严格同序。
建库时校验行数必须等于向量行数，对不上直接抛错——
**错位的向量不会报错，只会让每个答案都引到隔壁块的出处**，
这种错在最终页面上看起来完全正常（数字是真的、出处是真的、只是配错了）。
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "knowledge_base" / "chunks.jsonl"
DB = ROOT / "knowledge_base" / "index" / "chunks.sqlite"

COLS = ["row", "chunk_id", "doc_id", "source", "company", "title", "date",
        "url", "file", "unit", "page_start", "page_end", "section", "seq",
        "chars", "n_units", "text"]


def build(chunks=CHUNKS, db=DB, vectors=None, force=False):
    chunks, db = Path(chunks), Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        if not force:
            print(f"{db} 已存在，跳过（--force 重建）")
            return
        db.unlink()

    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=OFF")
    con.execute(f"CREATE TABLE chunks ({', '.join(_ddl())})")
    con.execute("CREATE UNIQUE INDEX ix_cid ON chunks(chunk_id)")

    rows, n = [], 0
    with open(chunks, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            rows.append(tuple(
                r.get(c) if c != "row" else n for c in COLS))
            n += 1
            if len(rows) >= 2000:
                con.executemany(f"INSERT INTO chunks VALUES ({','.join('?'*len(COLS))})", rows)
                rows.clear()
    if rows:
        con.executemany(f"INSERT INTO chunks VALUES ({','.join('?'*len(COLS))})", rows)
    con.commit()

    # 行数与向量行数必须严丝合缝
    if vectors and Path(vectors).exists():
        vrow = np.load(vectors, mmap_mode="r").shape[0]
        if vrow != n:
            raise RuntimeError(
                f"向量 {vrow} 行 ≠ 块 {n} 行 —— 拒绝建库。"
                f"错位的向量不会报错，只会让答案引用隔壁块的出处。")
        print(f"  向量行数核对：{vrow} = 块数 ✅")
    con.execute("CREATE INDEX ix_src ON chunks(source, company)")
    con.commit()

    size = db.stat().st_size / 1048576
    print(f"✓ {db}  {n:,} 块  {size:.0f} MB")
    con.close()
    return n


def _ddl():
    t = {"row": "INTEGER PRIMARY KEY", "chunk_id": "TEXT NOT NULL",
         "doc_id": "TEXT", "source": "TEXT", "company": "TEXT", "title": "TEXT",
         "date": "TEXT", "url": "TEXT", "file": "TEXT", "unit": "TEXT",
         "page_start": "INT", "page_end": "INT", "section": "TEXT",
         "seq": "INT", "chars": "INT", "n_units": "INT", "text": "TEXT"}
    return [f"{c} {t[c]}" for c in COLS]


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    build(force="--force" in sys.argv)

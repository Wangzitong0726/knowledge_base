# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
Q4 = "江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？"
T = 20749
import bm25 as B
try:
    toks = B.tokenize("营业总收入 营业收入 口径")
    print("切词:", toks)
    for t in toks:
        print(f"   词表含 {t!r}: {t in R.bm.vocab}")
except Exception as e:
    print("切词失败:", e)
for tag, q in [("原问题", Q4),
               ("直接问", "江波龙 合并利润表 营业总收入"),
               ("口径词", "营业总收入 和 营业收入 口径区别")]:
    b, d, _ds, _ = R._rank_one(q)
    br = b.get(T); dr = d.get(T)
    print(f"  {tag:<8} row20749 bm25={br if br is not None else '>100'} "
          f"dense={dr if dr is not None else '>100'}")
res = R.search(Q4, k=8, expand=True)
print("\n  Q4 前 8 的 row:", [r["row"] for r in res])
print("  20749 在不在前 8:", 20749 in [r["row"] for r in res])

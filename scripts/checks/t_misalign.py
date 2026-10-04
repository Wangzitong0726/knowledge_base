# -*- coding: utf-8 -*-
"""量化「标签盖错」现象：同一标签在**一块之内**紧挨着 ≥3 个数字出现，说明它被当成了
多个值的公共标签（真标签是别处的裸词）。这是表格拍平时列错位的可测指纹。"""
import sys, re, collections
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
PAIR = re.compile(r"([一-鿿]{2,10})\s+(\d[\d,]*\.\d{2})")
tot = bad = 0
by_src = collections.Counter()
worst = []
cur = R.con.execute("SELECT row,source,company,section,text FROM chunks "
                    "WHERE source IN ('cninfo','szse') AND section LIKE '%财务报表%'")
for r in cur:
    tot += 1
    labs = collections.Counter(m.group(1) for m in PAIR.finditer(r["text"]))
    if not labs: continue
    lab, c = labs.most_common(1)[0]
    if c >= 3:
        bad += 1
        by_src[r["source"]] += 1
        worst.append((c, r["row"], r["company"], lab, r["section"]))
print(f"财报类块（cninfo+szse，section 含「财务报表」）：{tot}")
print(f"其中同一标签紧贴 ≥3 个数字（疑似盖错）：{bad}  占比 {bad/max(tot,1):.1%}")
print("按来源：", dict(by_src))
print("\n最严重的 8 例：")
for c, row, co, lab, sec in sorted(worst, reverse=True)[:8]:
    print(f"   标签「{lab}」重复 {c} 次  row={row}  {co}  §{sec}")

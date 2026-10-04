# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
def n(sql, *a):
    return R.con.execute(sql, a).fetchone()[0]

print("全库块数:", n("SELECT count(*) FROM chunks"))
for term in ["营业总收入", "营业收入", "口径", "营业总成本"]:
    print(f"  含「{term}」的块: {n('SELECT count(*) FROM chunks WHERE text LIKE ?', f'%{term}%')}")
print("\n含「营业总收入」的块，按来源分：")
for r in R.con.execute("SELECT source, count(*) c FROM chunks WHERE text LIKE '%营业总收入%' GROUP BY source ORDER BY c DESC"):
    print(f"   {r['source']:<10} {r['c']}")
print("\n同时含「营业总收入」和「营业收入」的块（可能含口径说明）：",
      n("SELECT count(*) FROM chunks WHERE text LIKE '%营业总收入%' AND text LIKE '%营业收入%'"))
print("\n含「营业总收入」且含「差额 / 差 / 调节」的块：")
for r in R.con.execute("SELECT row,source,company,section,substr(text,1,150) s FROM chunks "
                       "WHERE text LIKE '%营业总收入%' AND (text LIKE '%差额%' OR text LIKE '%调节%') LIMIT 6"):
    print(f"   row={r['row']} {r['source']}/{r['company']} §{r['section']}")
    print("     ", r['s'].replace(chr(10), ' ')[:130])

# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
print("== 江波龙名下的「营业总收入」块 ==")
rows = list(R.con.execute("SELECT row,company,source,section,substr(text,1,220) s FROM chunks "
    "WHERE text LIKE '%营业总收入%' AND (company LIKE '%江波龙%' OR company LIKE '%longsys%') LIMIT 8"))
print("   条数:", len(rows))
for r in rows:
    print(f"   row={r['row']} {r['source']}/{r['company']} §{r['section']}")
    print("     ", r['s'].replace(chr(10),' | ')[:200])
print("\n== 任意三例「营业总收入+营业收入」同现块 ==")
for r in R.con.execute("SELECT row,company,source,substr(text,1,200) s FROM chunks "
    "WHERE text LIKE '%营业总收入%' AND text LIKE '%营业收入%' LIMIT 3"):
    print(f"   row={r['row']} {r['source']}/{r['company']}")
    print("     ", r['s'].replace(chr(10),' | ')[:180])
print("\n== 含「口径」的块里，与营业收入相关的 ==")
for r in R.con.execute("SELECT row,company,source,substr(text,1,180) s FROM chunks "
    "WHERE text LIKE '%口径%' AND text LIKE '%营业%' LIMIT 5"):
    print(f"   row={r['row']} {r['source']}/{r['company']}")
    print("     ", r['s'].replace(chr(10),' | ')[:160])

# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)

m = R._meta(46199)
print(f"=== row 46199 {m['source']} §{m['section']} p{m['page_start']} {m['date']} ===")
print(f"url={m['url']}")
print(m['text'][:800])

print("\n=== 生效日 / 公布日（DATES）===")
for r in R.con.execute("SELECT row,source,page_start,substr(text,1,60) s, text FROM chunks "
                       "WHERE text LIKE '%Effective date%' AND text LIKE '%December 2, 2024%' LIMIT 3"):
    print(f"  row={r['row']} {r['source']} p{r['page_start']}")
    t = r["text"]; i = t.find("Effective date")
    print("   ..." + t[max(0,i-80):i+240].replace(chr(10), " | ") + "...")

print("\n=== DRAM 定义（修订原文）===")
for r in R.con.execute("SELECT row,source,page_start,text FROM chunks "
                       "WHERE text LIKE '%DRAM%' AND (text LIKE '%dynamic random access memory%') "
                       "AND source IN ('fedreg','govinfo','ecfr') LIMIT 3"):
    t = r["text"]; i = t.find("DRAM")
    print(f"  row={r['row']} {r['source']} p{r['page_start']}: ...{t[max(0,i-120):i+300].replace(chr(10),' | ')}...")

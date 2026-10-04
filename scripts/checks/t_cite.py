# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)

def find(label, needle, srcs=None, limit=4):
    sql = "SELECT row,source,company,section,page_start,title,url,date,chars,text FROM chunks WHERE text LIKE ?"
    a = [f"%{needle}%"]
    if srcs:
        sql += " AND source IN (%s)" % ",".join("?" * len(srcs))
        a += list(srcs)
    sql += " ORDER BY chars LIMIT ?"
    a.append(limit)
    rows = list(R.con.execute(sql, a))
    print(f"\n### {label}  —— 命中 {len(rows)}（示例）")
    for r in rows:
        print(f"  row={r['row']} {r['source']}/{r['company']} §{r['section']} p{r['page_start']} {r['chars']}字")
        print(f"    date={r['date']}  title={str(r['title'])[:60]}")
    return rows

find("① 2 GB/s/mm² 门槛", "greater than 2 gigabytes per second per square millimeter")
find("② Technical Note 定义", "Memory bandwidth density")
find("③ BIS 承认覆盖全部在产 HBM", "exceed this threshold")
find("④ License Exception HBM 3.3", "3.3")
find("⑤ 合规日 12-31", "compliance date of December 31, 2024", srcs=["fedreg"])
find("⑥ DRAM 定义", "DRAM", srcs=["govinfo", "ecfr"])

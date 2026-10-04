# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
def c(sql, *a): return R.con.execute(sql, a).fetchone()[0]

print("== FR 引文 96790 ==")
print("  含 '96790' 的块:", c("SELECT count(*) FROM chunks WHERE text LIKE '%96790%'"))
for r in R.con.execute("SELECT row,source,page_start,text FROM chunks WHERE text LIKE '%89 FR 96790%' LIMIT 2"):
    t = r["text"]; i = t.find("89 FR 96790")
    print(f"    row={r['row']} {r['source']} p{r['page_start']}: ...{t[max(0,i-150):i+80].strip()}...")

print("\n== 「CCL 里 DRAM 零命中」复核 ==")
for src in ("govinfo", "ecfr"):
    n_all = c("SELECT count(*) FROM chunks WHERE source=?", src)
    n_dram = c("SELECT count(*) FROM chunks WHERE source=? AND text LIKE '%DRAM%'", src)
    n_ccl = c("SELECT count(*) FROM chunks WHERE source=? AND section LIKE '3A0%'", src)
    n_dram_ccl = c("SELECT count(*) FROM chunks WHERE source=? AND section LIKE '3A0%' AND text LIKE '%DRAM%'", src)
    print(f"   {src}: 总块 {n_all}, 含 DRAM {n_dram} ({n_dram/max(n_all,1):.2%})")
    print(f"        §3A0xx 块 {n_ccl}, 其中含 DRAM {n_dram_ccl}")

print("\n== 3A090 条目里 DRAM 出现情况 ==")
for r in R.con.execute("SELECT row,source,section,text FROM chunks WHERE section='3A090' LIMIT 6"):
    has = "DRAM" in r["text"]
    print(f"   row={r['row']} {r['source']} 含DRAM={has}")

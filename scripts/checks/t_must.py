# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
NL = chr(10)
NEEDLE = "greater than 2 gigabytes per second per square millimeter"
cur = R.con.execute(
  "SELECT row,source,section,page_start,chars,substr(text,1,90) AS snip FROM chunks "
  "WHERE text LIKE ? ORDER BY row", (f"%{NEEDLE}%",))
rows = cur.fetchall()
print(f"含判据原文的块：{len(rows)} 个")
for r in rows:
    print("  row=%-6s %-5s %-24s p%-4s %s字" % (r["row"], r["source"],
          str(r["section"])[:22], r["page_start"], r["chars"]))
    print("        " + repr(r["snip"].replace(NL, " ")))
print()
print("含 3A090 的块 :", R.con.execute("SELECT count(*) FROM chunks WHERE text LIKE '%3A090%'").fetchone()[0])
print("section LIKE '3A090%' :", R.con.execute("SELECT count(*) FROM chunks WHERE section LIKE '3A090%'").fetchone()[0])
for r in R.con.execute("SELECT row,section,source,chars FROM chunks WHERE section LIKE '3A090%' ORDER BY row LIMIT 12"):
    print("   row=%-6s %-16s %-6s %s字" % (r["row"], r["section"], r["source"], r["chars"]))

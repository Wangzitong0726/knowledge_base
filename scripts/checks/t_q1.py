# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever
R = Retriever(verbose=False)
NEEDLE = "greater than 2 gigabytes per second per square millimeter"
mus = {r[0] for r in R.con.execute("SELECT row FROM chunks WHERE text LIKE ?", (f"%{NEEDLE}%",))}
print(f"判据块全集（含 must 原文）：{len(mus)} 个 -> {sorted(mus)}")
print()
Q = "3A090.c 的管制门槛是什么？"
for expand in (False, True):
    res = R.search(Q, k=8, dedup=True, expand=expand)
    rows = [r["row"] for r in res]
    hits = [r for r in rows if r in mus]
    print(f"===== expand={expand} =====")
    print(f"  前8的 row：{rows}")
    print(f"  其中含 must 原文的：{hits}  ->  {'命中 ✅' if hits else '未命中 ❌'}")
    for i, r in enumerate(res, 1):
        tag = "  ★判据块" if r["row"] in mus else ""
        print(f"   {i}. [%-9s] sim=%-7s %s p%s%s" % (r["channels"], r["dense_sim"],
              str(r["section"])[:20] or r["file"], r["page_start"], tag))
    print()

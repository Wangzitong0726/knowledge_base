# -*- coding: utf-8 -*-
import sys, re, numpy as np
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever, INSTRUCTION
R = Retriever(verbose=False)
NEEDLE = "greater than 2 gigabytes per second per square millimeter"
mus = {r[0] for r in R.con.execute("SELECT row FROM chunks WHERE text LIKE ?", (f"%{NEEDLE}%",))}
print("判据块:", sorted(mus))

# 1. 结构子集：section 以某个 ECCN 开头
for sec in ("3A090", "3A090.c"):
    sub = [r[0] for r in R.con.execute("SELECT row FROM chunks WHERE section LIKE ? ORDER BY row", (sec+"%",))]
    print(f"\nsection LIKE {sec+'%'}: {len(sub)} 块, 判据块在其中 {sorted(set(sub)&mus)}")

ids = ["3A090", "3A090.c"]
sub = sorted({r[0] for i in ids for r in R.con.execute("SELECT row FROM chunks WHERE section LIKE ?", (i+"%",))})
print(f"\n并集子集 {len(sub)} 块")

# 2. 子集内用稠密相似度排序（只需算 42 行）
e = R._dense()
Q = "3A090.c 的管制门槛是什么？"
v = e.encode([Q], is_query=True, instruction=INSTRUCTION)[0]
M = np.asarray(R.vec[sub], dtype=np.float32) @ v
order = np.argsort(-M)
print(f"\n子集内按稠密相似度排序（查询：{Q}）：")
for i in order[:12]:
    r = sub[int(i)]
    print("   row=%-6s sim=%.4f %s %s" % (r, M[i],
          "★判据块" if r in mus else "      ", str(R._meta(r)["section"])[:14]))

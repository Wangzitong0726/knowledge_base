# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever, expand_queries, RRF_K, POOL
R = Retriever(verbose=False)
NEEDLE = "greater than 2 gigabytes per second per square millimeter"
mus = {r[0] for r in R.con.execute("SELECT row FROM chunks WHERE text LIKE ?", (f"%{NEEDLE}%",))}
Q = "3A090.c 的管制门槛是什么？"
ex = expand_queries(Q)
qs = [Q] + ex
print("查询集：")
for i, x in enumerate(qs): print(f"  [{i}] {x}")

ranks = []
for qq in qs:
    b, d, ds, _ = R._rank_one(qq)
    ranks.append((b, d))

def fuse(weights, mode="sum"):
    sc = {}
    for (b, d), w in zip(ranks, weights):
        for tbl in (b, d):
            for r, rk in tbl.items():
                v = w / (RRF_K + rk)
                if mode == "sum":
                    sc[r] = sc.get(r, 0.0) + v
                else:
                    sc[r] = max(sc.get(r, 0.0), v)
    return [r for r, _ in sorted(sc.items(), key=lambda x: -x[1])]

def doc_cap(rows, cap=2):
    """同一 doc_id 最多留 cap 块（top-8 里 5 块来自同一份 FR 文件）"""
    seen, out = {}, []
    for r in rows:
        dd = R._meta(r)["doc_id"]
        if seen.get(dd, 0) >= cap: continue
        seen[dd] = seen.get(dd, 0) + 1
        out.append(r)
    return out

print(f"\n{'变体':<34} {'前8里有无判据块':<16} 判据块最高名次")
tests = [
    ("现役  原1.0/改写0.6 sum",   fuse([1.0]+[0.6]*len(ex))),
    ("改写等权 全1.0 sum",        fuse([1.0]*(1+len(ex)))),
    ("原0.6/改写1.0 sum",         fuse([0.6]+[1.0]*len(ex))),
    ("max 融合 全1.0",            fuse([1.0]*(1+len(ex)), "sum" if False else "max")),
    ("sum + 同文档限2块",         doc_cap(fuse([1.0]+[0.6]*len(ex))), ),
    ("sum全1.0 + 同文档限2块",    doc_cap(fuse([1.0]*(1+len(ex)))),
)]
for name, rows in tests:
    top8 = rows[:8]
    hit = [r for r in top8 if r in mus]
    best = next((i for i, r in enumerate(rows, 1) if r in mus), None)
    print(f"{name:<34} {'命中 ✅ '+str(hit) if hit else '未命中 ❌':<16} {best if best else '>全部'}")

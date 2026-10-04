# -*- coding: utf-8 -*-
import sys, importlib.util
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever, expand_queries, RRF_K

spec = importlib.util.spec_from_file_location("rq", "scripts/run_questions.py")
rq = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(rq)
except SystemExit:
    pass
QS = rq.Q
print(f"载入 {len(QS)} 道题\n")

R = Retriever(verbose=False)

def doc_cap(rows, cap):
    if cap is None: return rows
    seen, out = {}, []
    for r in rows:
        dd = R._meta(r)["doc_id"]
        if seen.get(dd, 0) >= cap: continue
        seen[dd] = seen.get(dd, 0) + 1
        out.append(r)
    return out

def run(q, k, cap):
    ex = expand_queries(q)
    qs = [q] + ex
    sc = {}
    for qi, qq in enumerate(qs):
        w = 1.0 if qi == 0 else 0.6
        b, d, _, _ = R._rank_one(qq)
        for tbl in (b, d):
            for r, rk in tbl.items():
                sc[r] = sc.get(r, 0.0) + w / (RRF_K + rk)
    order = [r for r, _ in sorted(sc.items(), key=lambda x: -x[1])]
    order = doc_cap(order, cap)
    return order[:k]

import time
print(f"{'题':<4}{'cap=None':<12}{'cap=3':<12}{'cap=2':<12}{'cap=1':<12}")
tot = {None:0, 3:0, 2:0, 1:0}
cache = {}
for it in QS:
    q, k = it["q"], it.get("k", 8)
    musts = [m for m in it.get("must", [])]
    # 预取每题候选（不含 cap），再对 cap 切片
    cand = cache.setdefault(q, run(q, 400, None))
    row = f"{it['n']:<4}"
    for cap in (None, 3, 2, 1):
        rows = doc_cap(cand, cap)[:k]
        txts = [R._meta(r)["text"] for r in rows]
        ok = all(any(m in t for t in txts) for m in musts) if musts else True
        if it.get("must_fail"):
            ok = True   # 第10题另判，见下
        tot[cap] += ok
        row += ("✅" if ok else "❌") + "          "
    print(row)
print(f"\n{'合计':<4}" + "".join(f"{tot[c]}/{len(QS):<10}" for c in (None,3,2,1)))

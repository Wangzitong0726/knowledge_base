# -*- coding: utf-8 -*-
import sys, importlib.util
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from retrieve import Retriever, expand_queries, RRF_K
spec = importlib.util.spec_from_file_location("rq", "scripts/run_questions.py")
rq = importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(rq)
except SystemExit: pass
R = Retriever(verbose=False)
LIB = rq.LIB_SOURCES

def fused(q, k_max=400):
    ex = expand_queries(q); qs = [q] + ex
    sc = {}
    for qi, qq in enumerate(qs):
        w = 1.0 if qi == 0 else 0.6
        b, d, _, _ = R._rank_one(qq)
        for tbl in (b, d):
            for r, rk in tbl.items():
                sc[r] = sc.get(r, 0.0) + w / (RRF_K + rk)
    return [r for r, _ in sorted(sc.items(), key=lambda x: -x[1])][:k_max]

def apply(order, cap_lib, cap_src, cap_doc):
    cnt_l, cnt_s, cnt_d, kept = {}, {}, {}, []
    for r in order:
        m = R._meta(r); src = m["source"]; doc = m["doc_id"]
        lib = "A" if src in LIB["A"] else ("B" if src in LIB["B"] else "-")
        if cap_lib and cnt_l.get(lib, 0) >= cap_lib: continue
        if cap_src and cnt_s.get(src, 0) >= cap_src: continue
        if cap_doc and cnt_d.get(doc, 0) >= cap_doc: continue
        cnt_l[lib] = cnt_l.get(lib, 0) + 1
        cnt_s[cnt_s.get(src, 0)] = 0
        cnt_s[src] = cnt_s.get(src, 0) + 1
        cnt_d[doc] = cnt_d.get(doc, 0) + 1
        kept.append(r)
    return kept

CANDS = {it["n"]: fused(it["q"]) for it in rq.Q}
VARIANTS = [("仅限文档3(现役)", None, None, 3),
            ("+每来源≤5", None, 5, 3),
            ("+每来源≤4", None, 4, 3),
            ("+每库≤6", 6, None, 3),
            ("+每库≤5", 5, None, 3)]
print(f"{'变体':<16}" + "".join(f"Q{it['n']:<4}" for it in rq.Q) + " 通过")
for name, cl, cs, cd in VARIANTS:
    out, npass = [], 0
    for it in rq.Q:
        rows = apply(CANDS[it["n"]], cl, cs, cd)
        rows = [r for r in rows if r in rows][:0] or rows   # 保序
        sel = rows[:it.get("k", 8)]
        hits = [R._meta(r) for r in sel]
        ok, _v = rq.judge(it, hits, "材料未覆盖")
        npass += ok
        out.append(" ✅   " if ok else " ❌   ")
    print(f"{name:<16}" + "".join(out) + f" {npass}/10")

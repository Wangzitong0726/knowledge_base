# -*- coding: utf-8 -*-
import sys, numpy as np
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import llm
from retrieve import expand_queries, Retriever, _MARK

print("== 1. 行首编号剥离（回归测试）==")
for line in ["3A090.c 管制门槛 出口管制 ECCN 参数阈值",
             "1. 3A090.c control threshold EAR CCL",
             "2、HBM memory bandwidth density",
             "- 内存带宽密度 阈值",
             "3A090 内存带宽密度"]:
    print(f"   {line!r}\n     -> {_MARK.sub('', line).strip()!r}")

print("\n== 2. 改写查询 ==")
env, src = llm.load_env()
q = "3A090.c 的管制门槛是多少？"
ex = expand_queries(q, env)
print(f"   原问题：{q}")
for i, e in enumerate(ex):
    print(f"   改写{i+1}：{e}")
if not ex:
    print("   ⚠️ 改写仍为空（说明 60s 超时是主因）")

print("\n== 3. 目标块 row=38830（CCL 3A090 定义，含 memory bandwidth density）==")
R = Retriever(verbose=False)
TARGET = 38830
m = R._meta(TARGET)
print(f"   {m['source']} · {m['section']} · p{m['page_start']} · {m['chars']}字")

queries = [q] + ex
print(f"\n   {'查询':<52} {'BM25名次':>8} {'稠密名次':>8} {'相似度':>8}")
for qq in queries:
    b_r, d_r, d_s, _ = R._rank_one(qq)
    br = b_r.get(TARGET); dr = d_r.get(TARGET)
    print(f"   {qq[:50]:<52} {br if br is not None else '>99':>8} "
          f"{dr if dr is not None else '>99':>8} "
          f"{round(d_s.get(TARGET,0),4) if TARGET in d_s else '-':>8}")

print("\n== 4. 融合后名次（原问题权重1.0，改写0.6）==")
res = R.search(q, k=200, dedup=False, expand=True)
pos = next((i for i, r in enumerate(res, 1) if r["row"] == TARGET), None)
print(f"   row 38830 融合名次：{pos if pos else '200 名之外'}")
print(f"   前 8 里有没有它：{'有 ✅' if pos and pos <= 8 else '没有 ❌'}")
print("\n   前 8 名：")
for i, r in enumerate(res[:8], 1):
    mark = " ★" if r["row"] == TARGET else ""
    print(f"   {i}. [{r['channels']:9s}] bm25={r['bm25_rank']} dense={r['dense_rank']} "
          f"sim={r['dense_sim']} {r['section'] or r['file']}{mark}")

# -*- coding: utf-8 -*-
import sys, urllib.request, urllib.parse, time
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

def get(q, timeout=180):
    u = "http://127.0.0.1:8848/?" + urllib.parse.urlencode({"q": q})
    t0 = time.time()
    with urllib.request.urlopen(u, timeout=timeout) as r:
        return r.read().decode("utf-8"), time.time() - t0

# 1) 首页
h, dt = get("")
print(f"首页 {len(h)} 字节 {dt:.1f}s")
print("   含检索说明:", "BM25" in h)
print("   含输入框  :", 'name=q' in h)

# 2) 真实提问
h, dt = get("3A090.c 的管制门槛是什么？")
print(f"\n提问 {len(h)} 字节 {dt:.1f}s")
checks = [
    ("模型作答徽章", "模型作答" in h),
    ("语料原文徽章", "语料原文" in h),
    ("含判据原文  ", "greater than 2 gigabytes per second per square millimeter" in h),
    ("有 [n] 锚点 ", 'href="#hit1"' in h),
    ("无 None 泄漏", ">None<" not in h and "#None" not in h),
    ("无作答失败  ", "作答失败" not in h),
]
for n, ok in checks:
    print(f"   {'✅' if ok else '❌'} {n}")
open("outputs/_qa_home.html", "w", encoding="utf-8").write(h)
print("   存 outputs/_qa_home.html 供截图")

# -*- coding: utf-8 -*-
import sys, urllib.request, urllib.parse, time, threading
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

def get(q, timeout=240):
    u = "http://127.0.0.1:8848/?" + urllib.parse.urlencode({"q": q})
    t0 = time.time()
    with urllib.request.urlopen(u, timeout=timeout) as r:
        return r.read().decode("utf-8"), time.time() - t0

print("== 第10题（必败题）在页面上的表现 ==")
h, dt = get("HBM3E 现在的合约价是多少美元？")
print(f"   {len(h)} 字节 {dt:.1f}s")
print(f"   {'✅' if 'class=\"miss\"' in h else '❌'} 「材料未覆盖」标红")
import re
ans = re.search(r'class=answer>(.*?)</div>', h, re.S)
if ans:
    txt = re.sub(r"<[^>]+>", "", ans.group(1)).strip()
    print("   作答开头:", txt[:120].replace("\n", " "))

print("\n== A 股语料提问（换一类文档）==")
h2, dt2 = get("江波龙的年报里，营业收入和营业总收入的口径差在哪里？")
print(f"   {len(h2)} 字节 {dt2:.1f}s")
print(f"   {'✅' if '作答失败' not in h2 else '❌'} 未报错")
print(f"   {'✅' if '江波龙' in h2 else '❌'} 出处含江波龙")

print("\n== 并发两问（验线程局部连接）==")
res, errs = {}, []
def worker(i, q):
    try:
        hh, dd = get(q)
        res[i] = (len(hh), dd, "作答失败" not in hh)
    except Exception as e:
        errs.append(f"{i}: {type(e).__name__} {e}")
ts = [threading.Thread(target=worker, args=(i, q)) for i, q in
      enumerate(["3A090.c 的管制门槛是什么？", "美光的 HBM 资本开支怎么说？"])]
t0 = time.time()
[t.start() for t in ts]; [t.join() for t in ts]
print(f"   两个请求总耗时 {time.time()-t0:.1f}s")
for i in sorted(res): print(f"   请求{i}: {res[i][0]} 字节 {res[i][1]:.1f}s 无错={res[i][2]}")
print("   异常:", errs or "无 ✅")

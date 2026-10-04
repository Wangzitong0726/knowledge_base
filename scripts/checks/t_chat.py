# -*- coding: utf-8 -*-
import sys, time
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import llm
from retrieve import EXPAND_SYSTEM
env, src = llm.load_env()
q = "3A090.c 的管制门槛是多少？"
for i in range(4):
    t0 = time.time()
    txt, err = llm.chat(EXPAND_SYSTEM, q, env, max_tokens=300, temperature=0, timeout=60)
    dt = time.time() - t0
    print(f"[{i+1}] {dt:5.1f}s  错误={err}")
    print(f"     返回长度={len(txt) if txt else 0}  {repr((txt or '')[:80])}")
    time.sleep(1)

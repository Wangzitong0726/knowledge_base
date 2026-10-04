# -*- coding: utf-8 -*-
import sys, json, urllib.request
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import llm
from retrieve import EXPAND_SYSTEM
env, _ = llm.load_env()
base = (env.get("ANTHROPIC_BASE_URL") or "").rstrip("/")
tok = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY")
body = json.dumps({"model": env.get("ANTHROPIC_MODEL"), "max_tokens": 300,
    "temperature": 0, "system": EXPAND_SYSTEM,
    "messages": [{"role": "user", "content": "3A090.c 的管制门槛是多少？"}]}).encode()
req = urllib.request.Request(base + "/v1/messages", data=body,
    headers={"content-type": "application/json", "x-api-key": tok,
             "anthropic-version": "2023-06-01"})
for i in range(3):
    with urllib.request.urlopen(req, timeout=60) as r:
        js = json.loads(r.read().decode())
    print(f"--- 第{i+1}次 ---")
    print("  顶层键 :", sorted(js.keys()))
    print("  stop   :", js.get("stop_reason"), "| usage:", js.get("usage"))
    c = js.get("content")
    print("  content 类型:", type(c).__name__, "长度:", len(c) if isinstance(c, list) else "-")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict):
                t = b.get("text") or b.get("thinking") or ""
                print(f"    block type={b.get('type')!r} text长={len(t)} 预览={t[:70]!r}")
            else:
                print("    block 非 dict:", repr(b)[:120])

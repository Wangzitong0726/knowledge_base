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

def call(extra, tag):
    payload = {"model": env.get("ANTHROPIC_MODEL"), "max_tokens": 1200,
               "temperature": 0, "system": EXPAND_SYSTEM,
               "messages": [{"role": "user", "content": "3A090.c 的管制门槛是多少？"}]}
    payload.update(extra)
    req = urllib.request.Request(base + "/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json", "x-api-key": tok,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            js = json.loads(r.read().decode())
    except Exception as e:
        d = ""
        if hasattr(e, "read"):
            try: d = e.read().decode()[:200]
            except Exception: pass
        print(f"  {tag}: 失败 {type(e).__name__} {d}")
        return
    bs = js.get("content") or []
    think = sum(len(b.get("thinking") or "") for b in bs if b.get("type") == "thinking")
    text = "".join(b.get("text","") for b in bs if b.get("type")=="text")
    print(f"  {tag}: stop={js.get('stop_reason')} out={js['usage'].get('output_tokens')} "
          f"思考{think}字 正文{len(text)}字")
    if text: print(f"      {text[:100]!r}")

print("基线（不传 thinking 参数）:")
call({}, "baseline")
print("thinking 关闭:")
call({"thinking": {"type": "disabled"}}, "disabled")

# -*- coding: utf-8 -*-
"""
模型调用层。抽出来是因为**两个地方都要用**：页面作答、以及查询改写。
早先把 `load_env` 写在 `serve_qa.py` 里，`retrieve.py` 想用就形成
`serve_qa → retrieve → serve_qa` 的循环 import。**循环 import 的根因通常不是
import 写错了，而是职责放错了地方**——环境与网络是基础设施，不该躲在页面脚本里。
"""
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KEYS = ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL", "DEEPSEEK_API_KEY")


def load_env():
    """配置来源：**进程环境优先，.env 文件补缺**。返回 (env, 来源描述)。

    ⚠️ 顺序不能反，这是实测踩出来的：`ai_homework2/.env` 里存的那个
    `ANTHROPIC_AUTH_TOKEN` **不是 ASCII 的**（19 字符、第 3–8 位非 ASCII），
    塞进 HTTP 头会直接抛 `UnicodeEncodeError: 'latin-1' codec can't encode...`
    —— 报错长得像网络问题，其实是 key 本身用不了。
    进程环境里那个是真的（`sk-` + 32 位全 ASCII）。
    所以**环境变量必须压过文件**，否则一个坏文件会把能用的 key 顶掉。

    只读键值、只报长度与是否 ASCII，**从不回显值本身**。
    """
    env = {k: os.environ[k] for k in KEYS if os.environ.get(k)}
    src = "进程环境"
    for p in (ROOT / ".env", ROOT.parent / "ai_homework2" / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k in KEYS and k not in env:      # 环境已有的不覆盖
                env[k] = v
                src += f" + {p.name}"
        break
    return env, src


# ⚠️ 这个数**包含模型的思考链**，不是「答案能写多长」。
# 实测（deepseek-v4-flash-vision-exp）：它先吐一个 `thinking` 块再写正文，
# max_tokens 是从思考开始计的。给 300 时，思考经常自己就吃掉 300，
# 于是 **stop_reason=max_tokens、响应里只有 thinking 块、一个 text 块都没有**。
# 而旧解析 `"".join(b.get("text","") ...)` 对这种响应返回 `""`，
# **还报 错误=None**——等于把「被截断」谎报成「成功但没话说」。
# 表现出来就是：查询改写偶发空表、问答偶发空白，且**全都静默**。
DEFAULT_MAX_TOKENS = 4000


def chat(system, user, env=None, max_tokens=DEFAULT_MAX_TOKENS, temperature=0,
         timeout=180, think=True):
    """发一轮对话。返回 (文本, 错误)。错误不抛，交给调用方决定怎么显示。

    只取 `type=="text"` 的块，**思考块不计入回答**。
    「没有 text 块」一律算失败并说明原因，绝不返回 ("", None)。

    `think=False` 会带上 `{"thinking":{"type":"disabled"}}`（实测该接口认这个参数）。
    用在哪、不用在哪，是分开判断过的：
      · **查询改写** —— think=False。它只是措辞转换，实测关掉后 633 token → 40 token，
        思考 2109 字 → 0 字，输出照样可用。开着纯属浪费，还平添被截断的风险。
      · **作答** —— think=True（默认）。这里的思考是**承重**的：本页面唯一的设计纪律
        是「只依据材料、不许补事实数字」，推理链正是在压这件事。为省钱关掉它，
        等于拿交付物的诚实性换 token。
    """
    env = env or load_env()[0]
    base = (env.get("ANTHROPIC_BASE_URL") or "").rstrip("/")
    tok = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY")
    model = env.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    if not (base and tok):
        return None, "未配置 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN"

    payload = {
        "model": model, "max_tokens": max_tokens, "temperature": temperature,
        "system": system, "messages": [{"role": "user", "content": user}],
    }
    if not think:
        payload["thinking"] = {"type": "disabled"}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        base + "/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": tok,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            js = json.loads(r.read().decode())
        blocks = [b for b in (js.get("content") or []) if isinstance(b, dict)]
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        if not text:
            n_think = sum(len(b.get("thinking") or "") for b in blocks)
            stop = js.get("stop_reason")
            if stop == "max_tokens":
                return None, (f"思考链吃光了 max_tokens，没留下正文"
                              f"（max_tokens={max_tokens}，思考 {n_think} 字）——调大 max_tokens")
            return None, f"响应无 text 块（stop_reason={stop}，思考 {n_think} 字）"
        return text, None
    except Exception as e:
        detail = ""
        if hasattr(e, "read"):
            try:
                detail = e.read().decode()[:300]
            except Exception:
                pass
        return None, f"{type(e).__name__}: {e} {detail}"

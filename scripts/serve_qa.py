# -*- coding: utf-8 -*-
"""
阶段 4 · 带出处的问答页面（本机 http.server，只用标准库）

一条设计纪律，出自作业二精读页的同一处教训：
**模型说的话和材料原文，视觉上必须一眼分得开。**
精读页当时要防的是「把作者的主张读成事实」；这里要防的是
**「把模型的话读成原文」**——模型会顺手把两个块的说法缝成一句通顺的话，
缝出来的那句在语料里**不存在**。所以：
  · 作答区白底黑字、标「模型作答」徽章
  · 原文区灰底、标「语料原文」徽章、逐字引用不再加工
  · 每个论断强制带 [n]，n 指到下面第 n 条原文
  · 材料没覆盖时，回答必须是「材料未覆盖」而不是给个像样的数（第 10 题就考这个）

免费的标准库 http.server 不用 flask——本机没装 flask，也不该为一个页面装。
"""
import html
import json
import os
import re
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

PORT = int(os.environ.get("QA_PORT", "8848"))

SYSTEM = """你是内存（DRAM/HBM）产业与美国出口管制领域的研究助手。

规则，按优先级：
1. **只依据下面给出的材料回答**，不得使用你自己的记忆补充任何事实、数字或日期。
2. 每个论断后面用 [n] 标注它来自第几条材料。没有材料支撑的话不要写。
3. 如果材料不足以回答，**直接说「材料未覆盖」并说明缺什么**。
   不要给出一个"看起来合理"的数字，也不要拿相近的数字顶替。
   这一条比"答得像样"重要得多。
4. 引数字、型号、阈值时必须逐字照抄材料原文，不得改写成同义表述
   （`3A090.c` 不能写成「3A090 条款」，`2 GB/s/mm²` 不能写成「2GB/s/mm2」）。
5. 材料是中英文混杂的，中英之间可以正常串联，但引原文的部分保持原语言。
6. 回答用中文，简洁，不要复述规则。"""

ANSWER_CSS = """
:root{--ink:#1a1a1a;--ink2:#4a4a4a;--ink3:#8a8a8a;--line:#e3e3e3;
--bg:#fff;--bg2:#f7f7f5;--accent:#1f6f4a;--accent2:#0f4c75;--warn:#b45309}
*{box-sizing:border-box}
body{margin:0;background:var(--bg2);color:var(--ink);
font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--ink3);font-size:13px;margin-bottom:22px}
form{display:flex;gap:8px;margin-bottom:22px}
input[type=text]{flex:1;padding:12px 14px;border:1px solid var(--line);
border-radius:8px;font-size:15px;font-family:inherit}
input[type=text]:focus{outline:2px solid var(--accent2);outline-offset:-1px;border-color:transparent}
button{padding:12px 22px;border:0;border-radius:8px;background:var(--accent);
color:#fff;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit}
button:disabled{background:var(--ink3);cursor:wait}
.card{background:var(--bg);border:1px solid var(--line);border-radius:10px;
padding:18px 20px;margin-bottom:16px}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.06em;
padding:2px 8px;border-radius:4px;margin-bottom:10px}
.b-model{background:#eaf4ee;color:var(--accent)}
.b-src{background:#eef1f6;color:var(--accent2)}
.bdiag{background:var(--bg2);color:var(--ink3)}
.answer{white-space:pre-wrap}
.answer .cite{color:var(--accent2);font-weight:700;font-size:12px;
vertical-align:super;text-decoration:none}
.answer .miss{color:var(--warn);font-weight:700}
.hit{border-left:3px solid var(--line);padding-left:14px;margin:14px 0 0}
.hit .no{color:var(--accent2);font-weight:700}
.hit .prov{font-size:12px;color:var(--ink3);margin:2px 0 8px;line-height:1.6}
.hit .txt{background:var(--bg3,#fbfbf9);border:1px solid var(--line);
border-radius:6px;padding:10px 12px;font-size:13.5px;white-space:pre-wrap;
max-height:260px;overflow:auto;color:var(--ink2)}
.hit .diag{font-size:11px;color:var(--ink3);margin-top:6px;font-family:ui-monospace,Consolas,monospace}
.hit a{color:var(--accent2);word-break:break-all}
.err{background:#fdf2f2;border-color:#f5c2c2;color:#9b2226}
.muted{color:var(--ink3);font-size:13px}
"""


from llm import chat, load_env  # noqa: E402


def call_model(env, question, hits):
    """把检索到的材料喂给模型。返回 (作答文本, 错误)。"""
    parts = []
    for i, m in enumerate(hits, 1):
        prov = f"{m['company'] or m['source']} / {m['title'] or m['file']} / {m['section']} / p{m['page_start']}"
        parts.append(f"【材料 {i}】{prov}\n{m['text']}")
    user = "材料：\n\n" + "\n\n---\n\n".join(parts) + f"\n\n=====\n问题：{question}"
    return chat(SYSTEM, user, env)


def _ng(v, fmt=""):
    """None 的语义是「这条通道没给它投票」，不是「空」——印成 `—`，别把 None 甩给读者。

    实测会出现一整块 `bm25#None dense#None sim=None`：那是一块**只被改写查询捞上来**的
    条文本。这本身是有信息量的（说明原问题的措辞够不着它），所以留 `—` 而不是抹掉整段。
    """
    if v is None:
        return "—"
    return (fmt % v) if fmt else str(v)


def render_answer(text):
    """把 [n] 转成上标锚点；把「材料未覆盖」标红（第 10 题要能一眼看到它没编）。"""
    t = html.escape(text or "")
    t = re.sub(r"\[(\d+)\]", r'<a class="cite" href="#hit\1">[\1]</a>', t)
    t = t.replace("材料未覆盖", '<span class="miss">材料未覆盖</span>')
    return t


def page(q="", hits=None, answer=None, err=None, note=""):
    hits = hits or []
    h = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>内存产业知识库 · 带出处问答</title>',
         f"<style>{ANSWER_CSS}</style><div class=wrap>",
         "<h1>内存产业知识库 · 带出处问答</h1>",
         # ⚠️ 「136」= 巨潮 92 + 深交所 44，而深交所那 44 份与巨潮**字节相同**
         # （见 crosscheck_sources.py：44 对 sha256 100% 相同）。136 是记录数，
         # 去重后 A 股唯一文档是 92。旧版直接写 136，等于把重复当成了两批材料。
         '<div class=sub>语料：A 股内存产业链年报/半年报 136 份（含 44 份交易所同源副本，去重 92）· '
         'SEC 10-K · 三星/SK 海力士 IR · BIS 规则与 CFR 条文 · 共 81,895 块 ｜ '
         '检索：BM25 + 向量（RRF 融合）</div>',
         '<form method=get><input type=text name=q autofocus '
         f'placeholder="例如：3A090.c 的管制门槛是多少？" value="{html.escape(q)}">'
         "<button>提问</button></form>"]

    if err:
        h.append(f'<div class="card err"><b>作答失败</b><div class=muted>{html.escape(err)}</div></div>')
    if answer is not None:
        h.append('<div class=card><span class="badge b-model">模型作答 · 非原文</span>'
                 f'<div class=answer>{render_answer(answer)}</div></div>')
    if hits:
        h.append(f'<div class=card><span class="badge b-src">语料原文 · 逐字引用</span>'
                 f'<div class=muted>检索到 {len(hits)} 条，按 RRF 融合分排序</div>')
        for i, m in enumerate(hits, 1):
            prov = f"{m['company'] or m['source']} · {m['title'] or m['file']}"
            if m["section"]:
                prov += f" · {m['section']}"
            prov += f" · p{m['page_start']}"
            if m["page_end"] != m["page_start"]:
                prov = prov.replace(f"p{m['page_start']}", f"p{m['page_start']}–{m['page_end']}")
            if m["date"]:
                prov += f" · {m['date']}"
            url = f'<br><a href="{html.escape(m["url"] or "#")}" target=_blank>{html.escape(m["url"] or "")}</a>' if m["url"] else ""
            diag = (f"rrf={m['score']:.4f} · 通道 {m['channels'] or '-'}"
                    f" · bm25#{_ng(m['bm25_rank'])} · dense#{_ng(m['dense_rank'])}"
                    f" sim={_ng(m['dense_sim'], '%.4f')}")
            h.append(f'<div class=hit id=hit{i}><span class=no>[{i}]</span> '
                     f'{html.escape(prov)}<div class=prov>{url}</div>'
                     f'<div class=txt>{html.escape(m["text"])}</div>'
                     f'<div class=diag>{html.escape(diag)}</div></div>')
        h.append("</div>")
    if not q:
        h.append('<div class="card muted">输入一个问题开始。'
                 '答案只依据下面列出的语料原文，每条论断都可点 [n] 回到原文核对。</div>')
    h.append(f'<div class="muted" style="margin-top:20px">{html.escape(note)}</div>')
    h.append("</div></html>")
    return "".join(h)


_R = None


def get_retriever():
    global _R
    if _R is None:
        from retrieve import Retriever
        _R = Retriever()
    return _R


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        if u.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        qs = parse_qs(u.query)
        q = (qs.get("q") or [""])[0].strip()
        # 可选取几席。默认 8；`save_qa_snapshots.py` 会按十题记录里各题实际用的
        # k（8/10/14）来要，好让**截图与记录显示的席数一致**——原先页面写死 8，
        # 于是 Q7 那张图显示 8 席、记录里却是 14 席，同一个问题两个数。
        # 上界 50：k 直接决定要读多少块并塞进模型上下文，不设限就是一个
        # 「一个参数把服务打满」的口子。
        try:
            k = int((qs.get("k") or ["8"])[0])
        except ValueError:
            k = 8
        k = max(1, min(k, 50))
        hits, answer, err = [], None, None
        note = ""
        if q:
            try:
                R = get_retriever()
                hits = R.search(q, k=k, expand=True)
                if not hits:
                    note = "检索无命中：整个语料没有块能对上这个问题。"
                env, p = load_env()
                answer, err = call_model(env, q, hits)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
        body = page(q, hits, answer, err, note).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    env, p = load_env()
    print(f"语料 .env：{p if p else '未找到'}  模型={env.get('ANTHROPIC_MODEL','(未设)')}")
    get_retriever()
    print(f"起服务 http://127.0.0.1:{PORT}/   （Ctrl-C 停）")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

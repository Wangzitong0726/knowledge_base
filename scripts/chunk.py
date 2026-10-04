# -*- coding: utf-8 -*-
"""
阶段 3 · 切块（课程 p25 参数：800 字 / 重合 120 字 / 句末收尾；带 公司·章节·页码·块序号）

    python scripts/chunk.py --limit 6      # 试切几份，看分布与抽样
    python scripts/chunk.py                # 全库
    python scripts/chunk.py --no-overlap   # 关掉重合（做对照用）

四条硬约束（都是为了让**数字不脱离它的标签**，与阶段 2 的抽表原则一脉相承）：

1. **表格行是原子单位，绝不从中间切**。阶段 2 已把表拍平成 `表头 值 | 表头 值` 的行，
   一行就是一组「标签+数值」。若按 800 字机械切，切点落在行中间，
   保留的那半行就成了没有标签的裸数字——**检索得到数字、却不知道它是什么的**。
   所以：含 ` | ` 的行整行作为不可分单元。

2. **句末收尾**。中文断在 `。！？；`，西文断在 `. ` 前（但 **`3.3` 这种小数不切**，
   `.` 后紧跟数字时不是句号）。

3. **章节变了就断开，且不在章节间做重合**。重合是为了「跨块的一句话不被漏掉」，
   而跨章节的重合只会把上一节的尾巴粘到下一节头上，制造假的上下文。
   反过来，章节本身是最有检索价值的标签之一（`3A090`、`第三节 管理层讨论与分析`），
   所以**超长章节内的每一块都带着同一个章节名**——这正是库B 要的效果：
   CCL 里 3A090 那一节 1.3 万字，切成十几块，**每块都还认得自己是 3A090**。

4. **一份文档内才切**，不跨文档；`page` 记起止页，引用时能指回去。
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

EXTRACTED = ROOT / "data" / "extracted"
OUT = ROOT / "knowledge_base" / "chunks.jsonl"
REPORT = ROOT / "data" / "stage3_切块报告.md"

LIMIT_CHARS = 800
OVERLAP_CHARS = 120
MIN_CHUNK = 40                     # 短于此且不是整节，尽量并进相邻块

# 句末：中文标点后必断；西文 `.`/`!`/`?` **后面跟空白**才断。
# 关键在 (?=\s)：`3.3`、`§ 774.1`、`15 CFR` 里的点后面不跟空白，不会被切开。
SENT_SPLIT = re.compile(r"(?<=[。！？；])|(?<=[.!?])(?=\s)")

# 章节标题：命中即更新「当前章节」。要求**行首**、**行足够短**，
# 否则正文里一句「见第三节所述」也会被当成标题（假章节比没有章节更误导）。
#
# ⚠️ **必须分两级**，这是踩过的坑：
#   第一版把所有标题一视同仁，命中即**切断**当前块。可中文年报里 `一、` `二、`
#   这种小标题每隔几段就有一个，于是每块只能装到下一个 `一、` 为止——
#   实测 6 份年报切出 4,964 块，**中位块长只有 139 字**（应为 800），
#   还有 981 块不足 40 字。块太碎等于把上下文切没了，检索到也拼不出意思。
# 现在：**一级标题（节/章/ECCN/§/Item/PART/Supplement）才切断**，
#   二级标题（`一、`）只更新标签、不切断。
LEVEL1 = [
    re.compile(r"^(第[一二三四五六七八九十百]+[节章])\s*[　 ]*([^\n]{0,40})"),
    re.compile(r"^(Supplement No\.\s*\d+ to Part \d+)([^\n]{0,60})"),
    re.compile(r"^(§+\s*[\d.]+[a-z]?)\s+([^\n]{0,50})"),
    re.compile(r"^(\d[A-E]\d{3})\b([^\n]{0,60})"),          # ECCN，如 3A090
    # Item 后**必须有 `. ` 作结**，否则 "Item 1H26 | Item 2" 会被整段吞成标题名（实测踩过）
    re.compile(r"^(Item\s+\d+[A-C]?)\.\s+([A-Z][^\n]{0,60})"),
    re.compile(r"^(PART\s+[IVX]+)\b([^\n]{0,60})"),
]
LEVEL2 = [
    re.compile(r"^([一二三四五六七八九十]+、)\s*([^\n]{0,30})"),
    re.compile(r"^(\([一二三四五六七八九十]+\))\s*([^\n]{0,30})"),
]

# **前缀**标题：用于「标题在长行开头」的情况。财报和英文 IR 常把标题与正文
# 排成同一段（PDF 抽出来就是一行长的），按上面的「行必须短」判据会全部漏掉——
# 实测 SK 海力士**100%** 的块、三星 47% 的块因此没有章节标签，
# 而这两家恰恰是论文要讲的三星/海力士。这些模式只锚定**开头一小段**，
# 字符类里不含句点，所以在长行上也安全（匹配到 "Introduction" 就停，不会吞掉后半句）。
PREFIX = [
    re.compile(r"^(§+\s*[\d.]+[a-z]?)\s+([A-Z][A-Za-z ,\-]{2,45})"),
    re.compile(r"^(Consolidated\s+(?:Interim\s+)?Statements?\s+of\s+[A-Za-z ,]{2,50})"),
    re.compile(r"^(Consolidated\s+Statements?\s+of\s+[A-Za-z ,]{2,50})"),
    re.compile(r"^(Supplement No\.\s*\d+ to Part \d+)"),
    re.compile(r"^(\d[A-E]\d{3})\s"),
    re.compile(r"^(Item\s+\d+[A-C]?)\.\s+([A-Z][A-Za-z ,&\-]{2,45})"),
    re.compile(r"^([IVX]{1,4}\.\s+[A-Z][A-Za-z ,&\-]{2,45})"),
]
MAX_HEAD_LINE = 46                 # 标题行最长这么多字
PREFIX_PROBE = 220                 # 长行只拿开头这么多字去匹配前缀标题

# 这些来源的抽取器**一块就是一条**（`plain.py`：一个 § 或一个 ECCN 一个块），
# 所以块与块之间不能继承章节状态 —— 继承了就是**贴错标签**。
# 实测：CCL 里 3A090 那一条 13,220 字，本身没被识别成标题时，
# 它下面的块会把**上一条 ECCN（2D018）**的标签继承过来，引用就指错了地方。
# 而 SEC 的 HTML 是**一块一段**，Item 7 的标题单独成块、后面段落靠继承，
# 所以那条路必须保持继承。用来源区分，是因为这是**抽取器结构**的差异，不是内容的差异。
BLOCK_IS_SECTION = {"fedreg", "govinfo", "ecfr"}


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def detect_section(line):
    """返回 (级别, 标题文本)。级别 1 = 该切断，2 = 只更新标签，0 = 不是标题。"""
    t = _norm(line)
    if not t:
        return 0, ""
    if len(t) <= MAX_HEAD_LINE:
        for pat in LEVEL1:
            m = pat.match(t)
            if m:
                return 1, _norm(" ".join(g for g in m.groups() if g))[:80]
        for pat in LEVEL2:
            m = pat.match(t)
            if m:
                return 2, _norm(" ".join(g for g in m.groups() if g))[:80]
        return 0, ""
    # 长行：只拿**开头一段**去匹配前缀标题。不能因为「整行很长」就放弃——
    # CCL 里每条 ECCN 的正文都是一整行（3A090 那条 13,220 字），
    # 长度上限卡住它，它就永远认不出自己是谁。
    for pat in PREFIX:
        m = pat.match(t[:PREFIX_PROBE])
        if m:
            return 1, _norm(" ".join(g for g in m.groups() if g))[:80]
    return 0, ""


# 页脚页码：巨潮年报每页都有 `3 / 281` 这种「本页 / 总页」。
# 它不含任何信息、却**每页都出现**，留着会让每个块都拖一条尾巴，
# 还会在 BM25 里把「281」这种数字的频率抬得虚高。阶段 3 开头就把它去掉。
FOOTER_RE = re.compile(r"^\d{1,4}\s*/\s*\d{1,4}$")


def units_from_text(text):
    """把一页/一块的文字拆成**不可再分**的单元。

    含 ` | ` 的行是阶段 2 拍平的表行 → 整行一个单元，**不切**。
    其余按句末切。返回 [(单元文本, 是否表行)]。
    """
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or FOOTER_RE.match(line):
            continue
        if " | " in line:                       # 已拍平的表行：原子
            out.append((line, True))
            continue
        for piece in SENT_SPLIT.split(line):
            piece = piece.strip()
            if piece:
                out.append((piece, False))
    return out


def pack(units, limit=LIMIT_CHARS, overlap=OVERLAP_CHARS):
    """把单元打包成块。

    `units` 是 [(文本, 页号, 标签, 一级章节)]。返回 [(文本, 起页, 止页, 起始单元号, 单元数)]。
    - 不足 limit 时**至少放一个单元**（否则超长表行/超长 ECCN 段会死循环）；
    - 只在**一级章节**变化处断开（二级标题只换标签，见 LEVEL1/LEVEL2 注释）；
    - 重合按**整单元**回退到 ≥overlap 字为止（不按字符切单元，否则又切坏了行/句）。
    """
    chunks = []
    i, n = 0, len(units)
    while i < n:
        buf, pages, used = [], [], 0
        j = i
        while j < n:
            u = units[j][0]
            if buf and used + len(u) + 1 > limit:
                break
            if buf and units[j][3] != units[i][3]:      # 一级章节变了才断开
                break
            buf.append(u)
            pages.append(units[j][1])
            used += len(u) + 1
            j += 1
        if not buf:
            break
        chunks.append(("\n".join(buf), min(pages), max(pages), i, j - i))
        if j >= n:
            break
        k, back = j, 0
        while k > i + 1 and back < overlap:             # 回退，形成重合
            k -= 1
            back += len(units[k][0]) + 1
        i = k if k > i else j
    return chunks


def chunk_doc(pages, source=""):
    """一份文档 → (块列表, 单元数)。块是 dict，含正文与定位信息。

    只走一遍：先按页把文字拆成带 (页号, 标签, 一级章节) 的单元，再打包。
    章节状态**跨页延续**——`第三节` 的标题出现在第 12 页，第 13 页的块仍属于它；
    但库B（一块一条）**不延续**，每块各自认自己的标题（见 BLOCK_IS_SECTION）。
    """
    per_block = source in BLOCK_IS_SECTION
    units, cur_lbl, cur_l1 = [], "", ""
    for pg in pages:
        text = pg.get("text") or ""
        if not text:
            continue
        loc = pg.get("page")
        if per_block:                      # 新块 = 新条，先清空，免得继承上一条的标签
            cur_lbl, cur_l1 = "", ""
        for line in text.split("\n"):
            lvl, name = detect_section(line)
            if lvl:
                cur_lbl = name
                if lvl == 1:
                    cur_l1 = name          # 一级章节既换标签、也换断点
        for u, _is_row in units_from_text(text):
            units.append((u, loc, cur_lbl, cur_l1))

    out = []
    for text, p0, p1, st, nu in pack(units):
        out.append({
            "text": text, "page_start": p0, "page_end": p1,
            "section": units[st][2] if st < len(units) else "",
            "n_units": nu,
        })
    return out, len(units)


def drop_tiny(chunks):
    """丢掉过短的块（`< MIN_CHUNK` 字）。返回 (保留的块, 丢掉的块)。

    这些块是**板块边界上的残渣**：章节页只有一行 `□适用 √不适用` 或一个标题，
    切出来不足 40 字。留着它们会污染检索——问什么它都可能被 BM25 顶上来
    （短块命中关键词的相对分天然高），却什么也答不了。
    宁可少几块，也不要往索引里塞「□适用 √不适用」。
    """
    keep, drop = [], []
    for c in chunks:
        (drop if len(c["text"]) < MIN_CHUNK else keep).append(c)
    return keep, drop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="只切这些来源，逗号分隔")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    only = {s.strip() for s in args.only.split(",") if s.strip()}
    files = sorted(p for p in EXTRACTED.rglob("*.jsonl")
                   if not only or p.relative_to(EXTRACTED).parts[0] in only)
    if args.limit:
        files = files[:args.limit]

    print("=" * 84)
    print(f"阶段 3 · 切块：{len(files)} 份，{LIMIT_CHARS} 字/块，重合 {OVERLAP_CHARS} 字，句末收尾")
    print("=" * 84)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    stats, sizes, n_chunk, n_doc, n_unit, sec_hit, n_drop = [], [], 0, 0, 0, 0, 0
    samples = []
    by_src = {}

    with open(out_path, "w", encoding="utf-8") as fo:
        for fi, f in enumerate(files, 1):
            rows = []
            with open(f, encoding="utf-8") as fh:
                for ln in fh:
                    if '"__meta__"' in ln:
                        continue
                    ln = ln.strip()
                    if ln:
                        rows.append(json.loads(ln))
            if not rows:
                continue
            meta = {k: rows[0].get(k) for k in
                    ("doc_id", "source", "company", "title", "date", "url", "file", "unit")}
            chunks, n_u = chunk_doc(rows, meta.get("source") or "")
            chunks, dropped = drop_tiny(chunks)
            n_drop += len(dropped)
            n_doc += 1
            n_unit += n_u
            s = by_src.setdefault(meta.get("source") or "?", {"docs": 0, "chunks": 0, "chars": 0})
            s["docs"] += 1

            for seq, c in enumerate(chunks):
                rec = {
                    "chunk_id": f"{meta['doc_id']}::{seq:05d}",
                    "doc_id": meta["doc_id"], "source": meta["source"],
                    "company": meta["company"], "title": meta["title"],
                    "date": meta["date"], "url": meta["url"], "file": meta["file"],
                    "unit": meta["unit"], "page_start": c["page_start"],
                    "page_end": c["page_end"], "section": c["section"],
                    "seq": seq, "chars": len(c["text"]), "n_units": c["n_units"],
                    "text": c["text"],
                }
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_chunk += 1
                sizes.append(len(c["text"]))
                s["chunks"] += 1
                s["chars"] += len(c["text"])
                if c["section"]:
                    sec_hit += 1
                if len(samples) < 12 and seq in (0, 3):
                    samples.append(rec)

            if fi % 20 == 0 or fi == len(files):
                print(f"  [{fi:>3}/{len(files)}] 累计 {n_chunk:,} 块")

    el = time.time() - t0
    sizes.sort()
    def pct(q):
        return sizes[min(len(sizes) - 1, int(len(sizes) * q))] if sizes else 0
    over = sum(1 for x in sizes if x > LIMIT_CHARS)
    tiny = sum(1 for x in sizes if x < MIN_CHUNK)

    L = ["# 阶段 3 切块报告\n",
         f"- 参数：**{LIMIT_CHARS} 字/块，重合 {OVERLAP_CHARS} 字，句末收尾**（课程 p25）",
         f"- 文档 **{n_doc}** 份 → 块 **{n_chunk:,}** 个；用时 {el:.1f}s",
         f"- 单元总数 {n_unit:,}（表行按整行算一个单元）\n",
         "## 块长分布（字符）\n",
         "| 最小 | p10 | 中位 | p90 | p99 | 最大 | 超 800 | 少于 40 |",
         "|---:|---:|---:|---:|---:|---:|---:|---:|",
         f"| {sizes[0] if sizes else 0} | {pct(.1)} | {pct(.5)} | {pct(.9)} | {pct(.99)} "
         f"| {sizes[-1] if sizes else 0} | {over} | {tiny} |",
         "",
         f"- 带章节标签的块：**{sec_hit:,} / {n_chunk:,}**（{sec_hit/max(n_chunk,1):.1%}）",
         ""]
    L.append("## 分来源\n")
    L.append("| 来源 | 文档 | 块 | 字 | 块均字 |")
    L.append("|---|---:|---:|---:|---:|")
    for s, v in sorted(by_src.items(), key=lambda kv: -kv[1]["chunks"]):
        L.append(f"| {s} | {v['docs']} | {v['chunks']:,} | {v['chars']:,} "
                 f"| {v['chars']/max(v['chunks'],1):.0f} |")
    L.append("")
    L.append("## 抽样块\n")
    for r in samples[:6]:
        L.append(f"**`{r['chunk_id']}`**  第 {r['page_start']}–{r['page_end']} "
                 f"{'页' if r['unit']=='page' else '块'} · 章节 `{r['section']}` · {r['chars']} 字")
        L.append("```")
        L.append(r["text"][:420])
        L.append("```")
        L.append("")
    REPORT.write_text("\n".join(L), encoding="utf-8")

    print("-" * 84)
    print(f"文档 {n_doc} 份 → 块 {n_chunk:,} 个（另丢弃过短块 {n_drop:,} 个）")
    print(f"中位 {pct(.5)} 字，p90 {pct(.9)}，最大 {sizes[-1] if sizes else 0}")
    print(f"超 {LIMIT_CHARS} 字 {over} 个｜少于 {MIN_CHUNK} 字 {tiny} 个｜带章节 {sec_hit/max(n_chunk,1):.1%}")
    print(f"产出 {out_path}；报告 {REPORT}")


if __name__ == "__main__":
    main()

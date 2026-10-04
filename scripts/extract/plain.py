# -*- coding: utf-8 -*-
"""
阶段 2 · 纯文本 与 XML 抽取（库B · 规则库）

库B 是**论文的规范依据**，不是公司经营数据：要能指着「15 CFR 774.1 第 (a) 段」
说话，所以这里的抽取目标跟库A 正好相反——
库A 要「拍平成标签+数值」，库B 要**保留条款编号、按条成块**，
一条一块，块内不拆，引用时能整条取出。

两种输入：
  · `.txt`  —— Federal Register 全文（`89_FR_96790.txt` 这种）。空行分段。
  · `.xml`  —— eCFR / CFR 的官方 XML。按 SECTION 成块，**§ 号在正文里**
              （eCFR 是 `<DIV8 N="774.1" TYPE="SECTION">`，bulk CFR 是 `<SECTION>`，
               两者正文开头都自带 `§ 774.1`），所以不必另造编号，原样留着即可。

⚠️ 一个坑：XML 里 SECTION 会**嵌套**。若对每个 SECTION 都取 `itertext()`，
父条的文本会把它所有子条的文本一起吞进去，同一段话在库里出现好几遍。
处理办法与 `html.py` 一致：**有同类祖先的节点整棵剪掉**，只留最外层的条。
"""
import re
from pathlib import Path

from lxml import etree

# 视作「一条」的标签（去命名空间后的本地名）
SECTION_TAGS = {"SECTION", "DIV8", "DIV9"}
FALLBACK_BLOCK_TAGS = {"P", "FP", "FP-1", "FP-2", "HED", "NOTE", "SUBJECT"}

# 超大条（如 CCL）内部的再切边界。
# 为什么必须再切：Part 774 的 **Supplement No. 1 就是整份《商业管制清单》**——
# 实测 2024-11-01 版这一条 **132 万字**，而 3A090 只是里面一个 ECCN。
# 不切的话 3A090 的参数会被阶段 3 按 800 字机械切断，块里认不出是哪个 ECCN，
# 检索「3A090 管制参数」就取不回完整一条。
# **边界只认 `FP-2`**：它是每个 ECCN 的开头（正文以 ECCN 码打头，如 `0A002 Power generating…`）。
# `HD1` 不能一律当边界——实测 3A090 一条里，「List Based License Exceptions」
# 「List of Items Controlled」这些**条内小标题**也是 `HD1`，全当边界会把**一条 ECCN 劈成三块**
# （实测：319 管制要求 / 320 许可例外 / 321 物项参数），检索时侯取不全。
# 只在 `HD1` 是「Category 3—Electronics」「A. …」这种类/组标题时才切。
SPLIT_TAGS = {"FP-2"}
CATEGORY_RE = re.compile(r"^(Category\s|[A-F]\.)")
BIG_SECTION = 50_000          # 超过这么多字的条，才做 ECCN 级再切


def _norm(s):
    if not s:
        return ""
    s = s.replace("\xa0", " ").replace("", "").replace("​", "")
    return re.sub(r"[ \t]+", " ", s).strip()


def _localname(tag):
    return tag.rpartition("}")[2] if isinstance(tag, str) else ""


def _is_boundary(node):
    """判断一个元素是不是「新一条」的开头。"""
    ln = _localname(node.tag)
    if ln in SPLIT_TAGS:
        return True
    if ln == "HD1":                  # 只认类/组标题，条内小标题不算（见 SPLIT_TAGS 注释）
        return bool(CATEGORY_RE.match(_norm(node.text or "")))
    return False


def _segmented(el, split_tags=None):
    """按 `_is_boundary` 在**文档顺序**上切段，文本只取一次。

    为什么不逐个子节点取 `itertext()`：父节点的 itertext 会把所有后代的文本一起吞进去，
    父子都取就会让同一段话在库里出现好几遍（`html.py` 的表格也踩过同一个坑）。
    这里改成自己走一遍树：进到边界标签就冲掉当前缓冲、另起一段，
    其余文本原样累积，**每个字符只经过一次**。
    """
    out, buf = [], []

    def flush():
        t = _norm(" ".join(" ".join(buf).split()))
        if len(t) >= 2:
            out.append(t)
        buf.clear()

    def walk(node):
        if _is_boundary(node):
            flush()
        if node.text:
            buf.append(node.text)
        for ch in node:
            walk(ch)
            if ch.tail:
                buf.append(ch.tail)

    if el.text:
        buf.append(el.text)
    for ch in el:
        walk(ch)
        if ch.tail:
            buf.append(ch.tail)
    flush()
    return out


def extract_txt(path, meta=None):
    """纯文本：按空行分段。返回 (blocks, info)。

    ⚠️ Federal Register 的 `full_text/text` 端点**不是纯文本**，是 HTML 包着的：
    `<html><head><title>…` 再套一个 `<pre>`，正文在 pre 里按 ~72 列**硬折行**。
    当纯文本读会把标签混进索引（`<html> <head> <title>Federal Register, Volume 89…`
    整行进了块），所以先认出来、走 DOM 取 `<pre>`。
    段内再把硬折行接回一行；行首的 `[[Page 96789]]` 是 FR 的页码标记，**留着**
    （引用时要指到 FR 页码，这是最有用的定位信息）。
    """
    meta = meta or {}
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    head = raw[:2000].lower()
    if "<html" in head or "<pre" in head:
        try:
            import lxml.html
            doc = lxml.html.fromstring(raw.encode("utf-8"))
            pre = doc.find(".//pre")
            body = (pre if pre is not None else doc).text_content()
        except Exception:
            body = raw
        note = "空行分段（自 HTML 的 <pre> 取正文）"
    else:
        body, note = raw, "空行分段"

    blocks = []
    for para in re.split(r"\n\s*\n", body):
        t = re.sub(r"\s+", " ", para).strip()
        if len(t) >= 2:
            blocks.append(t)
    return _pack(blocks, path, meta, source_note=note)


def extract_xml(path, meta=None):
    """XML：按最外层 SECTION/DIV8/DIV9 成块；找不到条就退回按段落标签成块。"""
    meta = meta or {}
    try:
        root = etree.parse(str(path)).getroot()
    except Exception as e:
        return [], {"file": Path(path).name, "pages": 0, "chars": 0, "tables": 0,
                    "tables_dropped": 0, "unit": "block",
                    "error": f"{type(e).__name__}: {e}", **meta}

    secs = [e for e in root.iter() if _localname(e.tag) in SECTION_TAGS]
    # 剪掉嵌套：只保留**没有同类祖先**的那些（否则父条会把子条文本吞进去，重复入库）
    secset = set(secs)
    outermost = [e for e in secs if not any(a in secset for a in e.iterancestors())]

    if outermost:
        blocks = []
        n_big = 0
        for e in outermost:
            t = _norm(" ".join("".join(e.itertext()).split()))
            if len(t) > BIG_SECTION:
                # 超大条（CCL 就是这种）：按 ECCN 边界再切，别让 800 字的机械切分
                # 把 3A090 的参数拦腰截断
                n_big += 1
                blocks.extend(_segmented(e, SPLIT_TAGS))
            elif t:
                blocks.append(t)
        note = f"按条成块（{len(outermost)} 条，已剪掉嵌套）" + \
               (f"；其中 {n_big} 条超 {BIG_SECTION//1000}k 字，已按 ECCN/类标题再切" if n_big else "")
    else:
        blocks, note = [], "无条级标签，退回按段落标签成块"
        for e in root.iter():
            if _localname(e.tag) in FALLBACK_BLOCK_TAGS:
                t = _norm(" ".join("".join(e.itertext()).split()))
                if len(t) >= 2:
                    blocks.append(t)
        if not blocks:                       # 再退一步：整篇按空行切
            note += " → 再退回空行分段"
            return extract_txt(path, meta)
    return _pack(blocks, path, meta, source_note=note)


def _pack(blocks, path, meta, source_note=""):
    """统一成与 PDF/HTML 路同形的 pages 列表，好让阶段 3 只认一种格式。

    `page` 字段在这里是**顺序块号**（`unit` 标 `block`），不是页码。
    """
    pages = []
    for i, t in enumerate(blocks, 1):
        pages.append({"page": i, "text": t, "tables": 0, "tables_dropped": 0,
                      "drop_reasons": [], "strategy": source_note,
                      "chars": len(t), "kind": "block"})
    info = {
        "file": Path(path).name,
        "pages": len(pages),
        "text_pages": sum(1 for p in pages if p["chars"] > 0),
        "empty_pages": 0,
        "chars": sum(p["chars"] for p in pages),
        "tables": 0,
        "tables_dropped": 0,
        "unit": "block",
        **meta,
    }
    return pages, info


if __name__ == "__main__":
    import sys
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    for p in sys.argv[1:]:
        fn = extract_xml if p.lower().endswith(".xml") else extract_txt
        blocks, info = fn(p)
        print(f"\n=== {info['file']} ===")
        print(f"  {info['pages']} 块，{info['chars']:,} 字  [{blocks[0]['strategy'] if blocks else ''}]")
        for b in blocks[:2]:
            print(f"  #{b['page']} {b['text'][:170]!r}")

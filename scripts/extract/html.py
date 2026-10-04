# -*- coding: utf-8 -*-
"""
阶段 2 · HTML 抽取（SEC EDGAR 的 10-K/10-Q）

美光的申报是 `.htm` 而不是 PDF —— SEC 的 EDGAR 全文就是 HTML（含内联 XBRL）。
所以不能拿 PDF 那条路走，得单独解析 DOM。

与 PDF 路的共同原则：**表格拍平成「标签+数值」的行文本**，数字不脱离标签。
表格的过滤与格式化逻辑**与 PDF 路共用 `tablefmt.py`**，避免两边漂移。

三点差异要说清：
1. **没有页码**。HTML 无分页概念，用**文档内顺序块号**做定位（`page` 字段存块号，
   `unit` 字段标 `block` 以示区别）。引用时要靠章节名（如 Item 7 MD&A）而不是页码。
2. **表格更规整**。HTML 的 <table>/<tr>/<td> 结构明确，colspan/rowspan 要**展开成网格**，
   否则列会错位——这点比 PDF 好办。
3. **要丢掉隐藏的 XBRL**。EDGAR 的内联 XBRL 把机器读取用的事实塞在 `ix:header` 里
   （含 `ix:hidden`），必须删；但 `ix:nonfraction` 等**包的正是给人看的数字，不能删**。
"""
import re
from pathlib import Path

import lxml.html

from .tablefmt import cell_text, flatten_table, table_ok

# 这些标签里的内容不要。
# ⚠️ **不要**按「带冒号就删」来清 XBRL —— 内联 XBRL 里 `ix:nonfraction` 等标签
# 包的正是**给人看的数字**，删掉就把数据删了。真正该删的只有 `ix:header`
# （里面是 `ix:hidden`，机器读取用的隐藏事实，重复且无阅读价值）。
# 另外按 style 里的 display:none / visibility:hidden 删。
DROP_TAGS = {"script", "style", "head", "meta", "link", "noscript", "ix:header"}

# 块级标签：遇到就把当前段落缓冲刷出去
BLOCK_TAGS = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
              "table", "section", "article", "hr", "td"}


def _norm(s):
    if not s:
        return ""
    s = s.replace("\xa0", " ").replace("", "").replace("​", "")
    return re.sub(r"\s+", " ", s).strip()


def _tbody_grid(table_el):
    """把 <table> 展成规整网格，**处理 colspan/rowspan**。

    不展开就会列错位：一个 colspan=3 的表头格会把它后面所有列整体左移，
    于是「期初余额」的数字会跑到「期末余额」名下——**错得不报错，只是安静地错**。
    展开只负责对齐；输出时由 `tablefmt.dedup_runs` 把重复压回去。
    """
    grid, pending = [], {}          # pending: {列号: (剩余行数, 值)}
    for tr in table_el.iter("tr"):
        row, col = [], 0
        cells = [c for c in tr if c.tag in ("td", "th")]

        def flush_pending():
            nonlocal col
            while col in pending:
                left, val = pending[col]
                row.append(val)
                if left <= 1:
                    del pending[col]
                else:
                    pending[col] = (left - 1, val)
                col += 1

        flush_pending()
        for c in cells:
            flush_pending()
            val = cell_text(c.text_content())
            try:
                cs = max(1, int(c.get("colspan") or 1))
                rs = max(1, int(c.get("rowspan") or 1))
            except ValueError:
                cs = rs = 1
            cs = min(cs, 60)         # 防畸形 colspan 造出巨大的行
            for k in range(cs):
                row.append(val)
                if rs > 1:
                    pending[col + k] = (rs - 1, val)
            col += cs
        flush_pending()
        if any(row):
            grid.append(row)
    return grid


def extract_html(path, meta=None):
    """抽一份 HTML。返回 (pages, info)；pages 每项是 {page, text, tables, ...}。

    `page` 在 HTML 路里是**顺序块号**，不是页码——见模块头说明。
    """
    meta = meta or {}
    # ⚠️ 必须传 **bytes**。这些文件是 XBRL 包装的 XHTML，开头有
    # `<?xml version='1.0' encoding='ASCII'?>`，而 lxml 收到 **str** 时会抛
    # `ValueError: Unicode strings with encoding declaration are not supported`。
    # 我第一版就是这么写的，还被 except 吞掉、静默返回 0 块 —— 不报错的错。
    raw = Path(path).read_bytes()
    try:
        root = lxml.html.fromstring(raw)
    except Exception as e:
        return [], {"file": Path(path).name, "pages": 0, "chars": 0, "tables": 0,
                    "tables_dropped": 0, "unit": "block",
                    "error": f"{type(e).__name__}: {e}", **meta}

    # 清掉不要的标签。先物化成 list —— 边遍历边 drop_tree 会把迭代器搞坏。
    for el in list(root.iter()):
        tag = el.tag if isinstance(el.tag, str) else ""
        style = (el.get("style") or "").replace(" ", "").lower()
        hidden = ("display:none" in style) or ("visibility:hidden" in style)
        if tag in DROP_TAGS or hidden:
            try:
                el.drop_tree()
            except Exception:
                pass

    items = []          # [(块号, kind, text)]
    buf = []
    block = 0

    def flush():
        nonlocal buf, block
        t = _norm(" ".join(buf))
        if t:
            block += 1
            items.append((block, "text", t))
        buf = []

    # ⚠️ 表格的**后代节点要从正文流里整棵剪掉**。
    # 不剪的话，同一张表会进索引两次：一次是拍平后带标签的 `期末余额 1,234`（有用），
    # 一次是 `<td>` 被当成块级标签逐格刷出来的碎片（`1,234`、`5,678` 各自成块，全无标签）。
    # PDF 路是靠「块中心落在表格 bbox 内就丢」达到同样效果；HTML 有 DOM 树，直接剪子树更准。
    # 实测：不剪时美光 10-K 有 580 个重复块，剪完只剩正文里本来就重复的那几处。
    tables = {el for el in root.iter() if el.tag == "table"}

    for el in root.iter():
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag == "table":
            flush()
            rows = _tbody_grid(el)
            ok, why = table_ok(rows)
            if ok:
                flat = flatten_table(rows)
                if flat.strip():
                    block += 1
                    items.append((block, "table", flat))
            else:
                items.append((0, "drop", why))
            # `tail` 是**表外**的文字（紧跟表格之后），不属于表，别跟着一起剪掉
            if el.tail:
                buf.append(el.tail)
            continue
        if any(a in tables for a in el.iterancestors()):
            continue                      # 表格内部：已在上面整表处理过，这里跳过
        if tag in BLOCK_TAGS:
            flush()
        if el.text:
            buf.append(el.text)
        if el.tail:
            buf.append(el.tail)
    flush()

    drops = [t for _b, k, t in items if k == "drop"]
    items = [(b, k, t) for b, k, t in items if k != "drop"]

    pages = []
    for b, k, t in items:
        pages.append({"page": b, "text": t, "tables": 1 if k == "table" else 0,
                      "tables_dropped": 0, "drop_reasons": [], "strategy": "html",
                      "chars": len(t), "kind": k})

    info = {
        "file": Path(path).name,
        "pages": len(pages),
        "text_pages": sum(1 for p in pages if p["chars"] > 0),
        "empty_pages": 0,
        "chars": sum(p["chars"] for p in pages),
        "tables": sum(p["tables"] for p in pages),
        "tables_dropped": len(drops),
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
        pages, info = extract_html(p)
        print(f"\n=== {info['file']} ===")
        print(f"  {info['pages']} 块，{info['chars']:,} 字，表 {info['tables']} 张"
              f"（丢弃 {info['tables_dropped']}）")
        for pg in pages[:3]:
            print(f"  [{pg['kind']}] {pg['text'][:180]!r}")

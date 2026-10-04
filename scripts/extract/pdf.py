# -*- coding: utf-8 -*-
"""
阶段 2 · PDF 抽取：文字层 + 表格拍平

设计要点（都由 `_probe/stage2_probe.py`、`_probe/stage2_tables.py` 的实测支撑）：

1. **不需要 OCR**。抽样 300 页，无文字层页面占 0%——都是数字生成的 PDF。
   所以不走 OCR，GPU 在这一步没有角色。

2. **表格拍平成「标签+数值」的行文本，而不是保留版式**。
   知识库要的是「数字不脱离标签」——检索「交易性金融资产 期末余额」得命中那一行。
   保留网格反而会把标签和数字拆到不同块里，两边都检索不到。
   具体规则见 `tablefmt.py`（与 HTML 路共用）。

3. **表格区域的原文块要丢掉**，否则同一张表会在文本里出现一次（乱序碎片）、
   在表格里再出现一次（拍平），既重复又污染检索。
   做法：按块中心点是否落在表格 bbox 内判断，落内的文本块不再单独输出。
"""
import re
from pathlib import Path

import pymupdf

from .tablefmt import flatten_table, join_wrapped_lines, table_ok


def _find_tables(page):
    """只用 `lines` 策略。返回 (tables, strategy_used)。

    ⚠️ 曾经写成「`lines` 找不到就回退到 `text`」——**实测证明回退有害，已删除**。
    实测（`_probe/stage2_tables.py` 及后续抽样）：
      · 中文年报：`text` 只多找 1–2 页，内容同样不可靠（合并单元格更乱）
      · 三星英文 IR：**358 页里在 146 页触发**，抽出来全是把多栏正文按位置切碎
        再交错拼接的垃圾 ——
          `NTS OF (In millio | FIN ns of K | ANCIAL POS orean won`
          `ELECTR 2025 | ONICS C Business | o., Ltd. Report`
        连真·财务报表页（CONSOLIDATED STATEMENTS OF FINANCIAL POSITION）也被切碎。
    `text` 是纯几何聚类，**不含「这是不是表格」的判断**，它只会把多栏正文当成表。
    而垃圾进索引比「少一张表」更糟——数字本来就在文字层里，丢的是版式、不是信息。
    """
    try:
        return list(page.find_tables(strategy="lines").tables), "lines"
    except Exception:
        return [], "none"


def extract_page(page, page_no):
    """抽一页。返回 dict：正文 + 拍平后的表格 + 计数。"""
    tabs, strat = _find_tables(page)
    tboxes = [t.bbox for t in tabs]

    # 只判一次：哪些表留、哪些丢，留下的把拍平文本算好
    kept, dropped = [], []
    for t in tabs:
        try:
            rows = t.extract()
        except Exception as e:
            dropped.append(f"extract 失败 {type(e).__name__}")
            continue
        ok, why = table_ok(rows)
        if not ok:
            dropped.append(why)
            continue
        flat = flatten_table(rows)
        if flat.strip():
            kept.append((t.bbox[1], flat))
        else:
            dropped.append("拍平后为空")

    def in_table(bb):
        """块中心点是否落在某张表内（落在内的原文块要丢弃，避免与拍平结果重复）。"""
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        return any(tb[0] <= cx <= tb[2] and tb[1] <= cy <= tb[3] for tb in tboxes)

    # 正文块 + 表格，按 y 坐标排序，保留阅读顺序
    items = []
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, txt, _bno, btype = b
        if btype != 0:                       # 1 = 图片块，跳过
            continue
        # 块内被版式折断的行要接回去（中日韩字之间不插空格，见 tablefmt 注释）
        txt = re.sub(r"[ \t]+", " ", join_wrapped_lines(txt)).strip()
        if not txt or in_table((x0, y0, x1, y1)):
            continue
        items.append((y0, "text", txt))
    for y, flat in kept:
        items.append((y, "table", flat))
    items.sort(key=lambda x: x[0])

    body = "\n".join(txt for _y, _k, txt in items)
    n_tab = sum(1 for _y, k, _t in items if k == "table")
    return {
        "page": page_no,
        "text": body,
        "tables": n_tab,
        "tables_dropped": len(dropped),
        "drop_reasons": dropped[:6],
        "strategy": strat,
        "chars": len(body),
        "kind": "page",
    }


def extract_pdf(path, meta=None):
    """抽一份 PDF。返回 (pages, info)。pages 每项是 extract_page 的结果。"""
    meta = meta or {}
    doc = pymupdf.open(str(path))
    pages = []
    for i in range(doc.page_count):
        try:
            pages.append(extract_page(doc[i], i + 1))
        except Exception as e:
            pages.append({"page": i + 1, "text": "", "tables": 0, "tables_dropped": 0,
                          "drop_reasons": [f"整页失败 {type(e).__name__}: {e}"],
                          "strategy": "err", "chars": 0, "kind": "page"})
    n = doc.page_count
    doc.close()
    info = {
        "file": Path(path).name,
        "pages": n,
        "text_pages": sum(1 for p in pages if p["chars"] > 0),
        "empty_pages": sum(1 for p in pages if p["chars"] == 0),
        "chars": sum(p["chars"] for p in pages),
        "tables": sum(p["tables"] for p in pages),
        "tables_dropped": sum(p["tables_dropped"] for p in pages),
        "unit": "page",
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
        pages, info = extract_pdf(p)
        print(f"\n=== {info['file']} ===")
        print(f"  {info['pages']} 页，有字 {info['text_pages']}，空页 {info['empty_pages']}，"
              f"{info['chars']:,} 字，表 {info['tables']} 张（丢弃 {info['tables_dropped']}）")
        for pg in pages[:2]:
            if pg["text"]:
                print(f"  --- 第 {pg['page']} 页预览 ---")
                print("  " + pg["text"][:300].replace("\n", "\n  "))
                break

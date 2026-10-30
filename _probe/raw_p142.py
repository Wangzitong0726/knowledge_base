# -*- coding: utf-8 -*-
"""单页原始表格转储：只用 pymupdf 打开、只处理指定页（不跑整份 PDF，快）。
用来判断「新表头对不对」——不能只看扁平化结果，要看它到底选了哪一行。
"""
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import extract.tablefmt as NEW                                   # noqa: E402

PDF = ROOT / "data/raw/szse/雅克科技/002409_2024-04-26_雅克科技：2023年年度报告（更新前）.PDF"
PAGE = 142

doc = pymupdf.open(str(PDF))
page = doc[PAGE - 1]
tabs = page.find_tables(strategy="lines").tables
print("%s p%d：找到 %d 张表" % (PDF.name, PAGE, len(tabs)))
last = None
for ti, t in enumerate(tabs):
    rows = NEW.clean_rows(t.extract())
    if not rows or not NEW.table_ok(rows)[0]:
        continue
    print("\n── 表 %d  bbox_y=%.0f  原始行 ──" % (ti, t.bbox[1]))
    for ri, r in enumerate(rows):
        print("   [%d] %s" % (ri, [c for c in r]))
    n = NEW.pick_header(rows)
    print("   >> 新选中的表头行号：%s → %s" % (n, rows[n] if n is not None else "（不猜）"))
    inh = None
    try:
        import extract.pdf as PDFM
        inh = PDFM.inherit_for(t.bbox[1], page.rect.height, max(len(r) for r in rows), last)
    except Exception as e:
        print("   (inherit_for 不进)", e)
    print("   >> 跨页继承来的表头：%s" % inh)
    flat, carried = NEW.flatten_table(rows, inherited=inh)
    if carried:
        last = carried
doc.close()

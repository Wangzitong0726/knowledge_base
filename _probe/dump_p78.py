# -*- coding: utf-8 -*-
"""江波龙 2025 半年报 p76–78 原表逐张 dump：查 `资本公积 | 应付票据 …` 这个表头哪来的。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pymupdf                                              # noqa: E402
from extract import tablefmt as T                           # noqa: E402
from extract import pdf as PDF                              # noqa: E402

P = ROOT / "data/raw/cninfo/江波龙/301308_2025-08-23_2025年半年度报告.pdf"
doc = pymupdf.open(str(P))
last = None
for pno in (76, 77, 78):
    page = doc[pno - 1]
    tabs = page.find_tables(strategy="lines").tables
    print("\n" + "=" * 78)
    print("第 %d 页   共 %d 张表   page_h=%.1f" % (pno, len(tabs), page.rect.height))
    for ti, t in enumerate(tabs, 1):
        rows = T.clean_rows(t.extract())
        ok, why = T.table_ok(rows)
        hdr = T.pick_header(rows)
        inh = PDF.inherit_for(t.bbox[1], page.rect.height,
                              max(len(r) for r in rows), last)
        print("\n  ── 表 %d  y0=%.1f  行数=%d 宽=%d  table_ok=%s%s"
              % (ti, t.bbox[1], len(rows), max(len(r) for r in rows) if rows else 0,
                 ok, "" if ok else "（%s）" % why))
        if not ok:
            continue
        print("     pick_header -> %s" % (hdr if hdr is not None else "None（不猜）"))
        print("     inherit_for -> %s" % (inh if inh is None else "继承 %s" % inh))
        for i, r in enumerate(rows[:6]):
            print("       row%d %s" % (i, [c[:22] for c in r if c]))
        flat, carried = T.flatten_table(rows, inherited=inh)
        if carried:
            last = carried
        print("     ── 拍平前 4 行 ──")
        for ln in flat.split("\n")[:4]:
            print("       %s" % ln[:104])
doc.close()

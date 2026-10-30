# -*- coding: utf-8 -*-
"""表头错配探针：把指定 PDF 页的**原始表网格**打出来，看 `flatten_table` 到底拿到了什么。

只读，不改任何产物。用于给「表头判据」的修改提供实测依据。

用法：
    C:/Python314/python.exe _probe/header_probe.py <pdf路径> <页码> [页码...]

页码是**人看的 1 起**页号（与 PDF 阅读器一致）。
"""
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract.tablefmt import (clean_rows, flatten_table, table_ok,  # noqa: E402
                              _header_score, collapse_keep_col)


def show(pdf, pages):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    doc = pymupdf.open(str(pdf))
    for pno in pages:
        page = doc[pno - 1]
        tabs = page.find_tables(strategy="lines").tables
        print("=" * 78)
        print("第 %d 页 · 找到 %d 张表" % (pno, len(tabs)))
        print("=" * 78)
        for ti, t in enumerate(tabs, 1):
            rows = t.extract()
            ok, why = table_ok(rows)
            print("\n--- 表 %d · bbox=%s · table_ok=%s %s" % (
                ti, tuple(round(v, 1) for v in t.bbox), ok, why))
            for i, r in enumerate(clean_rows(rows)):
                print("  row[%d] score=%-5s %s" % (i, _header_score(r), r))
            print("\n  collapse_keep_col(row[0]) = %s" % (collapse_keep_col(clean_rows(rows)[0]),))
            print("\n  >>> flatten_table（本页孤立调用，不带继承）：")
            for ln in flatten_table(rows)[0].split("\n")[:12]:
                print("      " + ln)
    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    show(sys.argv[1], [int(x) for x in sys.argv[2:]])

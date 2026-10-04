# -*- coding: utf-8 -*-
"""
阶段 2 预探 · 表格识别质量

上一测发现：PyMuPDF `find_tables()` 默认策略在中文年报上**25 页识别出 0 张表**。
这不是速度问题（速度是 CPU 的事，且 42ms/页 × 3.1 万页用多进程几分钟就完了），
是**能不能识别**的问题——阶段 2 要求「按行列还原表格」，识别不出来就无从还原。

PyMuPDF 支持不同策略：
  · lines        —— 默认，靠页面上的**表格线**
  · lines_strict —— 更严格
  · text         —— **不靠线**，按文本块的几何位置聚类
中文财报大量使用细线表、无线表，所以预期 text 策略命中率更高。实测验证。
"""
import sys
import time
from pathlib import Path

import pymupdf

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent

CASES = [
    ("巨潮·澜起科技2024年报", ROOT / "data/raw/cninfo/澜起科技/688008_2025-04-11_澜起科技2024年年度报告.pdf"),
    ("深交所·江波龙2024年报", ROOT / "data/raw/szse/江波龙/301308_2025-03-21_江波龙：2024年年度报告.PDF"),
    ("三星·2025_4Q IR", ROOT / "data/raw/samsung/三星电子/2025_4Q_Interim_Report.pdf"),
]

STRATEGIES = ["lines", "lines_strict", "text"]
KEYWORDS = ["资产负债表", "利润表", "现金流量表", "Consolidated", "Statement"]

print("=" * 88)
print("阶段 2 预探 · 表格识别：策略对比")
print("=" * 88)

for label, path in CASES:
    if not path.exists():
        print(f"[跳过] {label}（文件不存在）")
        continue
    doc = pymupdf.open(str(path))
    n = doc.page_count

    # 先找**含有报表关键词**的页 —— 这些页上「本该有表」
    hits = []
    for i in range(n):
        t = doc[i].get_text()
        if any(k in t for k in KEYWORDS):
            hits.append(i)
    print(f"\n【{label}】{n} 页，含报表关键词的页 {len(hits)} 页，取前 6 页做对比")
    probe = hits[:6]
    if not probe:
        doc.close()
        continue

    print(f"  {'页':>4}  " + "".join(f"{s:>16}" for s in STRATEGIES))
    agg = {s: 0 for s in STRATEGIES}
    for i in probe:
        row = []
        for s in STRATEGIES:
            try:
                tabs = doc[i].find_tables(strategy=s)
                c = len(tabs.tables)
                agg[s] += c
                row.append(f"{c:>6}表")
            except Exception as e:
                row.append(f"ERR".rjust(6))
        print(f"  {i:>4}  " + "".join(f"{c:>16}" for c in row))
    print(f"  {'合计':>4}  " + "".join(f"{agg[s]:>15}张" for s in STRATEGIES))

    # 用命中最好的策略，把第一张表的实际内容打出来看看对不对
    best = max(STRATEGIES, key=lambda s: agg[s])
    print(f"  → 命中最多的是 `{best}`（{agg[best]} 张）")
    for i in probe:
        tabs = doc[i].find_tables(strategy=best).tables
        if tabs:
            t = tabs[0]
            print(f"  示例：第 {i} 页 第 1 张表，{len(t.rows)} 行 × {len(t.header.names) if t.header else '?'} 列")
            for r in t.extract()[:4]:
                cells = [(c or "").replace("\n", " ")[:22] for c in r[:5]]
                print("     | " + " | ".join(cells))
            break
    doc.close()

print("\n" + "=" * 88)

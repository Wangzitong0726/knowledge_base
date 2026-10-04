# -*- coding: utf-8 -*-
"""
阶段 2 预探：PDF 抽取到底吃不吃 GPU？

先问对问题。PDF 抽文本是**解析**（解压 / 字形映射 / 排版分析），不是矩阵运算，
PyMuPDF 是纯 C 的 CPU 库、没有 CUDA 路径 → 预期 GPU 帮不上。
**但**有一个例外：如果页面是**扫描图**（没有文字层），就得 OCR，而 OCR 是 GPU 活。
所以真正要测的是两件事：

  1. 抽取速度：页/秒，据此估全库耗时
  2. **无文字层页面的比例** —— 决定要不要上 OCR（也就决定 GPU 有没有用）

抽样覆盖各来源与语言（中文年报 / 英文 IR / 英文 HTM）。
"""
import sys
import time
import random
from pathlib import Path

import pymupdf

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

# 抽样：每源取几份，控制总时长
PICK = [
    ("巨潮·中文年报", RAW / "cninfo" / "澜起科技"),
    ("深交所·中文年报", RAW / "szse" / "江波龙"),
    ("深交所·中文年报", RAW / "szse" / "雅克科技"),
    ("三星·英文IR", RAW / "samsung" / "三星电子"),
    ("海力士·英文IR", RAW / "skhynix"),
]

TEXT_TIMEOUT_PAGES = 60          # 每份最多逐页计时这么多页，其余按均值外推
EMPTY_CHARS = 30                 # 一页少于这么多字符，视作「疑似无文字层」

print("=" * 84)
print("阶段 2 预探：抽取速度 + 无文字层比例")
print("=" * 84)

tot_pages = tot_sec = 0
empty_pages = 0
checked_pages = 0
samples = []

for label, d in PICK:
    fs = sorted(p for p in d.rglob("*") if p.suffix.lower() == ".pdf") \
        if d.exists() else []
    if not fs:
        print(f"[跳过] {label}  ({d} 无 PDF)")
        continue
    f = random.Random(7).choice(fs)        # 固定种子，可复现
    t0 = time.time()
    doc = pymupdf.open(str(f))
    n = doc.page_count
    chars = 0
    n_time = min(n, TEXT_TIMEOUT_PAGES)
    t1 = time.time()
    for i in range(n_time):
        t = doc[i].get_text()
        chars += len(t)
        if len(t.strip()) < EMPTY_CHARS:
            empty_pages += 1
    t2 = time.time()
    checked_pages += n_time
    per_page = (t2 - t1) / n_time
    est = per_page * n
    tot_pages += n
    tot_sec += est
    doc.close()
    samples.append((label, f.name, n, per_page, est, chars / max(n_time, 1)))
    print(f"[{label}] {f.name[:44]}")
    print(f"    {n} 页，计时 {n_time} 页，{per_page*1000:.1f} ms/页，"
          f"平均 {chars/max(n_time,1):.0f} 字/页  → 本份约 {est:.1f}s")

print("\n" + "-" * 84)
# 全库规模
all_pdf = [p for p in RAW.rglob("*") if p.suffix.lower() == ".pdf"]
html = [p for p in RAW.rglob("*") if p.suffix.lower() in (".htm", ".html")]
n_all = 0
for p in all_pdf[:400]:
    try:
        d = pymupdf.open(str(p))
        n_all += d.page_count
        d.close()
    except Exception:
        pass

print(f"抽样 {len(samples)} 份，{checked_pages} 页中**疑似无文字层** {empty_pages} 页 "
      f"（{empty_pages/max(checked_pages,1):.1%}）")
print(f"全库 PDF {len(all_pdf)} 份 / 约 {n_all:,} 页；另有 HTML {len(html)} 份（SEC 的 10-K/10-Q 是 .htm）")
if checked_pages:
    avg_ms = (tot_sec / tot_pages) * 1000 if tot_pages else 0
    print(f"按抽样均值 {avg_ms:.1f} ms/页 推算，全库纯文本抽取约 {tot_sec:.0f}s "
          f"（{tot_sec/60:.1f} 分钟）—— **单核 CPU**；PyMuPDF 释放 GIL，多进程可近线性加速")
print("=" * 84)

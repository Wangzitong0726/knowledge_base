# -*- coding: utf-8 -*-
"""表格定位通道的验收：① 判据单元测 ② Q4 实检索 ③ 其余九题排序是否一动没动。

只跑 BM25（use_dense=False）：后台正在跑向量增量重建，两件事都是 CPU 活，
不能互相抢。锚通道与稠密通道无关，这样测不影响结论。
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import retrieve as R                                        # noqa: E402

# ── ① 判据单元测 ──────────────────────────────────────────────
print("=" * 78)
print("① 判据单元测")
print("=" * 78)

LAB = [
    ("一、营业总收入 | 2025 年半年度 1,234.00 | 2024 年半年度 999.00", "营业总收入", 1),
    ("其中：营业收入 | 2025 年半年度 1,234.00", "营业收入", 1),
    ("二、营业总成本 | 2025 年半年度 1,234.00", "营业总收入", 0),   # 别的行，不算命中
    ("其他业务收入 | 2025 年半年度 1,234.00", "营业收入", 0),       # 不以后者结尾
    # ⚠️ 正文里提到科目名**不算**命中——我们要的是那张表的那一行
    ("本公司的营业收入主要来自存储器销售，详见附注。", "营业收入", 0),
    # 行标签对上了，但这一行没有数 → 不是「那张表的那一行」
    ("一、营业总收入 |  | ", "营业总收入", 0),
]
bad = 0
for line, anchor, want in LAB:
    got = R.label_hits(line, anchor)
    ok = got == want
    bad += 1 - ok
    print("  [%s] %-58s 锚=%-6s 期望%d 得%d"
          % ("✓" if ok else "✗", line[:58], anchor, want, got))

# 口径表的核心要求：这两个锚**必须分开**，合并掉就等于抹掉这条通道的意义
print("\n  —— 两个口径锚是否被正确区分 ——")
sep = (R.label_hits(LAB[0][0], "营业总收入") == 1
       and R.label_hits(LAB[0][0], "营业收入") == 0)
print("  [%s] 「一、营业总收入」行：命中 `营业总收入`，**不**命中 `营业收入`"
      % ("✓" if sep else "✗"))
bad += 1 - sep
print("  锚提取：%s" % R.parse_anchors(
    "江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？"))
print("  锚提取（无引号无口径词）：%s ← 空表=这条通道静默"
      % R.parse_anchors("出口管制对内存市场的影响涉及哪几个方面？"))

# ── ② Q4 实检索 ──────────────────────────────────────────────
print("\n" + "=" * 78)
print("② 第 4 题（口径题）实检索 —— 开关对照")
print("=" * 78)

Q4 = "江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？"
A4 = R.parse_anchors(Q4)
print("  锚：%s" % A4)

r = R.Retriever(use_dense=False, verbose=False)
t0 = time.time()
hits_on = r.search(Q4, k=8, expand=False)
dt = time.time() - t0

t1 = time.time()
hits_off = r.search(Q4, k=8, expand=False, anchors=[])      # 强制关掉锚通道
dt_off = time.time() - t1
print("  锚通道耗时 %.2fs（含全库 LIKE + 行标签核对）；关掉时 %.2fs" % (dt, dt_off))


def show(tag, hs):
    print("\n  【%s】" % tag)
    for i, h in enumerate(hs, 1):
        row = next((x for x in h["text"].split("\n")
                    if "营业总收入" in x or "其中：营业收入" in x), "")
        print("   %d. %-12s %s  %s" % (i, h["channels"], h["company"], h["file"][:28]))
        if row:
            print("        ↳ %s" % row[:96])


show("开锚通道（缺省）", hits_on)
show("关锚通道（改前行为）", hits_off)

print("\n  口径行是否进了前 8：")
for name in ("营业总收入", "其中：营业收入"):
    on = any(name in h["text"] for h in hits_on)
    off = any(name in h["text"] for h in hits_off)
    print("    %-12s 开=%s  关=%s" % (name, "是" if on else "否", "是" if off else "否"))

# ── ③ 其余九题：排序必须一字不动 ─────────────────────────────
print("\n" + "=" * 78)
print("③ 其余九题 —— 锚通道为空的题，排序必须与改前逐位相同")
print("=" * 78)
import run_questions as RQ                                   # noqa: E402

same, diff = 0, []
for spec in RQ.Q:
    if spec["n"] == 4:
        continue
    q = spec["q"]
    if R.parse_anchors(q):
        print("  ！第 %d 题竟认出了锚：%s" % (spec["n"], R.parse_anchors(q)))
        continue
    a = [h["row"] for h in r.search(q, k=spec["k"], expand=False)]
    b = [h["row"] for h in r.search(q, k=spec["k"], expand=False, anchors=[])]
    if a == b:
        same += 1
    else:
        diff.append((spec["n"], a, b))
print("  逐位相同：%d 题；不同：%d 题" % (same, len(diff)))
for n, a, b in diff:
    print("    第 %d 题  %s" % (n, "第 %d 位起不同" % next(
        (i + 1 for i, (x, y) in enumerate(zip(a, b)) if x != y), -1)))

print("\n  单元测失败 %d 项" % bad)
sys.exit(1 if bad else 0)

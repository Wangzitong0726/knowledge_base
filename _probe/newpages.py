# -*- coding: utf-8 -*-
"""把指定的 (文件, 页码) 用**新抽取代码**跑一遍，打印正文——
用来给 `checks/t_header.py` 的 CASES 取「修后应当长什么样」的原话。

不许凭印象写 must_have：印象里的字符串写进断言，等于给自己造一个必过的判据。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from extract import pdf as PDF                                   # noqa: E402

CASES = [
    ("data/raw/szse/雅克科技/002409_2024-04-26_雅克科技：2023年年度报告（更新前）.PDF", 142),
    ("data/raw/szse/江波龙/301308_2024-08-27_江波龙：2024年半年度报告.PDF", 146),
]

for rel, pno in CASES:
    p = ROOT / rel
    print("=" * 90)
    print(p.name, "p%d" % pno, "存在" if p.exists() else "**不存在**")
    print("=" * 90)
    if not p.exists():
        continue
    recs, _info = PDF.extract_pdf(p)
    text = recs[pno - 1]["text"]
    for ln in text.split("\n"):
        if " | " in ln:
            print("   ", ln[:150])
    print()

# -*- coding: utf-8 -*-
"""把「memory bandwidth density」这个阈值在**规则库全库**里的每一处表述抓出来。

论文要用它，所以不能只凭记忆里的数字——要逐个文件、逐处列出原文与出处。
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from extract.plain import extract_xml, extract_txt   # noqa: E402

# ⚠️ 不能写成 `[^.]{0,120}` —— 那个 `.` 会把 `3.3` 从中间截断成 `3`，
# 于是「3.3 GB/s/mm²」看起来像「3 GB/s/mm²」。阈值里就带小数点，别拿句点当边界。
PAT = re.compile(r".{0,90}bandwidth density.{0,150}", re.I | re.S)

for p in sorted((ROOT / "data/raw/rules").iterdir()):
    if p.suffix.lower() == ".xml":
        try:
            blocks, info = extract_xml(p)
        except Exception as e:
            print(f"[{p.name}] 解析失败 {e}")
            continue
    elif p.suffix.lower() == ".txt":
        blocks, info = extract_txt(p)
    else:
        continue

    hits = []
    for b in blocks:
        for m in PAT.finditer(b["text"]):
            hits.append(" ".join(m.group(0).split()))
    if hits:
        print(f"\n=== {p.name}  ({len(hits)} 处)")
        seen = set()
        for h in hits:
            if h in seen:
                continue
            seen.add(h)
            print(f"   · {h}")

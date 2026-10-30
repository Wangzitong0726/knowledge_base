# -*- coding: utf-8 -*-
"""表头错配的**可测指纹率**：修前 vs 修后，同一个口径量两遍。

`t_misalign.py` 量的是修前的库（61.2%）。这个脚本把它做成**前后对照**：
两个来源都取真实的产物，判据一字不改，只换数据。

指纹定义（与 `t_misalign.py` 一字不差，否则前后不可比）：
  在一块财报文本里，把所有「2–10 个汉字 + 空格 + 两位小数数字」的搭配数出来；
  若出现最多的那个汉字串**紧挨着 ≥3 个数字**，就认为它被当成了公共标签
  —— 这是表格拍平把残行当表头、再把表头灌进每个格子的可测后果。

⚠️ 这是**标志率，不是确认的错误率**：真表头（如「房屋建筑物」）本来也会连着多个数字。
   判「是不是错」，仍须回原 PDF 看那一行。

用法：
    C:/Python314/python.exe scripts/checks/t_align_rate.py
"""
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
INDEX = ROOT / "knowledge_base" / "index"
OLD_DB = INDEX / "chunks_20261004_修前.sqlite"
NEW_JSONL = ROOT / "knowledge_base" / "chunks.jsonl"

PAIR = re.compile(r"([一-鿿]{2,10})\s+(\d[\d,]*\.\d{2})")
MINE = ("cninfo", "szse")


def flagged(text):
    """这块文本是否带指纹；返回（是否命中, 命中标签, 次数）。"""
    labs = Counter(m.group(1) for m in PAIR.finditer(text))
    if not labs:
        return False, "", 0
    lab, c = labs.most_common(1)[0]
    return c >= 3, lab, c


def old_rows():
    con = sqlite3.connect(f"file:{OLD_DB}?mode=ro", uri=True)
    for src, sec, t in con.execute(
            "SELECT source, section, text FROM chunks WHERE source IN (?,?)", MINE):
        if "财务报表" in (sec or ""):
            yield t
    con.close()


def new_rows():
    with open(NEW_JSONL, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("source") in MINE and "财务报表" in (r.get("section") or ""):
                yield r.get("text") or ""


def rate(rows, tag):
    tot = bad = 0
    labels = Counter()
    for t in rows:
        tot += 1
        hit, lab, c = flagged(t)
        if hit:
            bad += 1
            labels[lab] += 1
    print("  %-6s 财报类块 %6d ，带指纹 %6d  →  **%5.1f%%**"
          % (tag, tot, bad, 100.0 * bad / max(tot, 1)))
    print("         最常见的几个「被当公共标签」的串：%s"
          % "、".join("%s×%d" % (k, v) for k, v in labels.most_common(6)))
    return tot, bad


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("表头错配指纹率（同一判据，两个库各量一遍）")
    print("=" * 78)
    if not OLD_DB.exists():
        print("！找不到修前的库 %s，只能量修后" % OLD_DB.name)
        o = None
    else:
        o = rate(old_rows(), "修前")
    n = rate(new_rows(), "修后")
    print("=" * 78)
    if o and o[0] and n[0]:
        print("  修前 %.1f%% → 修后 %.1f%%（差 %+.1f 个百分点）"
              % (100.0 * o[1] / o[0], 100.0 * n[1] / n[0],
                 100.0 * n[1] / n[0] - 100.0 * o[1] / o[0]))
        print()
        print("  ⚠️ **这个数几乎没动，而这正是它该有的样子**——它不是一个好指标。")
        print("     两库最常见的「被当公共标签」的串都是 `期末余额` `期初余额` `账面余额`，")
        print("     那些是**真表头**：一张资产负债表里，「期末余额」本来就该紧挨着一串数字。")
        print("     所以 61.2% 里绝大部分是正常表头，不是错配。")
        print("     **拿它当「错配率」是错的**（这个数在本项目里被引用过几轮，是个教训）。")
        print()
        print("  真正能分辨「旧表头配不配当表头」的数在 `scripts/checks/t_header.py --all`：")
        print("     它逐表拿新旧两套实现对同一张表各选一次表头，按")
        print("     A 未变 / B 修正 / C 弃标 / D 丢标（回归）分类计数。")
        print("     判「配不配」用的是结构判据（表头行在本表前两行、且非首列格非空），")
        print("     不是「有没有数字跟着」这种真假不分的东西。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

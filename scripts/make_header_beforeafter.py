# -*- coding: utf-8 -*-
"""生成 `outputs/表头修复对照.md`：四个已知错配的**修前 / 修后**原文并列。

老师批改：「**先修行列与口径**」「正确页码不能证明数字归属正确」。
这份对照就是「行列修了」的证据——同一页、同一张表，
左边是修前被盖错标签的原文，右边是修后的原文。

⚠️ **「修前」来自一份备份**：`chunks_20261004_修前.sqlite`（由旧库 `VACUUM INTO` 出来，
   已核对 81,895 块、`max(row)=81894`）。不备份的话，`build_store.py --force`
   一重建，基准就变成「修后」了，差异永远对不出来。

两个来源都是**仓库里真实的那份文件**，不是重新渲染的：
  · 修前 = `chunks_20261004_修前.sqlite`（2026-10-04 建，抽取修复之前的库）
  · 修后 = 新 `knowledge_base/chunks.jsonl`（重抽取之后）

匹配按 **公司 + 页码**，不按 doc_id——因为同一份报告在巨潮与深交所各有一份副本，
doc_id 不同而正文相同；按公司+页码找，去重前后都稳。

用法：
    C:/Python314/python.exe scripts/make_header_beforeafter.py
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "knowledge_base" / "index"
# 「修前」优先取**备份**：`chunks.sqlite` 会被 `build_store.py --force` 重建覆盖，
# 覆盖之后它就变成「修后」了，再拿它当基准就永远对不出差异。
OLD_BACKUP = INDEX / "chunks_20261004_修前.sqlite"
OLD_DB = OLD_BACKUP if OLD_BACKUP.exists() else INDEX / "chunks.sqlite"
NEW_JSONL = ROOT / "knowledge_base" / "chunks.jsonl"
OUT = ROOT / "outputs" / "表头修复对照.md"

# (公司, 页码, 错配的标签, 修后该出现的行首, 一句话说明)
CASES = [
    ("江波龙", 79, "利息收入", "二、营业总成本",
     "合并利润表跨页。续页顶部有一行只剩 `利息收入` 的残行，被当成了表头，"
     "于是 `二、营业总成本` 的**两个真实数字**都挂上了「利息收入」。"),
    ("江波龙", 147, "和补贴", "2、职工福利费",
     "职工薪酬表续页。行标签 `1、工资、奖金、津贴和补贴` 在 PDF 里折了行，"
     "`和补贴` 单独成行并被当成表头，整张表每个数字都被冠上「和补贴」。"),
    ("德明利", 130, "商誉", "长期待摊费用",
     "资产负债表续页。上一页残留的 `商誉`（一行**空值模板行**，母公司没有商誉）"
     "被灌进了续页，整张表的数字都被归到「商誉」名下。"),
    ("雅克科技", 142, "报废", "4.期末余额",
     "固定资产表续页。残行 `报废` 当了表头，**整块出现 30 处**「报废 数字」。"),
]


def old_lines():
    """旧库：(公司, 页码) → 文本列表。"""
    con = sqlite3.connect(f"file:{OLD_DB}?mode=ro", uri=True)
    d = {}
    for co, ps, pe, t in con.execute(
            "SELECT company, page_start, page_end, text FROM chunks"):
        d.setdefault(co, []).append((ps, pe, t))
    con.close()
    return d


def new_lines():
    d = {}
    with open(NEW_JSONL, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            d.setdefault(r.get("company") or "", []).append(
                (r.get("page_start"), r.get("page_end"), r.get("text") or ""))
    return d


def offending(chunks, page, label, head, limit=4):
    """在覆盖该页的块里，挑出与这条错配有关的行：带 `label 数字` 的，或行首为 head 的。

    **按行内容去重**：切块允许 120 字重叠，同一份报告又在巨潮与深交所各有一份副本——
    不去重的话，同一行会被打印四遍，看着像有四张表都错了。
    """
    bad, fixed, seen_b, seen_f = [], [], set(), set()
    for ps, pe, t in chunks:
        if ps is None or not (ps <= page <= (pe or ps)):
            continue
        for ln in t.split("\n"):
            if " | " in ln and ln.split(" | ")[0].strip().startswith(head):
                if ln not in seen_f:
                    seen_f.add(ln)
                    fixed.append(ln)
            if label in ln and any(ch.isdigit() for ch in ln):
                if ln not in seen_b:
                    seen_b.add(ln)
                    bad.append(ln)
    # 截断：`pre` 是横向滚动的，截图里超出部分**看不见**——看不见就等于没写。
    # 宁可显式标出「后面还有」，也不要让人以为那行就到此为止。
    return [_cut(x) for x in bad[:limit]], [_cut(x) for x in fixed[:limit]]


def _cut(s, n=150):
    return s if len(s) <= n else s[:n] + " …（右端已截断）"


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if not OLD_DB.exists():
        raise SystemExit("旧 chunks.sqlite 不在了——「修前」已经无从取得。")

    O, N = old_lines(), new_lines()
    L = ["# 表头修复：修前 / 修后原文对照", "",
         "老师批改说「**先修行列与口径**」「**正确页码不能证明数字归属正确**」。"
         "这一页给出四处已确认的错配：**同一页、同一张表**，"
         "修前数字被盖上了别的标签，修后回到本位。", "",
         "两边的文本都取自仓库里真实的产物，不是重新排的：",
         "",
         f"- **修前** ＝ `knowledge_base/index/{OLD_DB.name}`"
         "（2026-10-04 建，表头修复之前的库；由旧库 `VACUUM INTO` 备份而来，81,895 块）",
         "- **修后** ＝ `knowledge_base/chunks.jsonl`（重抽取之后）", "",
         "---", ""]

    n_ok = 0
    for co, pg, label, head, why in CASES:
        L += [f"## {co} · 第 {pg} 页 · 被盖错成「{label}」", "", why, ""]
        for tag, store, expect_bad in (("修前", O, True), ("修后", N, False)):
            bad, fixed = offending(store.get(co, []), pg, label, head)
            L += [f"**{tag}**", ""]
            if tag == "修前":
                if bad:
                    L.append("```text")
                    L += bad
                    L.append("```")
                else:
                    L.append("（未在该页找到该标签——请人工核对）")
            else:
                if fixed:
                    L.append("```text")
                    L += fixed
                    L.append("```")
                else:
                    L.append("（未在该页找到该行——请人工核对）")
            L.append("")
        ok = bool(offending(O.get(co, []), pg, label, head)[0]) and \
            bool(offending(N.get(co, []), pg, label, head)[1])
        n_ok += 1 if ok else 0
        L += [f"> 对照结果：{'✅ 修前有错、修后归位' if ok else '⚠️ 未能自动对上，需人工核对'}", "", "---", ""]

    L += ["## 还剩什么没说清", "",
          "· **雅克科技那一页有一列我们还原不了**：第 5 列的表头，PDF 文字层里写的就是"
          "`房屋建筑物`（应为「其他设备」）——**这是该公司自己「更新前」报告里的排印错误**，"
          "它次日发了更正版。我们的抽取忠实于原文，不是新错。", "",
          "· **修后不是「每张表都有表头」**：找不到可信表头时，宁可**不猜**"
          "（江波龙第 147 页就是），输出裸数字。"
          "「没有标签」比「盖错标签」好——前者看得见，后者看不出来。", "",
          f"（本页由 `scripts/make_header_beforeafter.py` 生成；"
          f"{n_ok}/{len(CASES)} 处对照自动对上。）"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("✓ %s（%d/%d 处自动对上）" % (OUT, n_ok, len(CASES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

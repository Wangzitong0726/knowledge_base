# -*- coding: utf-8 -*-
"""表头归属检查：把「指纹率」升级成「真绑定率」。

老师批改：「先修行列与口径」「正确页码不能证明数字归属正确」。这个脚本量的就是**归属**。

两部分：

  一 · 已知实例   四个手核过的错配（都已回原 PDF 逐字对过），断言修后的文本。
  二 · 全库归因   对每份 PDF 的每张表，用**旧实现**与**新实现**各跑一遍，按
                  「旧选中的表头行，用新判据看配不配当表头」分类计数。

为什么旧实现要从 git 里取：如果检查脚本自己复刻一份旧逻辑，那证明的只是
「我复刻的和我想的一样」。旧实现的 `_header_score` 用 `git show HEAD:...` 取出来
**原样加载**，新实现直接 `import` 生产代码——两边都是真身，只有比较是新的。

判据（三条互斥、可枚举，不需要人工判读）：

  A 未变    旧表头本来就配当表头，新旧选中的是同一行
  B 修正    旧表头不配（残行/数据行），新选中了另一行可信表头
  C 弃标    旧表头不配，且本表确实没有可信表头 → 新**不猜**，宁可无表头
  D 丢标    旧表头本来就配，新却选不出来 —— **理论上不可能**，出现即回归（脚本会断言）

D 不可能，是结构上推得出来的：新旧都只在前两行里挑，新挑不出 ⟺ 前两行都不配
⟹ 旧选中的那行（也出自前两行）不配。所以 D>0 只可能意味着实现有 bug。

用法：
    C:/Python314/python.exe scripts/checks/t_header.py             # 只跑已知实例
    C:/Python314/python.exe scripts/checks/t_header.py --all -j 8  # 加跑全库归因
    C:/Python314/python.exe scripts/checks/t_header.py --show 江波龙   # 看某家公司的修正明细
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import extract.tablefmt as NEW                                   # noqa: E402
from extract import pdf as PDF                                   # noqa: E402
from run_stage2 import HANDLERS, MANIFEST, load_manifest         # noqa: E402

import pymupdf                                                   # noqa: E402


# ────────────────────────────── 一 · 已知实例 ──────────────────────────────

CASES = [
    # 江波龙 2025 半年报 p79：合并利润表跨页，续页顶部 `['利息收入','','']` 残行当了表头，
    # 于是 `二、营业总成本` 的两个数被写成「利息收入 10,081,506,072.43」。
    # 真表头在上一页（p78 末张表）：`项目 | 2025 年半年度 | 2024 年半年度`。
    # ⚠️ 断言必须走 `extract_pdf`（它跨页带着表头），**不能**单跑 `extract_page(p79)`
    #    ——那样没接上 p78 的表头，输出是对的「裸数字」，会把正确当成错误。
    ("cninfo/江波龙/301308_2025-08-23_2025年半年度报告.pdf", 79,
     "二、营业总成本 | 2025 年半年度 10,081,506,072.43 | 2024 年半年度 8,215,067,574.55",
     "利息收入 10,081,506,072.43"),
    # 德明利 2025 年报 p130：续页被冠上上一页残留的 `商誉`。而 `商誉` 在原始表里
    # 本就是一行**空值模板行**（母公司没有商誉），不该给任何人当标签。
    ("cninfo/德明利/001309_2026-02-28_2025年年度报告.pdf", 130,
     "长期待摊费用 | 期末余额 116,884,419.36 | 期初余额 136,075,883.37",
     "商誉 116,884,419.36"),
    # 雅克科技 2023 年报（更新前）p142：固定资产表，续页残行 `报废` 当了表头，
    # 整张表每个数字都被冠上「报废」（全块 30 处）。
    # 注：修后第 5 列仍读出 `房屋建筑物`——**这是雅克科技自己排印错了**：
    #     该 PDF 文字层 x=442 处写的就是 `房屋建筑物`（应为「其他设备」），
    #     该公司次日发了（更新后）版本。我们的抽取忠实于原文，不是新错。
    ("szse/雅克科技/002409_2024-04-26_雅克科技：2023年年度报告（更新前）.PDF", 142,
     "4.期末余额 | 房屋建筑物 999,810,460.34",
     "报废 261,809,201.34"),
    # 江波龙 2024 半年报 p147：职工薪酬表续页，行标签 `1、工资、奖金、津贴和补贴`
    # 在 PDF 里折了行，`和补贴` 单独成行并被当成表头，整表被冠「和补贴」。
    # 修后本页**无表头可继承**（p145–146 也没有可信表头），于是**不猜**：
    # 输出裸数字「2、职工福利费 | 111,000.00」。宁可无标签，不盖错标签。
    ("szse/江波龙/301308_2024-08-27_江波龙：2024年半年度报告.PDF", 147,
     "2、职工福利费 | 111,000.00",
     "和补贴 111,000.00"),
]


def find_raw(rel):
    """按相对路径找原文；找不到就按文件名主干在 data/raw 下搜（大小写/后缀不一律）。"""
    p = ROOT / "data" / "raw" / rel
    if p.exists():
        return p
    stem = Path(rel).stem
    for cand in (ROOT / "data" / "raw").rglob(stem + ".*"):
        return cand
    return p


def run_cases(verbose=True):
    """跑已知实例。返回 (通过数, 总数)。"""
    print("=" * 80)
    print("一 · 已知实例（回原 PDF 逐字核对过的错配）")
    print("=" * 80)
    ok = 0
    for rel, pno, must_have, must_not in CASES:
        path = find_raw(rel)
        if not path.exists():
            print("  ！找不到 %s" % path)
            continue
        # 只抽到这一页就停：表头是**从前向后**带的，两者逐字相同（见 extract_pdf 注释）
        recs, _info = PDF.extract_pdf(path, max_page=pno)
        text = recs[pno - 1]["text"]
        hit = must_have in text
        bad = must_not in text
        ok += 1 if (hit and not bad) else 0
        print("\n  [%s p%d] %s" % (("通过" if hit and not bad else "**不通过**"),
                                   pno, path.name))
        print("     应有归属：%s" % must_have)
        print("      -> %s" % ("命中" if hit else "**没命中**"))
        print("     不应出现：%s" % must_not)
        print("      -> %s" % ("**仍然出现**" if bad else "已消失"))
    print("\n  已知实例：%d/%d 通过" % (ok, len(CASES)))
    return ok, len(CASES)


# ────────────────────────────── 二 · 全库归因 ──────────────────────────────

_OLD = {}


def old_mod():
    """从 git 取出**旧实现**的 tablefmt 原样加载（不是复刻）。"""
    if "m" not in _OLD:
        src = subprocess.check_output(
            ["git", "show", "HEAD:scripts/extract/tablefmt.py"], cwd=str(ROOT))
        f = Path(tempfile.gettempdir()) / "_old_tablefmt_head.py"
        f.write_bytes(src)
        spec = importlib.util.spec_from_file_location("_old_tablefmt", f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _OLD["m"] = m
    return _OLD["m"]


def old_pick(rows):
    """旧实现选中的表头行号。**打分用旧模块自己的 `_header_score`**，
    这里只补那 4 行 argmax（旧 `flatten_table` 里写死的那段）。
    推断对不对，由 `check_old_replication()` 拿旧模块自己的输出去验。"""
    old = old_mod()
    hdr_i, best = 0, old._header_score(rows[0])
    for i in range(1, min(2, len(rows))):
        s = old._header_score(rows[i])
        if s > best:
            hdr_i, best = i, s
    return hdr_i


def check_old_replication(rows):
    """自检：按推断出的 hdr_i，旧实现应当输出 `len(rows) - hdr_i - 1` 行（无数据行时输出表头 1 行）。"""
    old = old_mod()
    n_lines = len(old.flatten_table(rows).split("\n"))
    hdr_i = old_pick(rows)
    want = len(rows) - hdr_i - 1
    return n_lines == (want if want > 0 else 1)


PROSE_CELL = 40          # 单个单元格超过这么多字，就不像表格格子，像句子


def work(rec):
    """一份文档：逐表做新旧归因。返回 (计数 Counter, 明细 list, 自检失败数)。"""
    c = Counter()
    detail = []
    repl_bad = 0
    path = Path(rec["path"])
    new = NEW
    if path.suffix.lower() != ".pdf":
        return c, detail, repl_bad          # HTML 路无跨页问题，另论
    try:
        doc = pymupdf.open(str(path))
    except Exception:
        return c, detail, repl_bad
    last_header = None
    for i in range(doc.page_count):
        page = doc[i]
        try:
            tabs = page.find_tables(strategy="lines").tables
        except Exception:
            continue
        for t in tabs:
            try:
                rows = t.extract()
            except Exception:
                continue
            rows = new.clean_rows(rows)
            if not rows or not new.table_ok(rows)[0]:
                continue
            if not check_old_replication(rows):
                repl_bad += 1

            width = max(len(r) for r in rows)
            n = new.pick_header(rows)
            # **继承实际生效**的表数——这才是这次修复直接救回来的
            inh = PDF.inherit_for(t.bbox[1], page.rect.height, width, last_header)
            if inh is not None and n is None:
                c["继承生效"] += 1
            cells = [x for r in rows for x in r if x]
            if cells and sum(len(x) for x in cells) / len(cells) > PROSE_CELL:
                c["幻影表（格子里是成句文字）"] += 1

            o = old_pick(rows)
            old_credible = new._header_score(rows[o]) is not None
            if old_credible and n == o:
                c["A 未变"] += 1
            elif old_credible and n is None:
                c["D 丢标（回归！）"] += 1
            elif old_credible:
                c["E 换行（需人看）"] += 1
            elif n is not None:
                c["B 修正"] += 1
            else:
                c["C 弃标"] += 1
            if not old_credible and len(detail) < 4000:
                detail.append({
                    "doc": "%s/%s" % (rec.get("company", "?"), path.name),
                    "page": i + 1,
                    "prose": bool(cells and sum(len(x) for x in cells) / len(cells) > PROSE_CELL),
                    "old_hdr": [x for x in rows[o] if x],
                    "new_hdr": [x for x in rows[n] if x] if n is not None else None,
                })
            # 与 extract_page 同一套：本表若给出了可信表头，就更新携带的表头
            flat, carried = new.flatten_table(rows, inherited=inh)
            if carried:
                last_header = carried
    doc.close()
    return c, detail, repl_bad


def run_all(jobs):
    recs = [r for r in load_manifest(set()) if Path(r["path"]).suffix.lower() in HANDLERS]
    print("\n" + "=" * 80)
    print("二 · 全库归因（%d 份文档，旧实现取自 git HEAD）" % len(recs))
    print("=" * 80)
    tot = Counter()
    detail = []
    repl_bad = 0
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        for k, (c, d, rb) in enumerate(ex.map(work, recs, chunksize=2), 1):
            tot += c
            repl_bad += rb
            detail.extend(d)
            if k % 40 == 0:
                print("  [%d/%d] ..." % (k, len(recs)))
    CATS = ("A 未变", "B 修正", "C 弃标", "E 换行（需人看）", "D 丢标（回归！）")
    n = sum(tot[k] for k in CATS)          # 只数 A–E——「继承生效」「幻影表」是另算的附加计数
    print("\n  共 %d 张表（通过 table_ok 的）：" % n)
    for k in CATS:
        print("    %-16s %7d  %6.1f%%" % (k, tot[k], 100 * tot[k] / max(n, 1)))
    print("\n  旧表头被判定「不配当表头」的合计：%d（B+C，占 %.1f%%）"
          % (tot["B 修正"] + tot["C 弃标"],
             100 * (tot["B 修正"] + tot["C 弃标"]) / max(n, 1)))
    print("    其中新找到了可信表头：%d（B，归属被纠正且有标签）" % tot["B 修正"])
    print("    其中新选择不猜　　：%d（C，宁可无表头）" % tot["C 弃标"])
    print("\n  跨页表头继承**实际生效**的表数：%d" % tot["继承生效"])
    print("  table_ok 放进来的幻影表（格子里是成句文字）：%d（占 %.1f%%）"
          % (tot["幻影表（格子里是成句文字）"], 100 * tot["幻影表（格子里是成句文字）"] / max(n, 1)))
    print("    ⚠️ 这一批与本次表头修改无关：它们在修改前后都没有可信表头，")
    print("       因为**它们本来就不是表**——是 `table_ok` 把成段文字当表收了进来。")
    print("  旧实现推断自检失败：%d（应为 0，非 0 说明上面的旧/新比较不可信）" % repl_bad)
    if tot["D 丢标（回归！）"]:
        print("\n  ！出现 D —— 旧表头本来可信却被新实现丢掉，这是回归，必须查。")
    return tot, detail, repl_bad


def show_detail(detail, kw, limit=12):
    hits = [d for d in detail if kw in d["doc"]]
    print("\n" + "=" * 80)
    print("修正明细 · 含「%s」的 %d 张表" % (kw, len(hits)))
    print("=" * 80)
    for d in hits[:limit]:
        print("\n  %s  p%d" % (d["doc"], d["page"]))
        print("     旧表头：%s" % d["old_hdr"])
        print("     新表头：%s" % (d["new_hdr"] if d["new_hdr"] else "（不猜，本表无表头）"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="加跑全库归因")
    ap.add_argument("-j", "--jobs", type=int, default=8)
    ap.add_argument("--show", default="", help="打印含该关键词的文档的修正明细")
    ap.add_argument("--dump", default="", help="把修正明细存成 jsonl")
    args = ap.parse_args()

    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    run_cases()
    if not args.all and not args.show:
        return 0
    tot, detail, repl_bad = run_all(args.jobs)
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as f:
            for d in detail:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print("\n  明细已存 %s（%d 条）" % (args.dump, len(detail)))
    if args.show:
        show_detail(detail, args.show)
    return 0 if not tot["D 丢标（回归！）"] and repl_bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

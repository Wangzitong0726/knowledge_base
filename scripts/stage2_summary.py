# -*- coding: utf-8 -*-
"""
阶段 2 · 汇总（从**磁盘上已抽出的文件**重建，不依赖上一次运行的记忆）

    python scripts/stage2_summary.py

为什么要单独有这么一步：`run_stage2.py` 的报告只统计**本次**跑了哪些，
可抽取是分批跑完的（中断后续跑、分来源试跑），那样报出来的数字就只是最后一批的，
**看着像全库其实不是**——这种「不报错的错」比跑失败更危险。
这里改成以 `data/manifest.jsonl` 为**应有清单**，逐个去找产物、读它尾部的 `__meta__` 行，
**缺谁、谁没写完、谁的行数与页数对不上**，都当面列出来。

同时做两件校验：
  ① 每份产物末行必须是 `__meta__`（写到一半被杀掉的会没有 → 判为不完整）
  ② 正文字数必须等于 `__meta__` 里记的页数（行数对不上说明写到一半）
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from run_stage2 import HANDLERS, OUTDIR, INDEX, REPORT, _safe   # noqa: E402

MANIFEST = ROOT / "data" / "manifest.jsonl"


def main():
    recs = []
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if Path(r.get("path", "")).suffix.lower() in HANDLERS:
                recs.append(r)

    rows, missing, broken, mismatch = [], [], [], []
    for r in recs:
        p = Path(r["path"])
        out = OUTDIR / _safe(str(r.get("source") or "_")) / _safe(str(r.get("company") or "_")) \
            / (_safe(p.stem) + ".jsonl")
        base = {"doc_id": f"{r.get('source')}/{r.get('company')}/{p.stem}",
                "source": r.get("source"), "company": r.get("company"),
                "title": r.get("title"), "date": r.get("date"), "url": r.get("url"),
                "file": p.name, "out": str(out), "pages": 0, "chars": 0,
                "tables": 0, "tables_dropped": 0, "unit": "", "error": ""}
        if not out.exists():
            base["error"] = "产物缺失"
            missing.append(base)
            rows.append(base)
            continue
        try:
            with open(out, encoding="utf-8") as f:
                lines = [ln for ln in f if ln.strip()]
            meta = json.loads(lines[-1])
        except Exception as e:
            base["error"] = f"读不出 {type(e).__name__}"
            broken.append(base)
            rows.append(base)
            continue
        if not meta.get("__meta__"):
            base["error"] = "尾部无 __meta__（疑写到一半）"
            broken.append(base)
            rows.append(base)
            continue
        n_body = len(lines) - 1
        base.update({"pages": meta.get("pages", 0), "chars": meta.get("chars", 0),
                     "tables": meta.get("tables", 0),
                     "tables_dropped": meta.get("tables_dropped", 0),
                     "unit": meta.get("unit", "")})
        if n_body != meta.get("pages", 0):
            base["error"] = f"行数 {n_body} ≠ 页数 {meta.get('pages')}"
            mismatch.append(base)
        rows.append(base)

    ok = [r for r in rows if not r["error"]]
    bad = [r for r in rows if r["error"]]

    by_src = {}
    for r in ok:
        s = by_src.setdefault(r["source"] or "?", {"n": 0, "pages": 0, "chars": 0,
                                                   "tables": 0, "dropped": 0})
        for k_src, k_dst in (("pages", "pages"), ("chars", "chars"),
                             ("tables", "tables"), ("tables_dropped", "dropped")):
            s[k_dst] += r.get(k_src, 0)
        s["n"] += 1

    tot = {k: sum(v[k] for v in by_src.values()) for k in ("n", "pages", "chars", "tables", "dropped")}

    L = ["# 阶段 2 抽取报告（全库，由 `stage2_summary.py` 从磁盘重建）\n",
         f"- 应有 **{len(recs)}** 份（取自 `data/manifest.jsonl`），成功 **{len(ok)}** 份，"
         f"异常 **{len(bad)}** 份",
         f"- 产物目录 `{OUTDIR}`；索引 `{INDEX}`\n",
         "## 分来源\n",
         "| 来源 | 份数 | 页/块 | 字数 | 表数 | 丢弃表 | 字/页 |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for s, v in sorted(by_src.items(), key=lambda kv: -kv[1]["chars"]):
        L.append(f"| {s} | {v['n']} | {v['pages']:,} | {v['chars']:,} | {v['tables']:,} "
                 f"| {v['dropped']:,} | {v['chars']/max(v['pages'],1):.0f} |")
    L.append(f"| **合计** | **{tot['n']}** | **{tot['pages']:,}** | **{tot['chars']:,}** "
             f"| **{tot['tables']:,}** | **{tot['dropped']:,}** | "
             f"{tot['chars']/max(tot['pages'],1):.0f} |\n")

    L.append("## 校验\n")
    L.append(f"- 产物缺失：**{len(missing)}** 份")
    L.append(f"- 文件损坏 / 写到一半：**{len(broken)}** 份")
    L.append(f"- 行数与页数不符：**{len(mismatch)}** 份")
    L.append("")
    if bad:
        L.append("| 来源 | 公司 | 文件 | 问题 |")
        L.append("|---|---|---|---|")
        for r in bad:
            L.append(f"| {r['source']} | {r['company']} | {r['file']} | {r['error']} |")
        L.append("")

    thin = sorted(ok, key=lambda r: r["chars"])[:8]
    L.append("## 字数最少的 8 份（人工看一眼是否版式漏抽）\n")
    for r in thin:
        L.append(f"- `{r['company']}/{r['file']}` — {r['pages']} 页 / {r['chars']:,} 字 "
                 f"（{r['chars']/max(r['pages'],1):.0f} 字/页）")
    L.append("")

    INDEX.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                     encoding="utf-8")
    REPORT.write_text("\n".join(L), encoding="utf-8")

    print("=" * 80)
    print(f"应有 {len(recs)} 份 → 成功 {len(ok)}，异常 {len(bad)}"
          f"（缺失 {len(missing)} / 损坏 {len(broken)} / 行数不符 {len(mismatch)}）")
    print(f"合计 {tot['pages']:,} 页/块，{tot['chars']:,} 字，{tot['tables']:,} 张表")
    for s, v in sorted(by_src.items(), key=lambda kv: -kv[1]["chars"]):
        print(f"  {s:<9} {v['n']:>3} 份  {v['pages']:>7,} 页  {v['chars']:>10,} 字  "
              f"{v['tables']:>6,} 表")
    print(f"报告 → {REPORT}")
    print("=" * 80)


if __name__ == "__main__":
    main()

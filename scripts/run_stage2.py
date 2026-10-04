# -*- coding: utf-8 -*-
"""
阶段 2 · 抽取编排（PDF / HTML / TXT / XML 全库）

    python scripts/run_stage2.py                # 全部（已抽好的会跳过）
    python scripts/run_stage2.py --only cninfo  # 只跑某个源（逗号分隔）
    python scripts/run_stage2.py --limit 5      # 先试跑几份
    python scripts/run_stage2.py --force        # 重抽（忽略已有产物）
    python scripts/run_stage2.py -j 8           # 并发进程数

产出：
    data/extracted/<来源>/<公司>/<文件名>.jsonl   每份文档一个，一行一个「页/块」
    data/stage2_index.jsonl                     文档级汇总（一份一行）
    data/stage2_报告.md                          本次运行汇总 + 失败明细 + 异常样本

并行粒度取**文档**而不是页：一份文档开一个进程，写自己的文件、只回一个小 dict。
这样大块文本不进 IPC（省内存、也省序列化），进度也能按份数报出来。

⚠️ Windows 用 spawn 起子进程，会重新 import 本模块 —— 所以
① 所有并行函数必须是**模块级**的（不能是闭包）；② 入口必须放在 `if __name__ == "__main__"` 里。
"""
import argparse
import json
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MANIFEST = ROOT / "data" / "manifest.jsonl"
OUTDIR = ROOT / "data" / "extracted"
INDEX = ROOT / "data" / "stage2_index.jsonl"
REPORT = ROOT / "data" / "stage2_报告.md"

# 扩展名 → 抽取器名（真正的 import 放在子进程里做，主进程不必加载 pymupdf/lxml）
HANDLERS = {".pdf": "pdf", ".htm": "html", ".html": "html",
            ".txt": "plain_txt", ".xml": "plain_xml"}

# 保险：文件名的非法字符（公司名里有空格没问题，但斜杠之类要挡）
_BAD = '<>:"/\\|?*'


def _safe(s):
    return "".join("_" if ch in _BAD else ch for ch in s).strip() or "_"


def _skip_note(prev):
    """已有的产物能不能直接用：看它的尾部汇总行是否完整（写到一半断电就作废）。"""
    try:
        with open(prev, "rb") as f:
            f.seek(max(0, prev.stat().st_size - 4096))
            tail = f.read().decode("utf-8", "ignore")
        return "__meta__" in tail
    except Exception:
        return False


def work(rec):
    """子进程：抽一份文档，写自己的 jsonl，回一个小 dict。"""
    t0 = time.time()
    p = Path(rec["path"])
    ext = p.suffix.lower()
    kind = HANDLERS.get(ext)
    base = {"doc_id": "", "source": rec.get("source"), "company": rec.get("company"),
            "title": rec.get("title"), "date": rec.get("date"), "url": rec.get("url"),
            "file": p.name, "unit": "page", "pages": 0, "chars": 0, "tables": 0,
            "tables_dropped": 0, "error": "", "out": "", "secs": 0.0}

    if kind is None:
        base["error"] = f"不支持的扩展名 {ext}"
        return base
    if not p.exists():
        base["error"] = "文件不存在"
        return base

    doc_id = f"{rec.get('source')}/{rec.get('company')}/{p.stem}"
    base["doc_id"] = doc_id
    out = OUTDIR / _safe(str(rec.get("source") or "_")) / _safe(str(rec.get("company") or "_")) \
        / (_safe(p.stem) + ".jsonl")
    base["out"] = str(out)

    try:
        if kind == "pdf":
            from extract.pdf import extract_pdf
            pages, info = extract_pdf(p)
        elif kind == "html":
            from extract.html import extract_html
            pages, info = extract_html(p)
        elif kind == "plain_txt":
            from extract.plain import extract_txt
            pages, info = extract_txt(p)
        else:
            from extract.plain import extract_xml
            pages, info = extract_xml(p)
    except Exception as e:
        base["error"] = f"{type(e).__name__}: {e}"
        base["trace"] = traceback.format_exc()[-1200:]
        return base

    # 元数据挂在每行上：阶段 3 切块时一个文件就能自洽，不必回头 join 索引
    meta = {"doc_id": doc_id, "source": rec.get("source"), "company": rec.get("company"),
            "title": rec.get("title"), "date": rec.get("date"), "url": rec.get("url"),
            "file": p.name, "unit": info.get("unit", "page"),
            "strategy": info.get("strategy", "")}
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(out, "w", encoding="utf-8") as f:
            for pg in pages:
                row = dict(pg)
                row.update(meta)
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.write(json.dumps({**meta, "__meta__": True,
                                "pages": info.get("pages"), "chars": info.get("chars"),
                                "tables": info.get("tables"),
                                "tables_dropped": info.get("tables_dropped")},
                               ensure_ascii=False) + "\n")
    except Exception as e:
        base["error"] = f"写盘失败 {type(e).__name__}: {e}"
        return base

    base.update({
        "unit": info.get("unit", "page"),
        "pages": info.get("pages", 0),
        "chars": info.get("chars", 0),
        "tables": info.get("tables", 0),
        "tables_dropped": info.get("tables_dropped", 0),
        "strategy": info.get("strategy", ""),
        "drop_reasons": list(Counter(
            r for pg in pages for r in (pg.get("drop_reasons") or [])).items())[:8],
    })
    base["secs"] = round(time.time() - t0, 2)
    return base


def load_manifest(only):
    recs = []
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if Path(r.get("path", "")).suffix.lower() not in HANDLERS:
                continue
            if only and r.get("source") not in only:
                continue
            recs.append(r)
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只跑这些源，逗号分隔")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 份（试跑用）")
    ap.add_argument("--force", action="store_true", help="重抽，忽略已有产物")
    ap.add_argument("-j", "--jobs", type=int, default=0, help="并发进程数（默认 CPU-1）")
    args = ap.parse_args()

    only = {s.strip() for s in args.only.split(",") if s.strip()}
    recs = load_manifest(only)
    if not recs:
        raise SystemExit("清单里没有可抽的文档")

    todo, skipped = [], 0
    for r in recs:
        p = Path(r["path"])
        prev = OUTDIR / _safe(str(r.get("source") or "_")) / _safe(str(r.get("company") or "_")) \
            / (_safe(p.stem) + ".jsonl")
        if not args.force and prev.exists() and _skip_note(prev):
            skipped += 1
            continue
        todo.append(r)
    if args.limit:
        todo = todo[:args.limit]

    jobs = args.jobs or max(1, (__import__("os").cpu_count() or 4) - 1)
    print("=" * 84)
    print(f"阶段 2 · 抽取：待抽 {len(todo)} 份，已完成跳过 {skipped} 份，并发 {jobs}")
    print("=" * 84)
    if not todo:
        print("没有要抽的。")
        return

    results, t0, done = [], time.time(), 0
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        futs = {ex.submit(work, r): r for r in todo}
        for fu in as_completed(futs):
            r = futs[fu]
            try:
                res = fu.result()
            except Exception as e:
                res = {"doc_id": f"{r.get('source')}/{r.get('company')}",
                       "source": r.get("source"), "company": r.get("company"),
                       "file": Path(r["path"]).name, "pages": 0, "chars": 0, "tables": 0,
                       "tables_dropped": 0, "out": "", "secs": 0,
                       "error": f"子进程异常 {type(e).__name__}: {e}"}
            results.append(res)
            done += 1
            flag = "✗" if res.get("error") else "·"
            print(f"[{done:>3}/{len(todo)}] {flag} {res.get('file','?')[:46]:<46} "
                  f"{res.get('pages',0):>5} 页 {res.get('chars',0):>9,} 字 "
                  f"{res.get('tables',0):>4} 表 {res.get('secs',0):>6.1f}s"
                  + (f"  ⚠ {res['error'][:60]}" if res.get("error") else ""))

    el = time.time() - t0
    results.sort(key=lambda x: (x.get("source") or "", x.get("company") or "", x.get("file") or ""))

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    write_report(results, el, skipped, jobs)
    ok = [r for r in results if not r.get("error")]
    print("-" * 84)
    print(f"完成 {len(ok)}/{len(results)}，用时 {el:.1f}s（{el/max(len(results),1):.1f}s/份）")
    print(f"合计 {sum(r.get('pages',0) for r in ok):,} 页/块，"
          f"{sum(r.get('chars',0) for r in ok):,} 字，{sum(r.get('tables',0) for r in ok):,} 张表")
    print(f"索引 {INDEX}；报告 {REPORT}")


def write_report(results, el, skipped, jobs):
    ok = [r for r in results if not r.get("error")]
    bad = [r for r in results if r.get("error")]
    by_src = {}
    for r in ok:
        s = by_src.setdefault(r.get("source") or "?", {"n": 0, "pages": 0, "chars": 0, "tables": 0})
        s["n"] += 1
        s["pages"] += r.get("pages", 0)
        s["chars"] += r.get("chars", 0)
        s["tables"] += r.get("tables", 0)

    drops = Counter()
    for r in ok:
        for reason, cnt in (r.get("drop_reasons") or []):
            drops[reason.split()[0] if reason else "?"] += cnt

    L = []
    L.append("# 阶段 2 抽取报告\n")
    L.append(f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    L.append(f"- 本次抽取 **{len(ok)}** 份（跳过已完成 {skipped} 份），并发 {jobs}，"
             f"用时 **{el:.1f}s**（{el/max(len(results),1):.1f}s/份）")
    L.append(f"- 失败 **{len(bad)}** 份\n")
    L.append("## 分来源\n")
    L.append("| 来源 | 份数 | 页/块 | 字数 | 表数 | 字/页 |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for s, v in sorted(by_src.items(), key=lambda kv: -kv[1]["chars"]):
        L.append(f"| {s} | {v['n']} | {v['pages']:,} | {v['chars']:,} | {v['tables']:,} "
                 f"| {v['chars']/max(v['pages'],1):.0f} |")
    L.append(f"\n**合计**：{sum(v['pages'] for v in by_src.values()):,} 页/块，"
             f"{sum(v['chars'] for v in by_src.values()):,} 字，"
             f"{sum(v['tables'] for v in by_src.values()):,} 张表\n")

    L.append("## 表格被丢弃的原因（前 8）\n")
    L.append("| 原因 | 次数 |")
    L.append("|---|---:|")
    for k, v in drops.most_common(8):
        L.append(f"| {k} | {v} |")
    L.append("")

    empty = [r for r in ok if r.get("chars", 0) == 0]
    thin = sorted(ok, key=lambda r: r.get("chars", 0))[:5]
    L.append("## 异常样本\n")
    L.append(f"- 抽出 0 字的文档：**{len(empty)}** 份"
             + ("：" + "、".join(r["file"] for r in empty[:10]) if empty else ""))
    L.append("- 字数最少的 5 份（应人工看一眼是不是版式导致的漏抽）：")
    for r in thin:
        L.append(f"  - {r.get('company')}/{r['file']} — {r.get('pages',0)} 页 / {r.get('chars',0):,} 字")
    L.append("")

    if bad:
        L.append("## 失败明细\n")
        L.append("| 来源 | 公司 | 文件 | 错误 |")
        L.append("|---|---|---|---|")
        for r in bad:
            L.append(f"| {r.get('source')} | {r.get('company')} | {r.get('file')} "
                     f"| `{(r.get('error') or '')[:120]}` |")
        L.append("")
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()

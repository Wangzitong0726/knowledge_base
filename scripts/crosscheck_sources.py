# -*- coding: utf-8 -*-
"""
交叉印证：**深交所官网** vs **巨潮资讯网**，同一份年报是不是同一个东西

为什么必须做：作业要求「从交易所网站下载年报全文」，而我们为沪市用的是巨潮
（上交所官网取数接口未文档化，见 szse.py 说明）。那么至少要证明一件事——
**两个渠道拿到的是同一份文件**，否则「口径不同」就不只是来源差异，而是内容差异。

判据（从弱到强，全报出来，不靠单一项下结论）：
  1. 字节数与 sha256 —— 最强，但不同渠道重排版会导致不同，**不等不代表内容不同**
  2. 页数           —— PDF 结构量，截断/缺页立刻暴露
  3. 正文抽取字符数 —— 内容量；配合页数能区分「换皮」与「换内容」
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fetch.cninfo import parse_report          # noqa: E402

try:
    import pymupdf                     # 比 pypdf 快约 10 倍；逐页抽文本用它才跑得动
except ImportError:                    # pragma: no cover
    pymupdf = None


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def probe(p, max_pages=400):
    """返回 (页数, 正文字符数)。失败返回 (错误标记, None)。

    只统计字符数（不落盘文本），页数上限 400 防个别超长文件拖慢整体。
    """
    if pymupdf is None:
        return None, None
    try:
        d = pymupdf.open(str(p))
        n = d.page_count
        txt = "".join(d[i].get_text() for i in range(min(n, max_pages)))
        d.close()
        return n, len(txt)
    except Exception as e:
        return f"ERR:{type(e).__name__}", None


def index(dirpath):
    """{ (kind, year): [path, ...] } —— 同名（更正/更新前后）会落在同一键下。

    ⚠️ Windows 上 `rglob("*.pdf")` 与 `rglob("*.PDF")` 匹配**同一批文件**（大小写不敏感），
    两个 glob 相加会让每份文件出现两次，把配对总数直接翻倍。
    所以按 suffix.lower() 自己筛，并用 dict 去重。实测踩过（88 对 vs 真实 44 对）。
    """
    out = {}
    files = {p: None for p in Path(dirpath).rglob("*")
             if p.is_file() and p.suffix.lower() == ".pdf"}
    for p in sorted(files):
        t = p.stem
        t = re.sub(r"^\d{6}_\d{4}-\d{2}-\d{2}_", "", t)
        kind, year = parse_report(t)
        if kind is None:
            continue
        out.setdefault((kind, year), []).append(p)
    return out


def vkey(name):
    """版本标记。同一份年报可能有两个版本（更新前/后、更正前/后），
    必须**按版本对齐**再比，否则会拿「更新前」去比「更新后」，
    得出「两个渠道不一致」的假结论。实测踩过：4 处『异』全是这么来的。"""
    m = re.search(r"（(更新前|更新后|更正前|更正后)）", name)
    return m.group(1) if m else "原件"


print("=" * 96)
print("深交所官网  vs  巨潮资讯网  ·  同一份定期报告比对")
print("=" * 96)

rows, same_bytes, same_pages = [], 0, 0
for comp in sorted(p.name for p in (ROOT / "data/raw/szse").iterdir() if p.is_dir()):
    A = index(ROOT / "data/raw/szse" / comp)
    B = index(ROOT / "data/raw/cninfo" / comp)
    for key in sorted(A, key=lambda k: (k[1] or 0, k[0])):
        for a in A[key]:
            # 先在巨潮里找**同版本**的；找不到再退回同 (类型,年度) 的任一份
            cands = B.get(key, [])
            same_v = [p for p in cands if vkey(p.stem) == vkey(a.stem)]
            cands = same_v or cands
            if not cands:
                rows.append((comp, key, a, None, None, None, None))
                continue
            b = cands[0]
            sa, sb = sha(a), sha(b)
            pa, pb = probe(a), probe(b)
            eq_b = sa == sb
            eq_p = pa[0] == pb[0]
            same_bytes += eq_b
            same_pages += eq_p
            rows.append((comp, key, a, b, (eq_b, eq_p, pa, pb), sa, sb))

print(f"\n{'公司':<10}{'类型/年':<14}{'交易所官网':>22}{'巨潮':>22}  字节  页数")
print("-" * 96)
n_pair = 0
for comp, key, a, b, cmpres, sa, sb in rows:
    _v = vkey(a.stem)
    lbl = f"{key[0]}{key[1] or ''}" + (f"·{_v}" if _v != "原件" else "")
    if b is None:
        print(f"{comp:<10}{lbl:<14}{a.stat().st_size/1e6:>20.2f}MB{'—（巨潮无此份）':>24}")
        continue
    n_pair += 1
    eq_b, eq_p, pa, pb = cmpres
    print(f"{comp:<10}{lbl:<14}{a.stat().st_size/1e6:>20.2f}MB{b.stat().st_size/1e6:>20.2f}MB"
          f"  {'同' if eq_b else '异'}  {pa[0]} vs {pb[0]} {'✓' if eq_p else '✗'}")

print("-" * 96)
print(f"配到 {n_pair} 对：字节完全相同 {same_bytes} 对（{same_bytes/max(n_pair,1):.0%}），"
      f"页数相同 {same_pages} 对（{same_pages/max(n_pair,1):.0%}）")

# 逐份详表写盘
out = ["# 交叉印证：深交所官网 vs 巨潮资讯网", "",
       f"配对 {n_pair} 对。字节完全相同 {same_bytes} 对，页数相同 {same_pages} 对。", "",
       "| 公司 | 报告 | 官网 sha256 | 巨潮 sha256 | 字节同 | 官网页 | 巨潮页 | 官网字数 | 巨潮字数 |",
       "|---|---|---|---|---|---|---|---|---|"]
for comp, key, a, b, cmpres, sa, sb in rows:
    if b is None:
        _v = vkey(a.stem)
        out.append(f"| {comp} | {key[0]}{key[1] or ''}·{_v} | {sa[:16]} | — | — | — | — | — | — |")
        continue
    eq_b, eq_p, pa, pb = cmpres
    _v = vkey(a.stem)
    out.append(f"| {comp} | {key[0]}{key[1] or ''}·{_v} | {sa[:16]} | {sb[:16]} | "
               f"{'✓' if eq_b else '✗'} | {pa[0]} | {pb[0]} | {pa[1]} | {pb[1]} |")
(ROOT / "data" / "crosscheck_来源比对.md").write_text("\n".join(out), encoding="utf-8")
print(f"\n明细：{ROOT/'data'/'crosscheck_来源比对.md'}")

# -*- coding: utf-8 -*-
"""
库 A · 三星电子 业务报告 / 半年报（Samsung IR）

实测（`_probe/verify_endpoints.md`）：
  - 年报列表页 `https://www.samsung.com/global/ir/reports-disclosures/business-report/` 可取（173KB）
  - 页内 PDF 链接是**协议相对**的 `//images.samsung.com/...`，
    只匹配 `https?://` 会一条都抓不到（我第一遍就是这么错的）
  - CDN 路径有两代：`/assets/global/ir/docs/` 与 `/p5/global/ir/docs/`，都要收
  - 文件命名不统一：`2019_Business_Report.pdf` / `2022-4q-Business-Report.pdf` /
    `2026_Half_Interim_Report.pdf`，所以用宽松规则筛，别写死格式
"""
import re
from pathlib import Path

from .common import Fetcher, FetchError

COMPANY = "三星电子"
LIST_URLS = [
    ("business-report", "https://www.samsung.com/global/ir/reports-disclosures/business-report/"),
]

# ⚠️ 口径边界（实测发现，论文里也要写明）：
#   三星英文站**2023 年起不再发布年度 Business Report**。
#   页面上 62 个 PDF 里，年报只到 2022（2020_Business_Report / 2022-4q-Business-Report），
#   2023 之后英文只有 **Half Interim Report（半年报）** 与 **各季 Interim Report**。
#   故取「半年报 + 4Q 年终季报」两类，作为该公司可得的最全英文披露。
#   1Q/2Q/3Q 季报不收 —— 它们与半年报大量重叠，收了会让同一年的经营数据在索引里出现三份。
KEEP_RE = re.compile(r"(Business[_\-]?Report|Half[_\-]?(Year|Interim)[_\-]?Report|"
                     r"4Q[_\-]?Interim[_\-]?Report|Annual[_\-]?Report)", re.I)
DROP_RE = re.compile(r"[123]Q[_\-]?Interim|quarter\d", re.I)


def list_pdfs(f):
    """从列表页抽出所有 PDF 直链（含协议相对的）。"""
    seen = {}
    for label, url in LIST_URLS:
        try:
            html = f.get_text(url, timeout=60)
        except FetchError as e:
            f.fail("samsung", f"列表页 {label}", e)
            continue
        # 关键：同时匹配 https:// 与 // 开头（协议相对）
        raw = re.findall(r'(?:https?:)?//[^"\'\\\s]+?\.pdf', html, re.I)
        for u in raw:
            if u.startswith("//"):
                u = "https:" + u
            u = u.replace("&amp;", "&")
            name = u.rsplit("/", 1)[-1]
            if DROP_RE.search(name):
                continue
            if not KEEP_RE.search(name):
                continue
            seen[u] = name
    return sorted(seen.items(), key=lambda kv: kv[1])


def year_of(name):
    m = re.search(r"(20\d{2})", name)
    return int(m.group(1)) if m else 0


def run(f, outdir, min_year=2024):
    outdir = Path(outdir)
    print(f"\n=== 库 A · 三星电子 IR ===")
    pdfs = list_pdfs(f)
    print(f"  列到 {len(pdfs)} 份年报/半年报（已排除季报）")

    got = []
    for url, name in pdfs:
        y = year_of(name)
        if y and y < min_year:
            continue
        try:
            f.download(url, outdir / COMPANY / name, source="samsung",
                       company=COMPANY, title=name, date=str(y) if y else "")
            got.append(name)
        except FetchError as e:
            f.fail("samsung", name, e)
    print(f"      → 取到 {len(got)} 份（{min_year} 年起）")
    return got

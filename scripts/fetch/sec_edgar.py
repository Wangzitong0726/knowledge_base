# -*- coding: utf-8 -*-
"""
库 A · 美光科技 10-K / 10-Q（SEC EDGAR）

实测（`_probe/verify_endpoints.md`）：
  - `https://www.sec.gov/files/company_tickers.json` 用浏览器 UA 会 **403**
  - `https://data.sec.gov/submissions/CIK##########.json` 用**声明式 UA**（SEC_UA）正常
  - CIK 已确认：**723125 = MICRON TECHNOLOGY INC**

SEC 要求 UA 里声明使用者身份，这是公平使用政策，不是反爬——
所以我们如实声明，不伪装浏览器去绕。同理，请求要限速（SEC 建议 ≤10 次/秒）。
"""
import json
import time
from pathlib import Path

from .common import Fetcher, FetchError, sec_ua

CIK = 723125
COMPANY = "美光 Micron"
SUBMISSIONS = f"https://data.sec.gov/submissions/CIK{CIK:010d}.json"
ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"

WANT_FORMS = ("10-K", "10-Q")


def list_filings(f, limit_per_form=6):
    """列出发行人最近的 10-K/10-Q。返回 [{form, date, url, accession}]。"""
    raw, _ = f.get(SUBMISSIONS, ua=sec_ua(), headers={"Accept": "application/json"})
    js = json.loads(raw.decode("utf-8"))
    r = js["filings"]["recent"]
    out = []
    for form, date, acc, doc in zip(r["form"], r["filingDate"],
                                     r["accessionNumber"], r["primaryDocument"]):
        if form not in WANT_FORMS or not doc:
            continue
        out.append({
            "form": form, "date": date, "accession": acc,
            "url": ARCHIVE.format(cik=CIK, acc=acc.replace("-", ""), doc=doc),
        })
    # 每种表取最近 N 份
    keep = []
    for form in WANT_FORMS:
        keep += [x for x in out if x["form"] == form][:limit_per_form]
    return sorted(keep, key=lambda x: x["date"], reverse=True)


def run(f, outdir, limit_per_form=6):
    outdir = Path(outdir)
    print(f"\n=== 库 A · SEC EDGAR · {COMPANY} ===")
    try:
        filings = list_filings(f, limit_per_form)
    except (FetchError, json.JSONDecodeError, KeyError) as e:
        f.fail("sec", f"{COMPANY} 申报清单", e)
        return []
    print(f"  列到 {len(filings)} 份 10-K/10-Q")

    got = []
    for x in filings:
        fn = f"{x['form'].replace('-', '')}_{x['date']}_{x['accession']}.htm"
        try:
            f.download(x["url"], outdir / COMPANY / fn, source="sec",
                       company=COMPANY, title=f"{x['form']} {x['date']}",
                       date=x["date"], ua=sec_ua())
            got.append(x)
        except FetchError as e:
            f.fail("sec", f"{x['form']} {x['date']}", e)
    print(f"      → 取到 {len(got)} 份")
    return got

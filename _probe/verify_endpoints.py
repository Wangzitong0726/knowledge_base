# -*- coding: utf-8 -*-
"""
阶段 1 动工前：把要依赖的端点全部重新验一遍。

为什么重验：探测报告是几天前写的，而我已经吃过一次「拿记忆里的 URL 建东西」的亏
（eCFR 那个假 406）。建抓取器之前花两分钟重验，比写完才发现接口变了便宜得多。

本脚本只读不写，不改任何数据。
"""
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
UAS = [UA,
       "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
       "(KHTML, like Gecko) Version/18.1 Safari/605.1.15"]

_out = []


def rec(n, ok, note):
    _out.append((n, bool(ok), note))
    print(f"[{'OK  ' if ok else 'FAIL'}] {n} :: {note}")


def fetch(url, headers=None, data=None, timeout=90, ua=UA):
    """统一 HTTP：UA、gzip/deflate 正确解压。

    这里绝不关 TLS 校验 —— 证书链有问题就报出来查链，不在客户端把校验关掉。
    """
    h = {"User-Agent": ua}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        enc = (r.headers.get("Content-Encoding") or "").lower()
        if "gzip" in enc:
            raw = gzip.decompress(raw)
        elif "deflate" in enc:
            try:
                raw = zlib.decompress(raw)
            except zlib.error:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        return raw, time.time() - t0, dict(r.headers)


# ============================================================ 1. 巨潮：年报/半年报分类参数
def check_cninfo():
    api = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    # 待验：category 参数能否把范围收窄到 年报+半年报
    params = {
        "tabName": "fulltext", "pageSize": 30, "pageNum": 1,
        "column": "sse", "plate": "sh",
        "stock": "688008,9900039002",          # 澜起科技
        "searchkey": "", "secid": "",
        "category": "category_ndbg_szsh;category_bndbg_szsh",
        "trade": "", "seDate": "2024-01-01~2026-10-04",
        "sortName": "", "sortType": "", "isHLtitle": "true",
    }
    body = urllib.parse.urlencode(params).encode()
    try:
        raw, el, _ = fetch(api, headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
        }, data=body)
        js = json.loads(raw.decode("utf-8"))
        anns = js.get("announcements") or []
        rec("巨潮 category 过滤年报/半年报", bool(anns),
            f"total={js.get('totalRecordNum')} 本页 {len(anns)} 条")
        for a in anns[:6]:
            t = (a.get("announcementTitle") or "").replace("<em>", "").replace("</em>", "")
            sz = a.get("adjunctSize")
            d = time.strftime("%Y-%m-%d", time.localtime(a["announcementTime"] / 1000))
            kind = "PDF" if (a.get("adjunctUrl") or "").endswith(".pdf") else "?"
            rec(f"   · {d}", True, f"{t[:42]}  {sz}KB  {kind}  {a.get('adjunctUrl')}")
    except Exception as e:
        rec("巨潮 category 过滤年报/半年报", False, f"{type(e).__name__}: {str(e)[:80]}")


# ============================================================ 2. SEC EDGAR
def check_sec():
    # 先从官方 ticker 表拿 CIK，不靠记忆
    try:
        raw, el, _ = fetch("https://www.sec.gov/files/company_tickers.json",
                           headers={"Accept": "application/json"})
        js = json.loads(raw.decode("utf-8"))
        hit = [v for v in js.values() if v.get("ticker", "").upper() == "MU"]
        if not hit:
            rec("SEC EDGAR ticker→CIK", False, "未找到 MU")
            return
        cik = int(hit[0]["cik_str"])
        rec("SEC EDGAR ticker→CIK", True, f"MU CIK={cik:010d} {hit[0]['title']}")
    except Exception as e:
        rec("SEC EDGAR ticker→CIK", False, f"{type(e).__name__}: {str(e)[:80]}")
        return

    # submissions API
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        raw, el, _ = fetch(url, headers={"Accept": "application/json",
                                         "User-Agent": "ai_homework3 research contact@example.com"})
        js = json.loads(raw.decode("utf-8"))
        r = js["filings"]["recent"]
        forms = r["form"]
        want = [(f, d, a, p) for f, d, a, p in
                zip(forms, r["filingDate"], r["accessionNumber"], r["primaryDocument"])
                if f in ("10-K", "10-Q")]
        rec("SEC EDGAR submissions", bool(want), f"{len(want)} 份 10-K/10-Q")
        for f, d, a, p in want[:5]:
            acc = a.replace("-", "")
            rec(f"   · {f} {d}", True,
                f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{p}")
    except Exception as e:
        rec("SEC EDGAR submissions", False, f"{type(e).__name__}: {str(e)[:80]}")


# ============================================================ 3. 三星 IR
def check_samsung():
    urls = [
        ("三星 IR 主站", "https://www.samsung.com/global/ir/"),
        ("三星 IR 财报页", "https://www.samsung.com/global/ir/financial-information/earnings-release/"),
        ("三星 IR 年报页", "https://www.samsung.com/global/ir/financial-information/annual-report/"),
    ]
    for label, url in urls:
        try:
            raw, el, _ = fetch(url, timeout=45)
            body = raw.decode("utf-8", "replace")
            pdfs = sorted(set(re.findall(r'https?://[^"\']+?\.pdf', body, re.I)))
            rec(label, len(raw) > 3000, f"{len(raw)/1e3:.0f}KB PDF链接={len(pdfs)}")
            for p in pdfs[:3]:
                rec("   · PDF", True, p[:110])
        except Exception as e:
            rec(label, False, f"{type(e).__name__}: {str(e)[:70]}")


# ============================================================ 4. SK 海力士
def check_skhynix():
    # 记忆中的端点：homeapi.skhynix.com/board/list?bcode=101
    base = "https://homeapi.skhynix.com/board/list"
    for bcode, label in [(101, "Audit/Annual Report"), (105, "Earnings Release"),
                         (102, "Disclosure")]:
        q = urllib.parse.urlencode({"bcode": bcode, "pageSize": 5,
                                    "lang": "ENG", "pageNo": 1})
        try:
            raw, el, _ = fetch(f"{base}?{q}", timeout=45,
                               headers={"Accept": "application/json",
                                        "Referer": "https://www.skhynix.com/",
                                        "Origin": "https://www.skhynix.com"})
            js = json.loads(raw.decode("utf-8"))
            # 结构可能是 list 或被包一层
            items = js if isinstance(js, list) else (
                js.get("list") or js.get("data") or js.get("result") or [])
            rec(f"SK hynix bcode={bcode} {label}", bool(items),
                f"{len(items)} 条  顶层键={list(js)[:6] if isinstance(js, dict) else 'list'}")
            for it in items[:3]:
                if isinstance(it, dict):
                    rec("   · 条目", True,
                        f"keys={list(it)[:8]}  title={(it.get('title') or '')[:40]}")
                    break
        except urllib.error.HTTPError as e:
            rec(f"SK hynix bcode={bcode} {label}", False, f"HTTP {e.code}")
        except Exception as e:
            rec(f"SK hynix bcode={bcode} {label}", False,
                f"{type(e).__name__}: {str(e)[:70]}")


# ============================================================ 5. 规则库
def check_rules():
    # 取 6 篇 HBM 规则里最关键的那篇，看正文能不能全文拿到
    url = ("https://www.federalregister.gov/api/v1/documents/2024-28270.json"
           "?fields[]=title&fields[]=publication_date&fields[]=effective_on"
           "&fields[]=raw_text_url&fields[]=html_url&fields[]=citation&fields[]=abstract")
    try:
        raw, el, _ = fetch(url, headers={"Accept": "application/json"})
        js = json.loads(raw.decode("utf-8"))
        rec("FR 89 FR 96790 元数据", bool(js.get("raw_text_url")),
            f"{js.get('citation')} 发布={js.get('publication_date')} "
            f"生效={js.get('effective_on')}")
        rec("   · raw_text_url", bool(js.get("raw_text_url")), str(js.get("raw_text_url"))[:110])
        if js.get("raw_text_url"):
            t, el2, _ = fetch(js["raw_text_url"], timeout=180)
            body = t.decode("utf-8", "replace")
            rec("   正文可取", len(body) > 50000,
                f"{len(t)/1e6:.2f}MB  HBM={body.count('HBM')}  3A090={body.count('3A090')} "
                f"DRAM={body.count('DRAM')}")
    except Exception as e:
        rec("FR 89 FR 96790", False, f"{type(e).__name__}: {str(e)[:80]}")

    # govinfo 年度版 CFR（法规正文，论文逐字引用用）
    try:
        u = "https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml"
        raw, el, enc = fetch(u, timeout=180)
        x = raw.decode("utf-8", "replace")
        rec("govinfo CFR 年度版", "3A090" in x,
            f"{len(raw)/1e6:.2f}MB enc={enc or '-'} 3A090={x.count('3A090')} "
            f"DRAM={x.count('DRAM')} HBM={x.count('HBM')}")
    except Exception as e:
        rec("govinfo CFR 年度版", False, f"{type(e).__name__}: {str(e)[:80]}")


def main():
    print("=" * 74)
    print("阶段 1 动工前的端点复验")
    print("=" * 74)
    for name, fn in [("巨潮 cninfo", check_cninfo), ("SEC EDGAR", check_sec),
                     ("三星 IR", check_samsung), ("SK 海力士", check_skhynix),
                     ("规则库 FR/govinfo", check_rules)]:
        print(f"\n--- {name} ---")
        try:
            fn()
        except Exception as e:
            rec(name + "（整体）", False, f"{type(e).__name__}: {str(e)[:80]}")

    lines = ["# 阶段 1 端点复验报告", "",
             f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| 检查项 | 结果 | 实测记录 |", "|---|---|---|"]
    for n, ok, note in _out:
        lines.append(f"| {n} | {'✅' if ok else '❌'} | {note} |")
    (ROOT / "verify_endpoints.md").write_text("\n".join(lines), encoding="utf-8")
    bad = [n for n, ok, _ in _out if not ok]
    print(f"\n{'='*74}\n失败 {len(bad)} 项：{bad[:8]}\n→ {ROOT/'verify_endpoints.md'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

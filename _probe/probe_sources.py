# -*- coding: utf-8 -*-
"""
作业三 · 内存产业语料来源可行性探测

目的：在写方案之前，先把「到底抓得到什么」摸清楚。
纪律：只做 GET/轻量 POST，不落大数据；每条记录 HTTP 状态、耗时、字节数、
      以及「拿到的是不是我要的东西」的一句判断。不猜、不凭记忆下结论。

产出：_probe/probe_report.md（UTF-8）
用法：python probe_sources.py
"""
import json
import os
import re
import ssl
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "probe_report.md"

# SEC 要求 UA 带联系方式；长期使用需换成你自己的邮箱
SEC_UA = "Fudan AI Course Research/0.1 (course project; contact: replace-with-your-email@example.com)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")

_results = []


def rec(name, ok, note, extra=""):
    _results.append((name, ok, note, extra))
    print(f"[{'OK ' if ok else 'FAIL'}] {name} :: {note}")


def get(url, ua=BROWSER_UA, timeout=30, headers=None, data=None, encoding=None):
    """返回 (status, body_text, elapsed, length)。失败抛异常由调用方接。"""
    h = {"User-Agent": ua}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    t0 = time.time()
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        raw = r.read()
        el = time.time() - t0
        enc = encoding or r.headers.get_content_charset() or "utf-8"
        try:
            body = raw.decode(enc, errors="replace")
        except LookupError:
            body = raw.decode("utf-8", errors="replace")
        return r.status, body, el, len(raw)


# ---------------------------------------------------------------- 1. 巨潮（A 股）
def probe_cninfo():
    """A 股侧：复用作业二已验证的写法。先查 orgId，再查公告，再下 PDF。"""
    search = "http://www.cninfo.com.cn/new/information/topSearch/query"
    data = urllib.parse.urlencode({"keyWord": "澜起科技", "maxNum": 10}).encode()
    try:
        st, body, el, n = get(search, data=data, headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        })
        js = json.loads(body)
        item = js[0] if isinstance(js, list) and js else {}
        rec("巨潮 topSearch（取 orgId）", bool(item),
            f"{st} {el:.1f}s {n}B → code={item.get('code')} orgId={item.get('orgId')} "
            f"zwjc={item.get('zwjc')} category={item.get('category')}")
        if not item:
            return
        code, org = item["code"], item["orgId"]
    except Exception as e:
        rec("巨潮 topSearch（取 orgId）", False, f"{type(e).__name__}: {str(e)[:80]}")
        return

    # 查公告：直接用作业二的接口
    api = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    params = urllib.parse.urlencode({
        "tabName": "fulltext", "pageSize": 30, "pageNum": 1,
        "column": "sse", "plate": "sh", "stock": f"{code},{org}",
        "seDate": "2025-01-01~2026-12-31",
        "category": "category_ndbg_szsh;category_bndbg_szsh;",  # 年报+半年报
    }).encode()
    try:
        st, body, el, n = get(api, data=params, headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        })
        js = json.loads(body)
        anns = js.get("announcements") or []
        titles = [a.get("announcementTitle", "")[:40] for a in anns[:5]]
        rec("巨潮 hisAnnouncement（按年报/半年报类别筛）", bool(anns),
            f"{st} {el:.1f}s {n}B total={js.get('totalRecordNum')} 命中={len(anns)}；"
            f"前几条={titles}")
        if anns:
            a = anns[0]
            pdf = "http://static.cninfo.com.cn/" + a["adjunctUrl"]
            st2, body2, el2, n2 = get(pdf, timeout=90)
            head = body2[:4]
            is_pdf = head.startswith("%PDF")
            rec("巨潮 PDF 全文下载", is_pdf,
                f"{st2} {el2:.1f}s {n2/1e6:.2f}MB {head!r} 文件={a.get('announcementTitle','')[:30]}")
            if is_pdf:
                dest = ROOT / "sample_cninfo.pdf"
                dest.write_bytes(body2.encode("latin-1", errors="ignore") if isinstance(body2, str) else body2)
    except Exception as e:
        rec("巨潮 hisAnnouncement（按年报/半年报类别筛）", False,
            f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 2. SEC EDGAR（美光）
def probe_sec():
    tick = "https://www.sec.gov/files/company_tickers.json"
    try:
        st, body, el, n = get(tick, ua=SEC_UA)
        js = json.loads(body)
        mu = [v for v in js.values() if v.get("ticker") == "MU"]
        cik = str(mu[0]["cik_str"]).zfill(10) if mu else "0000723125"
        rec("SEC company_tickers.json", bool(mu),
            f"{st} {el:.1f}s {n}B → MU cik={cik} {mu[0]['title'] if mu else ''}")
    except Exception as e:
        rec("SEC company_tickers.json", False, f"{type(e).__name__}: {str(e)[:80]}")
        cik = "0000723125"

    try:
        st, body, el, n = get(f"https://data.sec.gov/submissions/CIK{cik}.json", ua=SEC_UA)
        js = json.loads(body)
        ren = js["filings"]["recent"]
        rows = list(zip(ren["form"], ren["filingDate"], ren["accessionNumber"],
                        ren["primaryDocument"], ren["reportDate"]))
        tens = [r for r in rows if r[0] in ("10-K", "10-Q", "20-F")][:4]
        rec("SEC submissions（美光申报清单）", bool(tens),
            f"{st} {el:.1f}s {n/1e6:.2f}MB name={js.get('name')} sic={js.get('sicDescription')}；"
            f"最近={[(a,b,d) for a,b,_,_,d in tens]}")
        if tens:
            form, fdate, acc, doc, rep = tens[0]
            accn = acc.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{doc}"
            st2, body2, el2, n2 = get(url, ua=SEC_UA, timeout=90)
            rec("SEC 主文档（10-K/10-Q）下载", n2 > 100_000,
                f"{st2} {el2:.1f}s {n2/1e6:.2f}MB {form} {fdate} 报告期={rep} "
                f"html={body2.lstrip()[:15]!r}")
            if n2 > 100_000:
                (ROOT / "sample_mu_filing.html").write_bytes(body2.encode("utf-8"))
    except Exception as e:
        rec("SEC submissions（美光申报清单）", False,
            f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 3. Federal Register（BIS 规则）
def probe_fedreg():
    base = "https://www.federalregister.gov/api/v1/documents.json"
    q = {
        "fields[]": ["title", "publication_date", "document_number", "html_url",
                     "pdf_url", "type", "agencies"],
        "per_page": 20,
        "order": "newest",
        "conditions[agencies][]": "industry-and-security-bureau",
        "conditions[term]": "advanced computing",
    }
    url = base + "?" + urllib.parse.urlencode(q, doseq=True)
    try:
        st, body, el, n = get(url)
        js = json.loads(body)
        res = js.get("results", [])
        rec("Federal Register API（BIS 文件检索）", bool(res),
            f"{st} {el:.1f}s {n}B count={js.get('count')}；"
            f"最近={[(r['publication_date'], r['title'][:50]) for r in res[:3]]}")
        if res:
            html = res[0].get("html_url")
            st2, body2, el2, n2 = get(html)
            has_hbm = "HBM" in body2 or "high bandwidth memory" in body2.lower()
            rec("Federal Register 单篇正文", n2 > 20_000,
                f"{st2} {el2:.1f}s {n2/1e3:.0f}KB 提HBM={has_hbm} 标题={res[0]['title'][:60]}")
    except Exception as e:
        rec("Federal Register API（BIS 文件检索）", False,
            f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 4. eCFR（EAR 条文全文）
def probe_ecfr():
    # 15 CFR Part 774 = Commerce Control List（含 3A090 等 ECCN）
    url = ("https://www.ecfr.gov/api/versioner/v1/full/2026-01-01/title-15.xml"
           "?part=774")
    try:
        st, body, el, n = get(url, timeout=90)
        has = "3A090" in body and "3A001" in body
        rec("eCFR API（15 CFR 774 商业管制清单全文）", n > 100_000,
            f"{st} {el:.1f}s {n/1e6:.2f}MB 含3A090={ '3A090' in body } "
            f"含3A001={'3A001' in body} 结构化XML={body.lstrip().startswith('<?xml')}")
        if n > 100_000:
            (ROOT / "sample_ecfr_774.xml").write_bytes(body.encode("utf-8"))
    except Exception as e:
        rec("eCFR API（15 CFR 774 商业管制清单全文）", False,
            f"{type(e).__name__}: {str(e)[:80]}")

    # 单条 ECCN 的精确取法（3A090 = 高性能计算/HBM 相关）
    try:
        url2 = "https://www.ecfr.gov/api/versioner/v1/full/2026-01-01/title-15.xml?part=774&section=774.1"
        st, body, el, n = get(url2, timeout=60)
        rec("eCFR 按 section 精确取", n > 1000, f"{st} {el:.1f}s {n}B")
    except Exception as e:
        rec("eCFR 按 section 精确取", False, f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 5. BIS 官网直连
def probe_bis():
    for name, url in [
        ("BIS 官网首页", "https://www.bis.gov/"),
        ("BIS EAR 页", "https://www.bis.gov/regulations/ear"),
    ]:
        try:
            st, body, el, n = get(url, timeout=30)
            rec(name, n > 5000, f"{st} {el:.1f}s {n/1e3:.0f}KB")
        except Exception as e:
            rec(name, False, f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 6. 韩国 DART（三星 / SK海力士）
def probe_dart():
    for name, url in [
        ("DART 英文站首页", "https://englishdart.fss.or.kr/"),
        ("DART 中文站首页", "https://dart.fss.or.kr/"),
        ("OpenDART API 无 key 探测", "https://opendart.fss.or.kr/api/list.json?crtfc_key=x&corp_code=00126380"),
    ]:
        try:
            st, body, el, n = get(url, timeout=30)
            rec(name, n > 500, f"{st} {el:.1f}s {n/1e3:.0f}KB 首80字={body[:80].strip()!r}")
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:200]
            except Exception:
                pass
            rec(name, e.code in (400, 401, 403), f"HTTP {e.code}（可达，返回体={detail!r}）")
        except Exception as e:
            rec(name, False, f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 7. 台湾 MOPS（南亚科 / 华邦）
def probe_mops():
    for name, url in [
        ("MOPS 首页", "https://mops.twse.com.tw/mops/web/index"),
        ("MOPS 年报查询页", "https://mops.twse.com.tw/mops/web/t57sb01_q1"),
        ("TWSE OpenAPI", "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"),
    ]:
        try:
            st, body, el, n = get(url, timeout=30)
            rec(name, n > 500, f"{st} {el:.1f}s {n/1e3:.0f}KB 首60字={body[:60].strip()!r}")
        except Exception as e:
            rec(name, False, f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 8. TrendForce（价格方向）
def probe_trendforce():
    for name, url in [
        ("TrendForce 新闻中心", "https://www.trendforce.com/presscenter/"),
        ("TrendForce 首页", "https://www.trendforce.com/"),
    ]:
        try:
            st, body, el, n = get(url, timeout=30)
            has = bool(re.search(r"DRAM|HBM|NAND", body, re.I))
            rec(name, n > 5000, f"{st} {el:.1f}s {n/1e3:.0f}KB 提DRAM/HBM/NAND={has}")
        except Exception as e:
            rec(name, False, f"{type(e).__name__}: {str(e)[:80]}")


# ---------------------------------------------------------------- 9. 内存产业链 A 股名单实测
def probe_ashare_list():
    """对候选公司逐个取 orgId，确认「10 家以上」能凑齐。"""
    names = ["澜起科技", "兆易创新", "江波龙", "佰维存储", "德明利", "北京君正",
             "东芯股份", "普冉股份", "聚辰股份", "香农芯创", "深科技", "太极实业",
             "雅克科技", "鼎龙股份", "安集科技", "兴森科技"]
    ok, bad = [], []
    for nm in names:
        data = urllib.parse.urlencode({"keyWord": nm, "maxNum": 3}).encode()
        try:
            st, body, el, n = get("http://www.cninfo.com.cn/new/information/topSearch/query",
                                  data=data, headers={
                                      "X-Requested-With": "XMLHttpRequest",
                                      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                  }, timeout=20)
            js = json.loads(body)
            hit = [x for x in js if x.get("zwjc") == nm] or js
            if hit:
                x = hit[0]
                ok.append(f"{nm}({x.get('code')},{x.get('orgId')})")
            else:
                bad.append(nm)
        except Exception as e:
            bad.append(f"{nm}:{type(e).__name__}")
        time.sleep(0.8)
    rec("A 股内存产业链 orgId 批量取号", len(ok) >= 10,
        f"成功 {len(ok)}/{len(names)}；未命中={bad}")
    if ok:
        (ROOT / "cninfo_orgids.txt").write_text("\n".join(ok), encoding="utf-8")


def main():
    print("=" * 70)
    print("作业三 · 语料来源可行性探测")
    print("=" * 70)
    probes = [
        ("巨潮（A股）", probe_cninfo),
        ("SEC EDGAR（美光）", probe_sec),
        ("Federal Register（BIS规则）", probe_fedreg),
        ("eCFR（EAR条文）", probe_ecfr),
        ("BIS官网", probe_bis),
        ("韩国 DART", probe_dart),
        ("台湾 MOPS", probe_mops),
        ("TrendForce", probe_trendforce),
        ("A股名单取号", probe_ashare_list),
    ]
    for name, fn in probes:
        print(f"\n--- {name} ---")
        try:
            fn()
        except Exception:
            rec(name, False, "探测函数本身异常：" + traceback.format_exc(limit=2)[-200:])

    lines = ["# 作业三 · 语料来源探测报告", "",
             f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| 来源 | 结果 | 实测记录 |", "|---|---|---|"]
    for name, ok, note, _ in _results:
        lines.append(f"| {name} | {'✅ 可用' if ok else '❌ 不可用'} | {note} |")
    n_ok = sum(1 for _, ok, _, _ in _results if ok)
    lines += ["", f"**小结：{n_ok}/{len(_results)} 项通过。**"]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已写入 {REPORT}")


if __name__ == "__main__":
    main()

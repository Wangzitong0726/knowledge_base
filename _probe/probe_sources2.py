# -*- coding: utf-8 -*-
"""
探测第二轮：追第一轮的失败项 + 验证「提取文字/表格」这一步。

第一轮结论：巨潮/SEC/FederalRegister/BIS/TrendForce 通；eCFR 406、MOPS 证书、DART 英文申报未定。
本轮要回答的是「拿到 PDF/HTML 之后能不能用」——这才是作业②③步的真正门槛。

修正第一轮的一个自己的 bug：PDF 是二进制，必须先取 bytes 再落盘，不能 decode 成 str 再 encode。
"""
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEC_UA = "Fudan AI Course Research/0.1 (course project; contact: replace-with-your-email@example.com)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
_out = []


def rec(name, ok, note):
    _out.append((name, ok, note))
    print(f"[{'OK ' if ok else 'FAIL'}] {name} :: {note}")


def fetch(url, ua=BROWSER_UA, headers=None, data=None, timeout=60, tries=3):
    """返回 (status, bytes, elapsed)。重试 + 指数退避。

    纪律：证书一律正常校验，不提供关闭校验的开关。证书链有问题就去查链，
    不在客户端把校验关掉——那样 TLS 就只剩加密、没有身份验证了。
    """
    h = {"User-Agent": ua}
    if headers:
        h.update(headers)
    ctx = ssl.create_default_context()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.status, r.read(), time.time() - t0
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (400, 401, 403, 406, 404):     # 这类重试没用，直接抛
                raise
            time.sleep(2 ** i)
        except Exception as e:
            last = e
            time.sleep(2 ** i)
    raise last


# ------------------------------------------------------------------ A. eCFR 406 追因
def probe_ecfr_again():
    url = "https://www.ecfr.gov/api/versioner/v1/full/2026-01-01/title-15.xml?part=774"
    variants = [
        ("默认 UA + Accept: application/xml", {"Accept": "application/xml"}),
        ("默认 UA + Accept: */*", {"Accept": "*/*"}),
        ("浏览器 UA + Accept: application/xml", {"Accept": "application/xml"}),
        ("默认 UA + Accept: application/xml + Accept-Encoding: identity",
         {"Accept": "application/xml", "Accept-Encoding": "identity"}),
    ]
    for label, hdr in variants:
        try:
            st, raw, el = fetch(url, headers=hdr, timeout=90)
            xml = raw.decode("utf-8", "replace")
            rec(f"eCFR 重试（{label}）", len(raw) > 100_000,
                f"{st} {el:.1f}s {len(raw)/1e6:.2f}MB 含3A090={'3A090' in xml} "
                f"含HBM={'HBM' in xml}")
            if len(raw) > 100_000:
                (ROOT / "sample_ecfr_774.xml").write_bytes(raw)
                return True
        except urllib.error.HTTPError as e:
            rec(f"eCFR 重试（{label}）", False, f"HTTP {e.code}")
        except Exception as e:
            rec(f"eCFR 重试（{label}）", False, f"{type(e).__name__}: {str(e)[:60]}")
    return False


def probe_ecfr_json():
    """换一条路：eCFR 的 JSON 版（structure / content 两个端点）。"""
    for label, url in [
        ("eCFR 目录树 API", "https://www.ecfr.gov/api/versioner/v1/titles.json"),
        ("eCFR 单节 JSON", "https://www.ecfr.gov/api/versioner/v1/full/2026-01-01/title-15.json?part=774"),
    ]:
        try:
            st, raw, el = fetch(url, headers={"Accept": "application/json"}, timeout=90)
            rec(f"{label}", len(raw) > 500, f"{st} {el:.1f}s {len(raw)/1e3:.0f}KB "
                f"{raw[:120].decode('utf-8','replace')!r}")
        except Exception as e:
            rec(f"{label}", False, f"{type(e).__name__}: {str(e)[:60]}")


# ------------------------------------------------------------------ B. MOPS 证书诊断（只诊断，不绕过）
def probe_mops_again():
    """MOPS 报 CERTIFICATE_VERIFY_FAILED：查清是「服务器证书链不完整」还是「本机缺根证书」。

    做法是拿正常的校验上下文去连、把 OpenSSL 的报错原文读出来，再独立看一下
    服务器实际发过来的证书链有几张。不在客户端关校验。
    """
    import socket
    host, port = "mops.twse.com.tw", 443
    for label, url in [("MOPS 首页", f"https://{host}/mops/web/index")]:
        try:
            fetch(url, timeout=20)
            rec(f"{label}（正常校验）", True, "证书校验通过")
        except ssl.SSLError as e:
            rec(f"{label}（正常校验）", False, f"SSL: {str(e)[:110]}")
        except Exception as e:
            rec(f"{label}（正常校验）", False, f"{type(e).__name__}: {str(e)[:90]}")

    # 独立看服务器发的链：几张证书、签发者是谁、缺不缺中间 CA
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=15) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ss:
                cert = ss.getpeercert()
                chain = ss.get_unverified_chain() if hasattr(ss, "get_unverified_chain") else []
        subject = {k: v for item in cert.get("subject", ()) for k, v in item}
        issuer = {k: v for item in cert.get("issuer", ()) for k, v in item}
        rec("MOPS 证书本身", True,
            f"CN={subject.get('commonName')} 签发者={issuer.get('commonName')} "
            f"有效期={cert.get('notBefore')} ~ {cert.get('notAfter')}")
    except ssl.SSLError as e:
        rec("MOPS 证书本身", False, f"握手阶段就失败：{str(e)[:110]}")
    except Exception as e:
        rec("MOPS 证书本身", False, f"{type(e).__name__}: {str(e)[:90]}")

    # 旁证：同一台机器访问其他台湾政府站点是否同样失败（判断是本机 CA 库问题还是该站问题）
    for label, url in [("台湾证交所 www.twse.com.tw", "https://www.twse.com.tw/"),
                       ("公开资讯观测站 openapi", "https://openapi.twse.com.tw/v1/opendata/t187ap03_L")]:
        try:
            st, raw, el = fetch(url, timeout=20)
            rec(f"{label}（正常校验）", len(raw) > 100,
                f"{st} {el:.1f}s {len(raw)/1e3:.0f}KB —— 同机可达，说明不是全局 CA 问题")
        except Exception as e:
            rec(f"{label}（正常校验）", False, f"{type(e).__name__}: {str(e)[:90]}")


# ------------------------------------------------------------------ C. DART 英文申报
def probe_dart_deep():
    # DART 英文站检索接口（公开页，无需 key）
    url = "https://englishdart.fss.or.kr/dsbb001/searchReptList.ax"
    body = urllib.parse.urlencode({
        "currentPage": "1", "maxResults": "15", "maxLinks": "10",
        "sort": "date", "series": "desc", "textCrpNm": "SK hynix",
        "reportName": "", "startDate": "2025-01-01", "endDate": "2026-12-31",
    }).encode()
    try:
        st, raw, el = fetch(url, data=body, timeout=40, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://englishdart.fss.or.kr/",
        })
        txt = raw.decode("utf-8", "replace")
        rec("DART 英文检索接口（SK hynix）", len(raw) > 100,
            f"{st} {el:.1f}s {len(raw)/1e3:.0f}KB {txt[:150]!r}")
    except Exception as e:
        rec("DART 英文检索接口（SK hynix）", False, f"{type(e).__name__}: {str(e)[:70]}")

    # 中文站检索（DART 主体，韩国公司都在）
    url2 = "https://dart.fss.or.kr/dsab007/searchList.ax"
    body2 = urllib.parse.urlencode({
        "currentPage": "1", "maxResults": "15", "maxLinks": "10", "sort": "date",
        "series": "desc", "textCrpNm": "SK하이닉스", "reportName": "",
        "startDate": "2025-01-01", "endDate": "2026-12-31",
        "publicType": "A001",
    }).encode()
    try:
        st, raw, el = fetch(url2, data=body2, timeout=40, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://dart.fss.or.kr/",
        })
        txt = raw.decode("utf-8", "replace")
        rec("DART 中文站检索接口（SK하이닉스）", len(raw) > 100,
            f"{st} {el:.1f}s {len(raw)/1e3:.0f}KB {txt[:200]!r}")
    except Exception as e:
        rec("DART 中文站检索接口（SK하이닉스）", False, f"{type(e).__name__}: {str(e)[:70]}")


# ------------------------------------------------------------------ D. Federal Register：锁定 HBM 规则
def probe_hbm_rule():
    q = {
        "fields[]": ["title", "publication_date", "document_number", "html_url",
                     "pdf_url", "type", "citation", "effective_on"],
        "per_page": 20, "order": "oldest",
        "conditions[term]": "high bandwidth memory",
    }
    url = "https://www.federalregister.gov/api/v1/documents.json?" + \
          urllib.parse.urlencode(q, doseq=True)
    try:
        st, raw, el = fetch(url)
        js = json.loads(raw)
        res = js.get("results", [])
        rec("Federal Register 搜 'high bandwidth memory'", bool(res),
            f"count={js.get('count')}；" +
            "；".join(f"{r['publication_date']} {r['title'][:55]}" for r in res[:5]))
        if res:
            (ROOT / "fedreg_hbm_hits.json").write_text(
                json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
            # 抓最早那篇的正文，确认是不是管制规则本体
            st2, raw2, el2 = fetch(res[0]["html_url"])
            body = raw2.decode("utf-8", "replace")
            rec("最早一篇正文", len(raw2) > 20_000,
                f"{len(raw2)/1e3:.0f}KB 标题={res[0]['title'][:70]}；"
                f"含'3A090'={'3A090' in body} 含'HBM'={'HBM' in body} "
                f"含'Comment'={'Comments' in body}")
    except Exception as e:
        rec("Federal Register 搜 'high bandwidth memory'", False,
            f"{type(e).__name__}: {str(e)[:70]}")


# ------------------------------------------------------------------ E. 提取环节：cninfo PDF
def probe_extract_cninfo():
    """作业②：「提取文字，表格按行列还原」。先证明这一步在本机做得成。"""
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    # 重新规范地下一份：先 bytes 再落盘
    search = "http://www.cninfo.com.cn/new/information/topSearch/query"
    st, raw, el = fetch(search, data=urllib.parse.urlencode(
        {"keyWord": "澜起科技", "maxNum": 3}).encode(), headers={
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    item = json.loads(raw)[0]
    code, org = item["code"], item["orgId"]
    api = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    st, raw, el = fetch(api, data=urllib.parse.urlencode({
        "tabName": "fulltext", "pageSize": 30, "pageNum": 1, "column": "sse",
        "plate": "sh", "stock": f"{code},{org}", "seDate": "2025-01-01~2026-12-31",
        "category": "category_ndbg_szsh;category_bndbg_szsh;",
    }).encode(), headers={
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    anns = json.loads(raw)["announcements"]
    a = anns[0]
    url = "http://static.cninfo.com.cn/" + a["adjunctUrl"]
    st, pdf_bytes, el = fetch(url, timeout=120)
    ok_head = pdf_bytes[:4] == b"%PDF"
    dest = ROOT / "sample_cninfo.pdf"
    dest.write_bytes(pdf_bytes)
    rec("巨潮 PDF 二进制落盘（修正第一轮 bug）", ok_head,
        f"{st} {len(pdf_bytes)/1e6:.2f}MB 头={pdf_bytes[:4]!r} {a['announcementTitle'][:30]}")

    doc = pymupdf.open(str(dest))
    total_chars = 0
    txt_pages = 0
    for p in doc:
        t = p.get_text()
        total_chars += len(t)
        if len(t) > 30:
            txt_pages += 1
    rec("PDF 文字层提取", total_chars > 1000,
        f"{doc.page_count} 页 / 有文字页 {txt_pages} / 共 {total_chars} 字 "
        f"→ 平均 {total_chars/max(doc.page_count,1):.0f} 字/页")
    # 表格：找一个含数字最多的页，看 find_tables 能不能还原行列
    best, best_n = None, 0
    for i in range(min(doc.page_count, 80)):
        tbs = doc[i].find_tables()
        if len(tbs.tables) > best_n:
            best, best_n = i, len(tbs.tables)
    if best is not None:
        tb = doc[best].find_tables().tables[0]
        rows = tb.extract()
        rec("PDF 表格按行列还原（find_tables）", len(rows) >= 3,
            f"第{best+1}页 检出 {best_n} 张表；首表 {len(rows)}行×{len(rows[0]) if rows else 0}列；"
            f"首行={str(rows[0])[:100]}")
        (ROOT / "sample_table.txt").write_text(
            "\n".join(" | ".join(str(c) for c in r) for r in rows[:15]), encoding="utf-8")
    else:
        rec("PDF 表格按行列还原（find_tables）", False, "前 80 页未检出表格")
    # 顺带取几页正文看内容是否真是财报
    sample = doc[10].get_text()[:200].replace("\n", " ")
    rec("正文抽样（第11页）", len(sample) > 50, f"{sample!r}")


# ------------------------------------------------------------------ F. 提取环节：SEC HTML
def probe_extract_sec():
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    st, raw, el = fetch("https://data.sec.gov/submissions/CIK0000723125.json", ua=SEC_UA)
    ren = json.loads(raw)["filings"]["recent"]
    rows = list(zip(ren["form"], ren["filingDate"], ren["accessionNumber"], ren["primaryDocument"]))
    row = [r for r in rows if r[0] == "10-K"][0]
    form, fdate, acc, doc = row
    url = f"https://www.sec.gov/Archives/edgar/data/723125/{acc.replace('-','')}/{doc}"
    st, raw, el = fetch(url, ua=SEC_UA, timeout=120)
    (ROOT / "sample_mu_10k.html").write_bytes(raw)
    rec("SEC 10-K 落盘", len(raw) > 500_000,
        f"{form} {fdate} {len(raw)/1e6:.2f}MB 主文档={doc}")
    # 用 PyMuPDF 的 HTML 解析器？不行——改用 lxml 抽表格
    try:
        from lxml import html as LH
        tree = LH.fromstring(raw)
        tables = tree.xpath("//table")
        texts = tree.xpath("//text()")
        alltext = " ".join(t.strip() for t in texts if t.strip())
        rec("SEC HTML 文字提取（lxml）", len(alltext) > 100_000,
            f"{len(alltext)} 字 / {len(tables)} 张 <table>")
        for kw in ["HBM", "high bandwidth memory", "export control", "Entity List", "China"]:
            rec(f"  · 关键词 '{kw}'", True, f"命中 {alltext.lower().count(kw.lower())} 次")
    except Exception as e:
        rec("SEC HTML 文字提取（lxml）", False, f"{type(e).__name__}: {str(e)[:70]}")


def main():
    print("=" * 70)
    print("探测第二轮 · 追失败项 + 验证提取环节")
    print("=" * 70)
    for name, fn in [
        ("eCFR 追因", probe_ecfr_again), ("eCFR JSON 路", probe_ecfr_json),
        ("MOPS 证书诊断", probe_mops_again),
        ("DART 深探", probe_dart_deep), ("HBM 规则定位", probe_hbm_rule),
        ("提取·巨潮PDF", probe_extract_cninfo), ("提取·SEC HTML", probe_extract_sec),
    ]:
        print(f"\n--- {name} ---")
        try:
            fn()
        except Exception as e:
            rec(name, False, f"{type(e).__name__}: {str(e)[:120]}")

    lines = ["# 探测第二轮报告", "", f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| 检查项 | 结果 | 实测记录 |", "|---|---|---|"]
    for n, ok, note in _out:
        lines.append(f"| {n} | {'✅' if ok else '❌'} | {note} |")
    (ROOT / "probe_report2.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n→ {ROOT/'probe_report2.md'}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
探测第三轮：把三个未决口子定死。
  1. eCFR 406 到底卡在哪（换 date / 换端点 / 换 govinfo 备用路）
  2. 出口管制规则里「HBM」是哪一份文件写进去的 —— 用机构过滤+正文 grep 钉死，不靠记忆
  3. 三星 / SK 海力士的英文财报从哪拿（DART 接口未摸到，改试公司 IR 站）

纪律：全部正常 TLS 校验；每个结论都要有实测记录，不做「应该可以」的判断。
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEC_UA = "Fudan AI Course Research/0.1 (course project; contact: replace-with-your-email@example.com)"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
_out = []


def rec(name, ok, note):
    _out.append((name, ok, note))
    print(f"[{'OK ' if ok else 'FAIL'}] {name} :: {note}")


def fetch(url, ua=UA, headers=None, data=None, timeout=60):
    h = {"User-Agent": ua}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(), time.time() - t0


def try_get(url, **kw):
    try:
        return fetch(url, **kw), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code} {e.reason}"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:80]}"


# ---------------------------------------------------------- 1. eCFR
def probe_ecfr3():
    # 先看 title 15 最近一次修订日，用它当 as-of 日期（日期不存在也是 406/404 的常见原因）
    got, err = try_get("https://www.ecfr.gov/api/versioner/v1/titles.json",
                       headers={"Accept": "application/json"})
    if got:
        js = json.loads(got[1])
        t15 = [t for t in js["titles"] if t["number"] == 15]
        rec("eCFR titles.json（title 15 修订日）", bool(t15),
            f"{t15[0]}" if t15 else "未找到 title 15")
    # 试多个日期 + 多个 Accept
    dates = ["2026-08-10", "2026-01-01", "2025-06-01", "2024-12-02"]
    for d in dates:
        for acc in ["application/xml", "text/xml", "*/*"]:
            got, err = try_get(
                f"https://www.ecfr.gov/api/versioner/v1/full/{d}/title-15.xml?part=774",
                headers={"Accept": acc})
            if got:
                xml = got[1].decode("utf-8", "replace")
                rec(f"eCFR full {d} Accept={acc}", True,
                    f"{got[0]} {len(got[1])/1e6:.2f}MB 含3A090={'3A090' in xml} 含HBM={'HBM' in xml}")
                (ROOT / "sample_ecfr_774.xml").write_bytes(got[1])
                return True
            else:
                rec(f"eCFR full {d} Accept={acc}", False, err)

    # 备用路①：structure 端点（不受 full 的 406 影响）
    got, err = try_get("https://www.ecfr.gov/api/versioner/v1/structure/2026-01-01/title-15.json",
                       headers={"Accept": "application/json"})
    rec("eCFR structure 端点", bool(got),
        f"{got[0]} {len(got[1])/1e3:.0f}KB" if got else err)

    # 备用路②：govinfo 的 CFR bulk（免费、无需 key）
    for label, url in [
        ("govinfo CFR-2025 title-15 vol-2", "https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml"),
        ("govinfo bulkdata 目录", "https://www.govinfo.gov/bulkdata/CFR/2025/title-15"),
    ]:
        got, err = try_get(url, timeout=120)
        if got:
            body = got[1].decode("utf-8", "replace")
            rec(label, len(got[1]) > 100_000,
                f"{got[0]} {got[1][:4]!r} {len(got[1])/1e6:.2f}MB 含3A090={'3A090' in body}")
        else:
            rec(label, False, err)

    # 备用路③：BIS 官网的 EAR 全文 PDF
    got, err = try_get("https://www.bis.gov/regulations/ear", timeout=60)
    if got:
        body = got[1].decode("utf-8", "replace")
        pdfs = re.findall(r'href="([^"]+\.pdf)"', body, re.I)
        rec("BIS EAR 页里的 PDF 链接", bool(pdfs), f"发现 {len(pdfs)} 个 PDF：{pdfs[:6]}")
    else:
        rec("BIS EAR 页里的 PDF 链接", False, err)


# ---------------------------------------------------------- 2. 钉死 HBM 规则
def probe_hbm_rules():
    """分两步：先用机构过滤取 BIS 近两年的重要规则，再逐篇 grep 'HBM'。"""
    q = {
        "fields[]": ["title", "publication_date", "document_number", "html_url",
                     "type", "citation", "effective_on", "abstract"],
        "per_page": 60, "order": "newest",
        "conditions[agencies][]": "industry-and-security-bureau",
        "conditions[publication_date][gte]": "2024-10-01",
        "conditions[type][]": "RULE",
    }
    url = "https://www.federalregister.gov/api/v1/documents.json?" + urllib.parse.urlencode(q, doseq=True)
    got, err = try_get(url)
    if not got:
        rec("BIS 规则清单（2024-10 起）", False, err)
        return
    res = json.loads(got[1]).get("results", [])
    rec("BIS 规则清单（2024-10 起）", bool(res), f"共 {len(res)} 篇最终规则")
    (ROOT / "bis_rules.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    hits = []
    for r in res[:25]:
        got2, err2 = try_get(r["html_url"], timeout=60)
        if not got2:
            continue
        body = got2[1].decode("utf-8", "replace")
        n_hbm = len(re.findall(r"\bHBM\b", body))
        n_hbm_full = len(re.findall(r"high[- ]bandwidth memory", body, re.I))
        n_3a090 = len(re.findall(r"3A090", body))
        if n_hbm or n_hbm_full:
            hits.append((r["publication_date"], r["title"][:70], r["citation"], n_hbm, n_hbm_full, n_3a090, r["html_url"]))
        time.sleep(0.3)
    rec("在这批规则里 grep 'HBM'", bool(hits), f"命中 {len(hits)} 篇")
    for d, t, c, a, b, cc, u in hits:
        rec(f"  ▶ {d} {c}", True, f"HBM×{a} high-bandwidth×{b} 3A090×{cc} | {t}")
    if hits:
        (ROOT / "hbm_rules.txt").write_text(
            "\n".join(f"{d}\t{c}\t{a}\t{b}\t{cc}\t{t}\t{u}" for d, t, c, a, b, cc, u in hits),
            encoding="utf-8")


# ---------------------------------------------------------- 3. 三星 / SK 海力士
def probe_korea_ir():
    targets = [
        ("SK hynix IR 首页", "https://www.skhynix.com/eng/ir/irActivity.do"),
        ("SK hynix IR 公告列表", "https://www.skhynix.com/eng/ir/announcement.do"),
        ("Samsung IR 首页", "https://www.samsung.com/global/ir/"),
        ("Samsung IR 财报页", "https://www.samsung.com/global/ir/financial-information/earnings-release/"),
        ("Samsung IR 年报页", "https://www.samsung.com/global/ir/financial-information/annual-reports/"),
    ]
    for label, url in targets:
        got, err = try_get(url, timeout=40)
        if got:
            body = got[1].decode("utf-8", "replace")
            pdfs = re.findall(r'href="([^"]+\.pdf)"', body, re.I)
            rec(label, len(got[1]) > 3000,
                f"{got[0]} {len(got[1])/1e3:.0f}KB PDF链接={len(pdfs)} {pdfs[:3]}")
        else:
            rec(label, False, err)

    # DART 真实接口再试一次：用官方公布的 URL 格式
    for label, url in [
        ("DART 公司检索 JSON", "https://dart.fss.or.kr/dsab007/searchList.ax?currentPage=1&maxResults=10&textCrpNm=SK%ED%95%98%EC%9D%B4%EB%8B%89%EC%8A%A4&publicType=A001"),
        ("DART 英文站 dartList", "https://englishdart.fss.or.kr/dsbb001/dartList.ax?currentPage=1&maxResults=10&textCrpNm=SK%20hynix"),
    ]:
        got, err = try_get(url, timeout=40, headers={"X-Requested-With": "XMLHttpRequest",
                                                     "Referer": "https://dart.fss.or.kr/"})
        if got:
            t = got[1].decode("utf-8", "replace")
            is_json = t.lstrip().startswith(("{", "["))
            rec(label, is_json, f"{got[0]} {len(got[1])/1e3:.0f}KB JSON={is_json} {t[:120]!r}")
        else:
            rec(label, False, err)


# ---------------------------------------------------------- 4. TrendForce 文章页
def probe_trendforce3():
    got, err = try_get("https://www.trendforce.com/presscenter/news", timeout=40)
    if got:
        body = got[1].decode("utf-8", "replace")
        links = sorted(set(re.findall(r'href="(/presscenter/news/[^"#]+)"', body)))
        rec("TrendForce 新闻列表页", bool(links), f"{got[0]} {len(got[1])/1e3:.0f}KB 文章链接 {len(links)} 条；{links[:3]}")
        if links:
            url = "https://www.trendforce.com" + links[0]
            got2, err2 = try_get(url, timeout=40)
            if got2:
                b2 = got2[1].decode("utf-8", "replace")
                txt = re.sub(r"<[^>]+>", " ", b2)
                txt = re.sub(r"\s+", " ", txt)
                has_price = bool(re.search(r"(increase|decrease|rise|fall)\s+by\s+[\d.]+%", txt, re.I))
                rec("TrendForce 单篇文章正文", len(txt) > 500,
                    f"{len(txt)} 字 含涨跌幅表述={has_price}；摘={txt[:220]!r}")
                (ROOT / "trendforce_sample.txt").write_text(txt[:8000], encoding="utf-8")
            else:
                rec("TrendForce 单篇文章正文", False, err2)
    else:
        rec("TrendForce 新闻列表页", False, err)


def main():
    print("=" * 70)
    print("探测第三轮")
    print("=" * 70)
    for n, f in [("eCFR 定死", probe_ecfr3), ("HBM 规则定位", probe_hbm_rules),
                 ("韩系 IR / DART", probe_korea_ir), ("TrendForce 正文", probe_trendforce3)]:
        print(f"\n--- {n} ---")
        try:
            f()
        except Exception as e:
            rec(n, False, f"{type(e).__name__}: {str(e)[:120]}")

    lines = ["# 探测第三轮报告", "", f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| 检查项 | 结果 | 实测记录 |", "|---|---|---|"]
    for n, ok, note in _out:
        lines.append(f"| {n} | {'✅' if ok else '❌'} | {note} |")
    (ROOT / "probe_report3.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n→ {ROOT/'probe_report3.md'}")


if __name__ == "__main__":
    main()

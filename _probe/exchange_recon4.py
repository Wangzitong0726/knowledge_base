# -*- coding: utf-8 -*-
"""
交易所侦察 · 第四轮：收口

  · 深交所：PDF 403 → 补 Referer（第二轮只取了列表，没验证下载）
  · 上交所：616B 空结果 → 不猜了，**直接读它自己页面的 JS**，
    看它调的是哪个接口、带什么参数。猜参数是浪费轮次。
"""
import json
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fetch.common import Fetcher, FetchError          # noqa: E402

f = Fetcher(Path(__file__).resolve().parent / "_recon_manifest.jsonl", delay=1.0)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

# ---------- 1. 深交所 PDF：补 Referer ----------
print("=" * 78)
print("【深交所】补 Referer 后重下 PDF")
PDF = "http://www.szse.cn/disc/disk03/finalpage/2026-08-11/35b248b6-6b97-4fe1-92f5-15a610d4e19c.PDF"
for label, hdr in [
    ("Referer=定期报告页", {**UA, "Referer": "http://www.szse.cn/disclosure/listed/fixed/index.html"}),
    ("Referer=szse根",     {**UA, "Referer": "http://www.szse.cn/"}),
    ("无 Referer",         {**UA}),
]:
    try:
        raw, h = f.get(PDF, headers=hdr, timeout=90, retries=1)
        print(f"  [{label}] OK {len(raw):,}B  魔术字={raw[:5]}  CT={h.get('Content-Type','')[:30]}")
        (Path(__file__).resolve().parent / "_szse_test.pdf").write_bytes(raw)
        break
    except FetchError as e:
        print(f"  [{label}] {str(e)[:100]}")

# ---------- 2. 上交所：读它自己的页面找接口 ----------
print("\n" + "=" * 78)
print("【上交所】不猜参数，读页面的 JS")
try:
    html = f.get_text("http://www.sse.com.cn/disclosure/listedinfo/regular/",
                      headers=UA, timeout=45, retries=2)
    print(f"  页面 {len(html):,} 字符")
    # 找 JS 文件引用
    for js in re.findall(r'src="([^"]+\.js[^"]*)"', html)[:12]:
        print("   js:", js)
    # 找接口线索
    for pat in [r'sqlId["\']?\s*[:=]\s*["\']([A-Z_0-9]+)',
                r'(query[A-Za-z]+\.do)',
                r'(common[A-Za-z]*Query[A-Za-z]*\.do)']:
        hits = set(re.findall(pat, html))
        if hits:
            print(f"   接口线索 {pat[:24]}… → {list(hits)[:6]}")
except FetchError as e:
    print("  FAIL", str(e)[:120])

# 上交所另一个已知家族：上市公司公告 sse 页面
try:
    html2 = f.get_text("http://www.sse.com.cn/disclosure/listedinfo/announcement/",
                       headers=UA, timeout=45, retries=2)
    print(f"\n  公告页 {len(html2):,} 字符")
    for pat in [r'(query[A-Za-z]+\.do)', r'sqlId=([A-Z_0-9]+)',
                r'src="([^"]+bulletin[^"]*\.js)"']:
        hits = set(re.findall(pat, html2, re.I))
        if hits:
            print(f"   → {list(hits)[:8]}")
except FetchError as e:
    print("  FAIL", str(e)[:120])

# ---------- 3. 试 SSE 已知 sqlId 家族 ----------
print("\n【上交所】试 commonSoaQuery / 常见 sqlId")
CANDIDATES = [
    ("SSE 公告(新)", "http://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"
                     "?jsonCallBack=jsonpCallback&isPagination=true&productId=688008"
                     "&securityType=0101%2C120100%2C020100%2C020200%2C120200&reportType2=DQBG"
                     "&reportType=ALL&beginDate=2024-01-01&endDate=2026-10-04"
                     "&pageHelp.pageSize=25&pageHelp.pageNo=1&pageHelp.beginPage=1"
                     "&pageHelp.cacheSize=1&pageHelp.endPage=1"),
    ("SSE 定期报告列表接口", "http://query.sse.com.cn/commonQuery.do"
                             "?sqlId=COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L&isPagination=true"
                             "&pageHelp.pageSize=25&pageHelp.pageNo=1&COMPANY_CODE=688008"),
    ("SSE 信息披露(定期)", "http://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"
                            "?jsonCallBack=jsonpCallback&isPagination=true&productId=600667"
                            "&securityType=0101&reportType2=DQBG&reportType=ALL"
                            "&beginDate=2024-01-01&endDate=2026-10-04"
                            "&pageHelp.pageSize=25&pageHelp.pageNo=1"),
]
for label, url in CANDIDATES:
    try:
        raw, _ = f.get(url, headers={**UA, "Referer": "http://www.sse.com.cn/disclosure/listedinfo/regular/",
                                     "Accept": "*/*"}, timeout=45, retries=1)
        t = raw.decode("utf-8", "replace")
        n_url = len(re.findall(r'"(?:URL|url)"', t))
        n_title = len(re.findall(r'"(?:TITLE|title)"', t))
        print(f"  [{label}] {len(raw):,}B  URL字段={n_url} TITLE字段={n_title}")
        if len(raw) < 900:
            print("     内容:", t[:300].replace("\n", " "))
        else:
            for u in re.findall(r'"URL":"([^"]+)"', t)[:3]:
                print("      ", u)
    except FetchError as e:
        print(f"  [{label}] FAIL {str(e)[:90]}")
print("=" * 78)

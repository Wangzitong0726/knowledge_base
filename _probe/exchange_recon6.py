# -*- coding: utf-8 -*-
"""交易所侦察 · 第六轮：只攻上交所（8/15 家是沪市，值得再试一次）"""
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

print("=" * 78)
# 主 app JS 里找公告接口
for js in ["http://www.sse.com.cn/xhtml/js/sse_full.js?v=3.8.1_20260901",
           "http://www.sse.com.cn/xhtml/js/app/sse_menufun_2021.js"]:
    try:
        t = f.get_text(js, headers=UA, timeout=60, retries=1)
        print(f"\n{js.rsplit('/',1)[-1]}  {len(t):,} 字符")
        for pat in [r"(query[A-Za-z]*Bulletin[A-Za-z]*\.do)", r"(COMMON_SSE[A-Z_0-9]{6,})",
                    r"sqlId\s*[:=]\s*['\"]([A-Za-z_0-9]+)"]:
            hits = sorted(set(re.findall(pat, t)))
            if hits:
                print(f"   {pat[:30]}… → {hits[:10]}")
    except FetchError as e:
        print(f"{js.rsplit('/',1)[-1]} FAIL {str(e)[:80]}")

# 直接请求通知页，看它内联脚本里的接口
print("\n--- 定期报告页内联脚本 ---")
try:
    h = f.get_text("http://www.sse.com.cn/disclosure/listedinfo/regular/", headers=UA,
                   timeout=45, retries=1)
    for pat in [r"query[A-Za-z]+\.do", r"COMMON_SSE[A-Z_0-9]+", r"sqlId"]:
        hits = sorted(set(re.findall(pat, h)))
        print(f"   {pat[:22]:<24} → {hits[:8]}")
except FetchError as e:
    print("  FAIL", str(e)[:100])

# 试 SSE 的「上市公司公告」新版接口族
print("\n--- 试接口族 ---")
for label, url in [
    ("commonQuery + 公告sqlId(推测)",
     "http://query.sse.com.cn/commonQuery.do?sqlId=COMMON_SSE_CP_GPJCTPZ_GG_L"
     "&isPagination=true&pageHelp.pageSize=25&pageHelp.pageNo=1&SECURITY_CODE=688008"),
    ("announcement 页接口",
     "http://query.sse.com.cn/security/stock/queryCompanyAnnouncementNew.do"
     "?jsonCallBack=jsonpCallback&isPagination=true&productId=688008"
     "&beginDate=2024-01-01&endDate=2026-10-04&pageHelp.pageSize=25&pageHelp.pageNo=1"),
    ("无参数探测(看默认返回)",
     "http://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"),
]:
    try:
        raw, _ = f.get(url, headers={**UA, "Referer": "http://www.sse.com.cn/disclosure/listedinfo/regular/",
                                     "Accept": "*/*"}, timeout=45, retries=1)
        t = raw.decode("utf-8", "replace")
        print(f"  [{label}] {len(raw):,}B  URL={len(re.findall(chr(34)+'URL'+chr(34), t))}")
        if len(raw) < 1200:
            print("     ", t[:220].replace("\n", " "))
    except FetchError as e:
        print(f"  [{label}] FAIL {str(e)[:80]}")
print("=" * 78)

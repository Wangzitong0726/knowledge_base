# -*- coding: utf-8 -*-
"""
交易所侦察 · 第二轮：找**真正的取数接口**

第一轮只证明页面可达（SSE 27KB / SZSE 31KB 都是 JS 壳，pdf=0）。
这一轮直接打各自的 API，看到底能不能拿到「年报全文的 PDF 直链」。

重点三个：
  · 上交所——列表是 JS 渲染的，数据来自 query.sse.com.cn
  · 深交所——annList 是 POST JSON
  · 韩国 DART——法定电子公示，三星/海力士的年报（사업보고서）原文在这里
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


def show(label, raw, pat=None, limit=300):
    t = raw.decode("utf-8", "replace")
    print(f"\n--- {label}  ({len(raw):,}B) ---")
    if pat:
        for m in re.findall(pat, t)[:8]:
            print("   ", m)
    print("   ", t[:limit].replace("\n", " ")[:limit])


# ============ 1. 上交所 ============
print("=" * 78)
print("【上交所】")
try:
    raw, _ = f.get(
        "http://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"
        "?jsonCallBack=jsonpCallback&isPagination=true&productId=688008"
        "&reportType2=DQBG&reportType=ALL&beginDate=2024-01-01&endDate=2026-10-04"
        "&pageHelp.pageSize=10&pageHelp.pageNo=1",
        headers={**UA, "Referer": "http://www.sse.com.cn/"}, timeout=45, retries=2)
    show("SSE 公告检索API", raw, pat=r'"URL":"([^"]+)"')
except FetchError as e:
    print("  FAIL", str(e)[:120])

# 上交所还有个 zqpz/announcement 接口
try:
    raw, _ = f.get(
        "http://query.sse.com.cn/commonQuery.do"
        "?sqlId=COMMON_SSE_ZQPZ_SSGG_P_ZLXXPL_GGLB_L"
        "&isPagination=true&pageHelp.pageSize=10&pageHelp.pageNo=1"
        "&START_DATE=2024-01-01&END_DATE=2026-10-04&SECURITY_CODE=688008",
        headers={**UA, "Referer": "http://www.sse.com.cn/"}, timeout=45, retries=2)
    show("SSE commonQuery", raw)
except FetchError as e:
    print("  FAIL", str(e)[:120])

# ============ 2. 深交所 ============
print("\n" + "=" * 78)
print("【深交所】")
try:
    body = json.dumps({
        "seDate": ["2024-01-01", "2026-10-04"],
        "channelCode": ["fixed_disc"],
        "pageSize": 10, "pageNum": 1,
        "stock": ["301308"],
    }).encode()
    raw, _ = f.get("http://www.szse.cn/api/disc/announcement/annList",
                   data=body,
                   headers={**UA, "Content-Type": "application/json",
                            "Referer": "http://www.szse.cn/disclosure/listed/fixed/index.html",
                            "X-Request-Type": "ajax", "X-Requested-With": "XMLHttpRequest"},
                   timeout=45, retries=2)
    show("SZSE annList", raw, pat=r'"attachPath":"([^"]+)"')
except FetchError as e:
    print("  FAIL", str(e)[:120])

# ============ 3. 韩国 DART ============
print("\n" + "=" * 78)
print("【韩国 DART】（法定电子公示——三星/海力士年报原文）")
for label, url, hdr, data in [
    ("DART 搜索(三星전자 定期报告)",
     "https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90",
     {"Referer": "https://dart.fss.or.kr/"}, None),
    ("DART 公司list API",
     "https://dart.fss.or.kr/dsab007/searchCorpList.ax", {}, None),
]:
    try:
        raw, _ = f.get(url, headers={**UA, **hdr}, data=data, timeout=45, retries=2)
        show(label, raw, pat=r'(rcpNo=\d+|viewer\.do\?[^"\']{0,80})')
    except FetchError as e:
        print(f"\n--- {label} ---\n  FAIL {str(e)[:120]}")

# ============ 4. KIND ============
print("\n" + "=" * 78)
print("【韩国交易所 KIND】")
try:
    raw, _ = f.get("http://kind.krx.co.kr/disclosure/searchtotalinfo.do",
                   headers={**UA, "Referer": "http://kind.krx.co.kr/"},
                   timeout=45, retries=2)
    show("KIND searchtotalinfo", raw)
except FetchError as e:
    print("  FAIL", str(e)[:120])
print("=" * 78)

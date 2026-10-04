# -*- coding: utf-8 -*-
"""
交易所侦察 · 第三轮：把「能用的」坐实，把「不能用的」证伪

第二轮结论：
  · 深交所 annList **返回真 PDF 直链** → 可用，本轮验证能否真下到全文
  · 上交所 queryCompanyBulletinNew 返回 data:[] → 参数不全（缺 securityType），本轮补全
  · DART / KIND 返回 HTML 壳 → 数据在 POST 接口后面，本轮试真接口
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

# ============ 1. 上交所（补 securityType） ============
print("=" * 78)
print("【上交所】补 securityType 后重试")
for sec_type in ["0101%2C120100%2C020100%2C020200%2C120200", "0101,120100,020100,020200,120200"]:
    try:
        raw, _ = f.get(
            "http://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"
            "?jsonCallBack=jsonpCallback&isPagination=true&productId=688008"
            f"&securityType={sec_type}"
            "&reportType2=DQBG&reportType=ALL&beginDate=2024-01-01&endDate=2026-10-04"
            "&pageHelp.pageSize=25&pageHelp.pageNo=1&pageHelp.beginPage=1"
            "&pageHelp.cacheSize=1&pageHelp.endPage=1",
            headers={**UA, "Referer": "http://www.sse.com.cn/"}, timeout=45, retries=2)
        t = raw.decode("utf-8", "replace")
        cnt = len(re.findall(r'"URL"', t))
        print(f"  securityType={sec_type[:20]}... → {len(raw):,}B, URL字段 {cnt} 个")
        for u in re.findall(r'"URL":"([^"]+)"', t)[:4]:
            print("     ", u)
        for ti in re.findall(r'"TITLE":"([^"]{0,60})"', t)[:4]:
            print("     标题:", ti)
    except FetchError as e:
        print("  FAIL", str(e)[:110])

# ============ 2. 深交所：真下一份年报全文验证 ============
print("\n" + "=" * 78)
print("【深交所】验证真能下到年报全文（不只直链）")
try:
    body = json.dumps({
        "seDate": ["2024-01-01", "2026-10-04"],
        "channelCode": ["fixed_disc"],
        "pageSize": 30, "pageNum": 1,
        "stock": ["301308"],
    }).encode()
    raw, _ = f.get("http://www.szse.cn/api/disc/announcement/annList", data=body,
                   headers={**UA, "Content-Type": "application/json",
                            "Referer": "http://www.szse.cn/disclosure/listed/fixed/index.html",
                            "X-Request-Type": "ajax", "X-Requested-With": "XMLHttpRequest"},
                   timeout=45, retries=2)
    js = json.loads(raw.decode("utf-8"))
    rows = js.get("data") or []
    print(f"  江波龙 定期报告 {len(rows)} 条：")
    for r in rows[:12]:
        print(f"     {r['publishTime'][:10]}  {r['attachSize']:>6}KB  {r['title'][:44]}")
    # 挑一份「半年度报告」正文（非摘要）真下
    pick = next((r for r in rows
                 if "半年度报告" in r["title"] and "摘要" not in r["title"]), None) or rows[0]
    url = "http://www.szse.cn" + pick["attachPath"]
    dest = Path(__file__).resolve().parent / "_szse_test.pdf"
    raw, hdr = f.get(url, headers=UA, timeout=90)
    dest.write_bytes(raw)
    head = raw[:8]
    print(f"\n  下载 {pick['title'][:40]}")
    print(f"  → {len(raw):,}B  Content-Type={hdr.get('Content-Type','')[:30]}  魔术字={head}")
    print(f"  写入 {dest.name}")
except Exception as e:
    print("  FAIL", type(e).__name__, str(e)[:140])

# ============ 3. 韩国 DART 真接口 ============
print("\n" + "=" * 78)
print("【韩国 DART】试真数据接口")
for label, url, data, hdr in [
    ("DART detailSearch.ax",
     "https://dart.fss.or.kr/dsab007/detailSearch.ax",
     "currentPage=1&maxResults=15&maxLinks=10&sort=date&seriesKey=&textCrpNm=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90&reportName="
     "&reportNamePopup=&startDate=2024-01-01&endDate=2026-10-04&finalReport=recent&publicType=A001&govBody=&bgnDate="
     "&businessCode=&reportNameDetail=&reportNameDetailPopup=&mainReport=&mainReportPopup=".encode(),
     {"Referer": "https://dart.fss.or.kr/dsab007/main.do",
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
      "X-Requested-With": "XMLHttpRequest"}),
]:
    try:
        raw, _ = f.get(url, data=data, headers={**UA, **hdr}, timeout=45, retries=2)
        t = raw.decode("utf-8", "replace")
        print(f"\n--- {label} ({len(raw):,}B) ---")
        print("  rcpNo 命中:", len(re.findall(r"rcpNo=\d+", t)))
        print("  ", t[:400].replace("\n", " "))
    except FetchError as e:
        print(f"\n--- {label} ---\n  FAIL {str(e)[:110]}")

# ============ 4. KIND 真接口 ============
print("\n" + "=" * 78)
print("【韩国 KIND】试真数据接口")
try:
    raw, _ = f.get("http://kind.krx.co.kr/disclosure/searchtotalinfo.do",
                   data=("method=searchTotalInfoSub&currentPageSize=15&pageIndex=1&orderMode=0&orderStat=D"
                         "&reportName=&fromData=20240101&toData=20261004"
                         "&searchCodeType=&searchCorpName=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90"
                         "&repIsuSrtCd=&businessCode=").encode(),
                   headers={**UA, "Referer": "http://kind.krx.co.kr/disclosure/searchtotalinfo.do",
                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                            "X-Requested-With": "XMLHttpRequest"},
                   timeout=45, retries=2)
    t = raw.decode("utf-8", "replace")
    print(f"  {len(raw):,}B  含 corpName={len(re.findall('corpName', t))} 处")
    print("  ", t[:400].replace("\n", " "))
except FetchError as e:
    print("  FAIL", str(e)[:110])
print("=" * 78)

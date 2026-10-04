# -*- coding: utf-8 -*-
"""
交易所侦察 · 第五轮（收口）

  · 上交所：sqlId 就写在它自己的 table_config.js 里 —— 去读，不再猜
  · 深交所：PDF 403 → 试 host 变体（disc.szse.cn / https）
  · DART：上一轮表格是空的，补 finalReport / publicType 参数
"""
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

# ---------- 1. 上交所：从 table_config.js 里挖 sqlId ----------
print("=" * 78)
print("【上交所】读 table_config.js 找 sqlId")
for js in ["http://www.sse.com.cn/xhtml/js/common/table_config.js?v=V3.7.9",
           "http://www.sse.com.cn/xhtml/js/common/common_table.js?v=V3.6.1_20250626"]:
    try:
        t = f.get_text(js, headers=UA, timeout=45, retries=1)
        ids = sorted(set(re.findall(r"(COMMON_SSE[A-Z_0-9]+)", t)))
        print(f"  {js.rsplit('/',1)[-1]:<28} {len(t):>7,} 字符  sqlId {len(ids)} 个")
        for i in ids:
            if any(k in i for k in ("GP", "CP", "ZLXX", "GG")):
                print("      ", i)
    except FetchError as e:
        print(f"  {js.rsplit('/',1)[-1]} FAIL {str(e)[:80]}")

# ---------- 2. 深交所 PDF：试 host 变体 ----------
print("\n" + "=" * 78)
print("【深交所】PDF host 变体")
P = "/disc/disk03/finalpage/2026-08-11/35b248b6-6b97-4fe1-92f5-15a610d4e19c.PDF"
for host in ["http://disc.szse.cn" + P, "https://www.szse.cn" + P,
             "https://disc.szse.cn" + P, "http://www.szse.cn" + P]:
    try:
        raw, h = f.get(host, headers={**UA, "Accept": "*/*", "Accept-Encoding": "identity",
                                      "Referer": "http://www.szse.cn/disclosure/listed/fixed/index.html"},
                       timeout=90, retries=1)
        print(f"  OK  {host[:34]:<36} {len(raw):,}B 魔术字={raw[:5]}")
        (Path(__file__).resolve().parent / "_szse_test.pdf").write_bytes(raw)
        break
    except FetchError as e:
        print(f"  ✗   {host[:34]:<36} {str(e)[-60:]}")

# ---------- 3. DART 补参数 ----------
print("\n" + "=" * 78)
print("【韩国 DART】补参数重试")
for label, body in [
    ("finalReport=recent+publicType=A001",
     "currentPage=1&maxResults=15&maxLinks=10&sort=date&seriesKey=&textCrpNm=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90"
     "&reportName=&startDate=2024-01-01&endDate=2026-10-04&finalReport=recent&publicType=A001"
     "&govBody=&bgnDate=&businessCode=&reportNameDetail=&mainReport="),
    ("全套必填",
     "currentPage=1&maxResults=15&maxLinks=10&sort=date&seriesKey=&textCrpNm=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90"
     "&reportName=&startDate=2024-01-01&endDate=2026-10-04&finalReport=&publicType="
     "&govBody=&bgnDate=&businessCode=&reportNameDetail=&mainReport=&textPresenterNm="),
]:
    try:
        raw, _ = f.get("https://dart.fss.or.kr/dsab007/detailSearch.ax", data=body.encode(),
                       headers={**UA, "Referer": "https://dart.fss.or.kr/dsab007/main.do?option=corp",
                                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                "X-Requested-With": "XMLHttpRequest"}, timeout=45, retries=1)
        t = raw.decode("utf-8", "replace")
        rcp = re.findall(r"rcpNo=(\d+)", t)
        corp = re.findall(r"corpName[^>]*>([^<]{2,30})<", t)
        print(f"  [{label}] {len(raw):,}B  rcpNo={len(rcp)} 公司={corp[:3]}")
        if len(raw) > 3000:
            print("     片段:", re.sub(r"\s+", " ", t)[:260])
    except FetchError as e:
        print(f"  [{label}] FAIL {str(e)[:90]}")
print("=" * 78)

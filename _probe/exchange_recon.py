# -*- coding: utf-8 -*-
"""
交易所官网可达性 + 结构化程度侦察

目的：回答「作业要求从**交易所网站**下年报，我是不是都找过了」。

方法：对每个候选入口实抓，报 (状态, 字节, 是否含季度报告线索)。
只报事实，不做判断——判断写在 _probe/exchange_recon.md。
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

TARGETS = [
    # ---- A 股：交易所自己的站 ----
    ("上交所·定期报告列表", "http://www.sse.com.cn/disclosure/listedinfo/regular/"),
    ("上交所·公告检索API", "http://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"
                            "?jsonCallBack=jsonpCallback&isPagination=true&productId=688008"
                            "&reportType2=DQBG&reportType=ALL&beginDate=2024-01-01"
                            "&endDate=2026-10-04&pageHelp.pageSize=10&pageHelp.pageNo=1"),
    ("深交所·定期报告", "http://www.szse.cn/disclosure/listed/fixed/index.html"),
    ("北交所·公告", "https://www.bse.cn/disclosure/announcement.html"),
    # ---- 韩国：交易所 / 法定公示 ----
    ("韩国交易所 KIND 首页", "http://kind.krx.co.kr/"),
    ("KIND·定期报告检索", "http://kind.krx.co.kr/disclosure/searchtotalinfo.do"),
    ("韩国 DART 首页", "https://dart.fss.or.kr/"),
    ("DART 英文站", "https://english.dart.fss.or.kr/"),
    ("DART 定期报告检索", "https://dart.fss.or.kr/dsab007/main.do"),
    # ---- 日本：东交所 + 铠侠 ----
    ("东交所 JPX 首页", "https://www.jpx.co.jp/"),
    ("铠侠 IR", "https://www.kioxia-holdings.com/en-jp/ir.html"),
    # ---- 台湾：复验是否真的下不了（决策二） ----
    ("台湾 MOPS 公开信息观测站", "https://mops.twse.com.tw/mops/web/index"),
]

print("=" * 78)
for label, url in TARGETS:
    try:
        raw, hdr = f.get(url, timeout=45, retries=2)
        txt = raw.decode("utf-8", "replace")
        n = len(raw)
        ct = hdr.get("Content-Type", "")[:40]
        # 找线索：PDF 直链数、是否出现「年度报告」/「사업보고서」/「Annual Report」
        pdfs = len(re.findall(r"\.pdf", txt, re.I))
        hit = []
        if re.search(r"年度报告|年报", txt):
            hit.append("含『年度报告』")
        if re.search(r"사업보고서", txt):
            hit.append("含『사업보고서』(韩·年报)")
        if re.search(r"Annual Report", txt, re.I):
            hit.append("含 Annual Report")
        print(f"[OK ] {label:<24} {n:>9,}B  pdf={pdfs:<4} {ct}")
        if hit:
            print(f"        ↳ {', '.join(hit)}")
    except FetchError as e:
        print(f"[FAIL] {label:<24} {str(e)[:90]}")
    except Exception as e:
        print(f"[ERR ] {label:<24} {type(e).__name__}: {str(e)[:70]}")
print("=" * 78)

# -*- coding: utf-8 -*-
"""
库 A · A 股产业链年报/半年报（巨潮资讯网）

参数全部照抄作业二已验证的那份（`D:\\ai_homework2\\scripts\\fetch_cninfo.py`），
以及本次开工前端点复验（`_probe/verify_endpoints.md`）。实测结论：

  - 必须带 UA，否则 403；带 X-Requested-With 模拟 ajax
  - pageSize 服务端硬限 30，传大无效，必须翻页
  - category 参数实测可把范围收窄到 年报+半年报，且返回干净
  - orgId 必须从接口取，不可臆造（老股 gssh/gssz、新股纯数字、北交所 nssc）

**口径决定（明写，不静默）**：只收**正文**，不收「摘要」。
摘要与正文内容重复、只是压缩版，收进来会让同一事实在索引里出现两份，
既浪费算力又会让检索结果看起来「证据很多」而实际是同一份。
"""
import re
import time
from pathlib import Path

from .common import Fetcher, FetchError

API = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
PDF_BASE = "http://static.cninfo.com.cn/"

# 15 家，orgId 来自 `_probe/cninfo_orgids.txt`（当时逐家实测取得）
# 北京君正未命中精确名，待另取（见方案 §2）
COMPANIES = [
    ("澜起科技", "688008", "9900039002"),
    ("兆易创新", "603986", "9900026561"),
    ("江波龙", "301308", "9900048787"),
    ("佰维存储", "688525", "9900047412"),
    ("德明利", "001309", "nssc1000644"),
    ("东芯股份", "688110", "nssc1000767"),
    ("普冉股份", "688766", "nssc1000720"),
    ("聚辰股份", "688123", "9900039009"),
    ("香农芯创", "300475", "9900023854"),
    ("深科技", "000021", "gssz0000021"),
    ("太极实业", "600667", "gssh0600667"),
    ("雅克科技", "002409", "9900012610"),
    ("鼎龙股份", "300054", "9900010037"),
    ("安集科技", "688019", "9900038987"),
    ("兴森科技", "002436", "9900012934"),
]

CATEGORY = "category_ndbg_szsh;category_bndbg_szsh"   # 年报 + 半年报（实测有效）


def board_of(code):
    """板块 → (column, plate)。6 开头是沪市，0/3 开头是深市。"""
    return ("sse", "sh") if code.startswith("6") else ("szse", "sz")


def parse_report(title):
    """从标题判断报告类型与所属年度。返回 (类型, 年度) 或 (None, None)。

    ⚠️ 顺序要紧：**「半年度报告」里含「年度报告」**，先判「年度报告」
    会把所有半年报误判成年报。实测踩过（自测：澜起科技2026年半年度报告 → 年报）。
    这类子串包含导致的误判不报错，只会让元数据整体错位。
    """
    m = re.search(r"(\d{4})\s*年", title)
    year = int(m.group(1)) if m else None
    if "半年度报告" in title:
        return "半年报", year
    if "年度报告" in title:
        return "年报", year
    return None, year


def query(f, code, orgid, start, end, max_pages=10):
    """翻页拉取一家公司的年报/半年报公告。"""
    from .common import BROWSER_UAS
    import urllib.parse
    column, plate = board_of(code)
    out, page = [], 1
    while page <= max_pages:
        params = {
            "tabName": "fulltext", "pageSize": 30, "pageNum": page,
            "column": column, "plate": plate,
            "stock": f"{code},{orgid}",
            "searchkey": "", "secid": "",
            "category": CATEGORY, "trade": "",
            "seDate": f"{start}~{end}",
            "sortName": "", "sortType": "", "isHLtitle": "true",
        }
        body = urllib.parse.urlencode(params).encode()
        raw, _ = f.get(API, data=body, headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
        })
        import json
        d = json.loads(raw.decode("utf-8"))
        anns = d.get("announcements") or []
        out.extend(anns)
        total = d.get("totalRecordNum") or 0
        if page * 30 >= total or not anns:
            break
        page += 1
        time.sleep(f.delay)
    return out


def run(f, outdir, start="2024-01-01", end=None, skip_summary=True, only_year=None):
    """抓全部公司。返回抓到的记录列表。"""
    end = end or time.strftime("%Y-%m-%d")
    outdir = Path(outdir)
    got = []
    print(f"\n=== 库 A · 巨潮 A 股年报/半年报  {start} ~ {end} ===")

    for i, (name, code, orgid) in enumerate(COMPANIES, 1):
        print(f"[{i}/{len(COMPANIES)}] {name} {code}")
        try:
            anns = query(f, code, orgid, start, end)
        except FetchError as e:
            f.fail("cninfo", f"{name} {code} 列表", e)
            continue

        picked = 0
        for a in anns:
            title = (a.get("announcementTitle") or "").replace("<em>", "").replace("</em>", "")
            kind, year = parse_report(title)
            if kind is None:
                continue
            if skip_summary and "摘要" in title:
                continue
            if only_year and year not in only_year:
                continue
            adj = a.get("adjunctUrl")
            if not adj:
                continue
            url = PDF_BASE + adj
            date = time.strftime("%Y-%m-%d", time.localtime(a["announcementTime"] / 1000)) \
                if a.get("announcementTime") else ""
            fn = re.sub(r'[\\/:*?"<>|]', "_", f"{code}_{date}_{title}")[:80] + ".pdf"
            try:
                f.download(url, outdir / name / fn, source="cninfo",
                           company=name, title=title, date=date,
                           # adjunctSize 是 KB 取整，给 2KB 容差，别为几百字节的
                           # 舍入差误杀正常文件。真截断由 Content-Length 抓。
                           expect_size=(a.get("adjunctSize") or 0) * 1024 or None,
                           size_tolerance=2048)
                picked += 1
            except FetchError as e:
                f.fail("cninfo", f"{name} {title}", e)
        print(f"      → 本家取到 {picked} 份正文")
        got.append((name, picked))
        time.sleep(f.delay)

    print("\n--- 库 A 汇总 ---")
    for name, n in got:
        flag = "  !! 0 份" if n == 0 else ""
        print(f"  {name:8s} {n} 份{flag}")
    return got

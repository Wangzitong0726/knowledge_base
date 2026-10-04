# -*- coding: utf-8 -*-
"""
库 A · 深交所**官网**年报/半年报全文

为什么单独做这一个源：作业要求「从**交易所网站**下载年报/半年报全文」。
巨潮资讯网虽是证监会指定信息披露网站，域名毕竟不是交易所的。
实测（`_probe/exchange_recon*.py`，共 6 轮）结论：

  ✅ 深交所官网 **完全可用** —— 列表与全文都能取
  ❌ 上交所官网 定期报告接口**未公开文档化**：页面 28 个 script 块里
     没有 iframe、没有内联 URL、sse_full.js(360KB) 里也没有 sqlId，
     数据源不是静态可分析的 → 沪市仍走巨潮（见 cninfo.py 说明）
  ❌ 台湾 MOPS 证书链失败（决策二，已放弃）
  ✅ 美 SEC EDGAR 本身就是法定源（见 sec_edgar.py）

两个必须记住的坑（都是实测踩出来的）：
  1. 列表接口是 **POST JSON** 到 `www.szse.cn/api/disc/announcement/annList`
  2. **PDF 的 host 是 `disc.szse.cn`，不是 `www.szse.cn`** ——
     用 www 下会 403 Forbidden（补 Referer 也没用，换 host 才对）
"""
import json
import re
import time
from pathlib import Path

from .cninfo import parse_report          # 复用同一套「年报/半年报」判定（含子串顺序坑）
from .common import Fetcher, FetchError

LIST_API = "http://www.szse.cn/api/disc/announcement/annList"
PDF_HOST = "http://disc.szse.cn"          # ← 不是 www.szse.cn

# 深市 7 家（0/3 开头）。沪市 8 家见 cninfo.py。
COMPANIES = [
    ("江波龙",   "301308"),
    ("德明利",   "001309"),
    ("香农芯创", "300475"),
    ("深科技",   "000021"),
    ("雅克科技", "002409"),
    ("鼎龙股份", "300054"),
    ("兴森科技", "002436"),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
      "Referer": "http://www.szse.cn/disclosure/listed/fixed/index.html",
      "Content-Type": "application/json",
      "X-Request-Type": "ajax",
      "X-Requested-With": "XMLHttpRequest"}


def query(f, code, start, end, max_pages=6):
    """POST 翻页取一家公司的定期报告公告。"""
    out, page = [], 1
    while page <= max_pages:
        body = json.dumps({
            "seDate": [start, end],
            "channelCode": ["fixed_disc"],        # 定期报告频道
            "pageSize": 30, "pageNum": page,
            "stock": [code],
        }).encode()
        raw, _ = f.get(LIST_API, data=body, headers=UA)
        d = json.loads(raw.decode("utf-8"))
        rows = d.get("data") or []
        out.extend(rows)
        if len(rows) < 30:
            break
        page += 1
        time.sleep(f.delay)
    return out


def run(f, outdir, start="2024-01-01", end=None, skip_summary=True):
    end = end or time.strftime("%Y-%m-%d")
    outdir = Path(outdir)
    got = []
    print(f"\n=== 库 A · 深交所官网 定期报告  {start} ~ {end} ===")

    for i, (name, code) in enumerate(COMPANIES, 1):
        print(f"[{i}/{len(COMPANIES)}] {name} {code}")
        try:
            rows = query(f, code, start, end)
        except Exception as e:
            f.fail("szse", f"{name} {code} 列表", e)
            continue

        picked = 0
        for a in rows:
            title = a.get("title") or ""
            kind, year = parse_report(title)
            if kind is None:
                continue                      # 排除季报等
            if skip_summary and "摘要" in title:
                continue
            path = a.get("attachPath")
            if not path:
                continue
            url = PDF_HOST + path
            date = (a.get("publishTime") or "")[:10]
            fn = re.sub(r'[\\/:*?"<>|]', "_", f"{code}_{date}_{title}")[:80] + ".PDF"
            try:
                f.download(url, outdir / name / fn, source="szse",
                           company=name, title=title, date=date, headers=UA,
                           # attachSize 是 KB 取整，给 2KB 容差
                           expect_size=(a.get("attachSize") or 0) * 1024 or None,
                           size_tolerance=2048, timeout=180)
                picked += 1
            except FetchError as e:
                f.fail("szse", f"{name} {title}", e)
        print(f"      → 本家取到 {picked} 份正文")
        got.append((name, picked))
        time.sleep(f.delay)

    print("\n--- 深交所官网 汇总 ---")
    for name, n in got:
        print(f"  {name:8s} {n} 份{'  !! 0 份' if n == 0 else ''}")
    return got

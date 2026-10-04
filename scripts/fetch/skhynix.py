# -*- coding: utf-8 -*-
"""
库 A · SK 海力士 审计报告/财报（SK hynix IR API）

实测（`_probe/verify_endpoints.md`）：
  - 官网 www.skhynix.com 的 IR 页面全是 JS 渲染，前几轮探到的路径全是 404
  - 真正的数据源是 Nuxt 应用里写死的 API 基址：**https://homeapi.skhynix.com**
  - `GET /board/list?bcode=&pageSize=&lang=ENG&pageNo=` 返回 JSON
  - 信封字段：`cdnUrl` `filePath` `list` `total` `urlPath`
  - **坑**：文件不在 `fileUrl1`，而在 `fileUrl4`/`fileUrl5`——
    必须遍历 fileUrl1..5，只读 1 号会一份都拿不到（且不报错，只是空）
  - 下载地址 = `cdnUrl` + `fileUrlN`，实测返回 `%PDF`，1.23MB

bcode：101 = Audit(Review) Report（年报正文）/ 105 = Earnings Release / 102 = Disclosure
"""
import re
from pathlib import Path

from .common import Fetcher, FetchError

API = "https://homeapi.skhynix.com/board/list"
COMPANY = "SK 海力士"
HEADERS = {"Accept": "application/json",
           "Referer": "https://www.skhynix.com/",
           "Origin": "https://www.skhynix.com"}

BOARDS = [(101, "年报/审计报告"), (105, "业绩发布")]


def fetch_board(f, bcode, page_size=100):
    """取一个板块的全部条目。"""
    import urllib.parse
    q = urllib.parse.urlencode({"bcode": bcode, "pageSize": page_size,
                                "lang": "ENG", "pageNo": 1})
    raw, _ = f.get(f"{API}?{q}", headers=HEADERS, timeout=60)
    import json
    js = json.loads(raw.decode("utf-8"))
    cdn = js.get("cdnUrl") or js.get("filePath") or ""
    items = js.get("list") or []
    return cdn, items, js.get("total")


def files_of(item):
    """把条目上 fileUrl1..5 / fileName1..5 配对抽出来。

    必须遍历 1..5 —— 实打实的坑：文件常常挂在第 4、5 号槽位。
    """
    out = []
    for i in range(1, 6):
        u = item.get(f"fileUrl{i}")
        if not u:
            continue
        out.append({
            "url_path": u,
            "name": item.get(f"fileName{i}") or u.rsplit("/", 1)[-1],
            "size": item.get(f"fileSize{i}") or "",
        })
    return out


def run(f, outdir, min_year=2024):
    outdir = Path(outdir)
    print(f"\n=== 库 A · {COMPANY} IR API ===")
    got = []
    for bcode, label in BOARDS:
        try:
            cdn, items, total = fetch_board(f, bcode)
        except (FetchError, Exception) as e:
            f.fail("skhynix", f"bcode={bcode} {label}", e)
            continue
        print(f"  bcode={bcode} {label}：total={total} 取到 {len(items)} 条，cdn={cdn[:46]}...")

        for it in items:
            title = (it.get("title") or "").strip()
            disp = (it.get("displayDate") or "").strip()
            m = re.search(r"(20\d{2})", disp) or re.search(r"(20\d{2})", title)
            year = int(m.group(1)) if m else 0
            if year and year < min_year:
                continue
            fl = files_of(it)
            if not fl:
                print(f"      ! 「{title[:40]}」无附件（可能是纯网页内容）")
                continue
            for x in fl:
                url = cdn + x["url_path"]
                name = re.sub(r'[\\/:*?"<>|]', "_", x["name"])[:80]
                if not name.lower().endswith(".pdf"):
                    name += ".pdf"
                try:
                    f.download(url, outdir / COMPANY / name, source="skhynix",
                               company=COMPANY, title=title, date=disp)
                    got.append((title, name))
                except FetchError as e:
                    f.fail("skhynix", f"{title[:40]} / {name}", e)
    print(f"      → 取到 {len(got)} 份")
    return got

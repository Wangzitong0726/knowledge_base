# -*- coding: utf-8 -*-
"""
库 B · 规则库：BIS 最终规则正文 + CFR 法规正文

三个来源，分工不同，**不能混用**：

  · **Federal Register**（公告）= 规则**发布时的全文**，含前言说明（讨论、理由、影响评估）。
    判定「某条管制是哪份规则加的、什么时候生效」必须用它。
    实测：89 FR 96790 的 raw_text 0.31MB，HBM=85 3A090=231 DRAM=23。

  · **govinfo CFR 年度版**（法规）= **整理后的现行条文**，只有条文、没有前言。
    论文要**逐字引用条文**时用它。
    实测：6.96MB，3A090=71 **DRAM=0** HBM=10。

    ⚠️ 这两个数字的差别是要写进论文的：**FR 前言里 DRAM 出现 23 次，CFR 条文里 0 次**。
    ——管制条文本身不按「DRAM 这个品类」划线，这正是论证的支点。

  · **eCFR versioner API** = 条文的**时点版本**，用来做版本对照（课程 p50 的「版本陷阱」）。
    实测：`/api/versioner/v1/full/{YYYY-MM-DD}/title-15.xml?part=774`，
    必须 `Accept: application/xml` + `Accept-Encoding: gzip`，且**要正确解压**。
    （我曾因没解 gzip 得出「eCFR 含 3A090=False」的假结论——工具错，不是站点错。）

6 篇提到 HBM 的规则由 `_probe/bis_rules_scanned.json` 全量扫描 54 篇得出：
**抽查不等于全查**（我曾只扫最新 25 篇，得出「只有 1 篇」，漏掉最关键的 2024-12-05）。
"""
import json
from pathlib import Path

from .common import Fetcher, FetchError

# 6 篇提到 HBM 的规则（实测，非记忆）。docnum 取自各自 FR URL 的末段。
HBM_RULES = [
    ("2024-28423", "2024-12-04", "89 FR 96095", "Public Briefing on Changes to Advanced Computing"),
    ("2024-28270", "2024-12-05", "89 FR 96790", "Foreign-Produced Direct Product Rule Additions（首次纳入 HBM）"),
    ("2025-00636", "2025-01-15", "90 FR 4544", "Framework for Artificial Intelligence Diffusion"),
    ("2025-00711", "2025-01-16", "90 FR 5298", "Implementation of Additional Due Diligence Measures"),
    ("2025-02655", "2025-02-14", "90 FR 9604", "Implementation of Additional Due Diligence Measures（二）"),
    ("2026-00789", "2026-01-15", "91 FR 1684", "Revision to License Review Policy for Advanced Computing"),
]

FR_API = "https://www.federalregister.gov/api/v1/documents/{}.json"
FR_FIELDS = ("fields[]=title&fields[]=publication_date&fields[]=effective_on"
             "&fields[]=raw_text_url&fields[]=html_url&fields[]=citation"
             "&fields[]=document_number&fields[]=abstract")

GOVINFO_CFR = ("https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/"
               "CFR-2025-title15-vol2.xml")
ECFR_FULL = "https://www.ecfr.gov/api/versioner/v1/full/{date}/title-15.xml?part=774"


def run_federal_register(f, outdir):
    """取 6 篇规则的正文 + 元数据。"""
    outdir = Path(outdir)
    print(f"\n=== 库 B · Federal Register（{len(HBM_RULES)} 篇提到 HBM 的规则）===")
    meta_all = []
    for docnum, date, cite, desc in HBM_RULES:
        print(f"  {cite}  {desc[:44]}")
        try:
            js = f.get_json(FR_API.format(docnum) + "?" + FR_FIELDS)
        except (FetchError, json.JSONDecodeError) as e:
            f.fail("fedreg", f"{cite} 元数据", e)
            continue

        rec = {
            "docnum": docnum, "cite": cite, "date": date,
            "title": js.get("title"),
            "publication_date": js.get("publication_date"),
            "effective_on": js.get("effective_on"),
            "html_url": js.get("html_url"),
            "raw_text_url": js.get("raw_text_url"),
            "abstract": (js.get("abstract") or "")[:400],
        }
        # 「生效日早于发布日」是反常识的，标出来提醒回条文核分段生效
        if rec["effective_on"] and rec["publication_date"] \
                and rec["effective_on"] < rec["publication_date"]:
            rec["_注意"] = "生效日早于发布日 —— 须回条文核分段生效条款，不得直接引用"
        meta_all.append(rec)

        if rec["raw_text_url"]:
            try:
                f.download(rec["raw_text_url"], outdir / f"{cite.replace(' ', '_')}.txt",
                           source="fedreg", company="BIS", title=rec["title"] or cite,
                           date=date, timeout=180)
            except FetchError as e:
                f.fail("fedreg", f"{cite} 正文", e)

    (outdir / "rules_meta.json").write_text(
        json.dumps(meta_all, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"      → 元数据表 {outdir/'rules_meta.json'}")
    return meta_all


def run_cfr(f, outdir):
    """govinfo CFR 年度版（法规正文）+ eCFR 时点版。"""
    outdir = Path(outdir)
    print("\n=== 库 B · CFR 法规正文 ===")
    try:
        f.download(GOVINFO_CFR, outdir / "CFR-2025-title15-vol2.xml", source="govinfo",
                   company="BIS", title="15 CFR 年度版（含 part 774 CCL）",
                   date="2025", timeout=300)
    except FetchError as e:
        f.fail("govinfo", "CFR 年度版", e)

    # eCFR 时点版：做版本对照用。取管制前后两个时点。
    for d, label in [("2024-11-01", "管制前"), ("2026-09-24", "现行")]:
        try:
            f.download(ECFR_FULL.format(date=d),
                       outdir / f"eCFR_774_{d}.xml", source="ecfr",
                       company="BIS", title=f"15 CFR 774 {label}版（{d}）",
                       date=d, timeout=300,
                       headers={"Accept": "application/xml",
                                "Accept-Encoding": "gzip"})
        except FetchError as e:
            f.fail("ecfr", f"774 {label}版 {d}", e)


def run(f, outdir):
    meta = run_federal_register(f, outdir)
    run_cfr(f, outdir)
    return meta

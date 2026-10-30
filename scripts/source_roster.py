# -*- coding: utf-8 -*-
"""来源清单：**公司 × 官方来源 × 份数 × sha256 × 官方 URL** → `outputs/来源清单.md`

为什么非有这一步：老师批改要求「**至少 10 家官方全文来源**」。
逐条凭据本来就在 `data/manifest.jsonl` 里（184 条，条条有 URL、有 sha256），
可那个文件被 `.gitignore` 的 `data/*.jsonl` 挡在仓库外——
**也就是说不交这份表，「有 184 条带 sha256 的官方来源」这句话在仓库里无从查证**。
凡是要交的结论，它的依据必须也在仓库里。

四条纪律：

  ① **sha256 重算，不抄 manifest**。表里写的是**现在重新算出来的**哈希，
     与 manifest 记的对不上就报错——「凭据自述」和「凭据实测」必须分开。
  ② **按唯一文档计数，不按条目计数**。实测：175 条库 A 条目里有 44 条是
     **同一份文件**在巨潮资讯网与深交所各取了一次（sha256 全等，文件字节全等）。
     报 175 就是虚报 44 份。表里两个数都写，差额写明白。
  ③ **公司定期报告全文**与**规则条文**分开列（老师单列「官方全文来源」，
     规则条文另有出处，混在一起会被当成凑数）。
  ④ 官方来源站点写人可核查的名字（巨潮资讯网 / 深交所 / SEC EDGAR …），
     只写 `cninfo` 这种内部代号，读的人核不了。
"""
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.jsonl"
OUT = ROOT / "outputs" / "来源清单.md"

SITE = {
    "cninfo": "巨潮资讯网 cninfo.com.cn",
    "szse": "深圳证券交易所 szse.cn",
    "sec": "美国 SEC EDGAR sec.gov",
    "samsung": "三星电子 IR samsung.com",
    "skhynix": "SK 海力士 IR skhynix.com",
    "fedreg": "美国联邦公报 federalregister.gov",
    "ecfr": "美国联邦法规 eCFR ecfr.gov",
    "govinfo": "美国政府出版局 GovInfo govinfo.gov",
}
LIB_A = ("cninfo", "szse", "sec", "samsung", "skhynix")
LIB_B = ("fedreg", "ecfr", "govinfo")


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load():
    with open(MANIFEST, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def verify(rows):
    """逐条**重算** sha256 与字节数，不信 manifest 的自述。"""
    ok, bad = [], []
    for r in rows:
        p = Path(r["path"])
        if not p.exists():
            bad.append((r, "文件不存在"))
        elif p.stat().st_size != r.get("bytes"):
            bad.append((r, "字节数 %d ≠ manifest 记的 %s" % (p.stat().st_size, r.get("bytes"))))
        elif sha256_of(p) != r.get("sha256"):
            bad.append((r, "sha256 与 manifest 记的不符（文件被换过）"))
        else:
            ok.append(r)
    return ok, bad


def chunk_duplication():
    """块级重复：szse 的切块里有多少与 cninfo 的**逐字相同**。**从库里现算**。

    ⚠️ 这几个数不许写死在模板里。语料一改，写死的数字就变成一句没人会去核的假话——
       本项目栽过的原话是「数字要量在交付的那份文件上，不是量在记忆里」。
       库不在就老实说「未测量」，不猜。
    """
    import sqlite3
    db = ROOT / "knowledge_base" / "index" / "chunks.sqlite"
    if not db.exists():
        return "（块级重复未测量：`knowledge_base/index/chunks.sqlite` 不在）"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    total = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    by = defaultdict(set)
    for s, c, t in con.execute(
            "SELECT source, company, text FROM chunks WHERE source IN ('cninfo','szse')"):
        by[(s, c)].add(hashlib.sha1(t.encode("utf-8")).hexdigest())
    con.close()
    n_szse = sum(len(v) for (s, _c), v in by.items() if s == "szse")
    n_dup = sum(len(v & by.get(("cninfo", c), set()))
                for (s, c), v in by.items() if s == "szse")
    return (f"块级实测（在 `chunks.sqlite` 的 {total:,} 块上现算）：szse 的 **{n_szse:,}** 块里，"
            f"**{n_dup:,}** 块与 cninfo 的对应块**逐字相同**（{100.0 * n_dup / max(n_szse, 1):.1f}%），"
            f"占全库 **{100.0 * n_dup / max(total, 1):.1f}%**。")


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    rows = load()
    ok, bad = verify(rows)
    print("manifest %d 条；重算 sha256 通过 %d 条；不符 %d 条" % (len(rows), len(ok), len(bad)))
    for r, why in bad:
        print("  ！%s  %s" % (Path(r["path"]).name, why))

    A = [r for r in ok if r["source"] in LIB_A]
    B = [r for r in ok if r["source"] in LIB_B]

    # ── 按 sha256 归并成**唯一文档**（同一份文件可能被两个来源各取一次）──
    docs = {}
    for r in A:
        d = docs.setdefault(r["sha256"], {"sha256": r["sha256"], "company": r["company"],
                                          "sources": [], "dates": set(), "paths": [],
                                          "titles": [], "urls": {}})
        d["sources"].append(r["source"])
        d["urls"][r["source"]] = r.get("url") or "—"
        d["dates"].add(r.get("date") or "")
        d["paths"].append(Path(r["path"]).name)
        if r.get("title"):
            d["titles"].append(r["title"])
    dlist = sorted(docs.values(), key=lambda d: (d["company"], sorted(d["dates"])))
    companies = sorted({d["company"] for d in dlist})
    n_multi = sum(1 for d in dlist if len(set(d["sources"])) > 1)

    byc = defaultdict(list)
    for d in dlist:
        byc[d["company"]].append(d)

    L = ["# 来源清单 · 公司官方全文来源与规则条文", "",
         f"- 生成：{time.strftime('%Y-%m-%d %H:%M:%S')}　来源：`data/manifest.jsonl`",
         f"- **sha256 是本脚本现在逐文件重算的**，不是抄 manifest 的："
         f"重算通过 **{len(ok)}/{len(rows)}** 条"
         + ("，全部一致 ✅" if not bad else f"，**{len(bad)} 条不符**（见文末）"),
         f"- 库 A（公司官方披露全文）：条目 {len(A)} 条 → **唯一文档 {len(dlist)} 份 / "
         f"{len(companies)} 家公司**（同一份文件被两个官方来源各取一次的：{n_multi} 份）",
         f"- 库 B（美国出口管制规则条文）：{len(B)} 份",
         "- 两类**分开列**：公司定期报告全文才是「官方全文来源」，"
         "规则条文是管制依据；混在一起列会被当成凑数。", "",
         "---", "",
         "## 一、公司官方全文来源（库 A）", "",
         f"**{len(companies)} 家公司、{len(dlist)} 份唯一文档。**"
         f"老师要求「至少 10 家」，实际 **{len(companies)} 家**。", "",
         "| 公司 | 官方来源 | 唯一文档数 | 覆盖期间 |", "|---|---|---:|---|"]
    for c in companies:
        ds = byc[c]
        srcs = sorted({s for d in ds for s in d["sources"]})
        dates = sorted({x for d in ds for x in d["dates"] if x})
        span = f"{dates[0]} ~ {dates[-1]}（{len(dates)} 个报告期）" if dates else "—"
        L.append("| **%s** | %s | %d | %s |"
                 % (c, "<br>".join(SITE.get(s, s) for s in srcs), len(ds), span))

    L += ["", f"### 逐份明细（{len(dlist)} 份唯一文档）", "",
          "| 公司 | 文件 | 报告期 | 官方来源（URL） | sha256（前 16） |",
          "|---|---|---|---|---|"]
    for d in dlist:
        ds = sorted({x for x in d["dates"] if x})
        src = "<br>".join(f"{SITE.get(s, s).split()[0]} <{u}>"
                          for s, u in sorted(d["urls"].items()))
        L.append("| %s | %s | %s | %s | `%s` |"
                 % (d["company"], d["paths"][0][:40], "、".join(ds) or "—",
                    src, d["sha256"][:16]))

    L += ["", "---", "", "## 二、美国出口管制规则条文（库 B）", "",
          "| 来源 | 文件 | 日期 | 官方 URL | sha256（前 16） |", "|---|---|---|---|---|"]
    for r in sorted(B, key=lambda x: (x["source"], x.get("date") or "")):
        L.append("| %s | %s | %s | <%s> | `%s` |"
                 % (SITE.get(r["source"], r["source"]).split()[0],
                    Path(r["path"]).name[:38], r.get("date") or "—",
                    r.get("url") or "—", (r.get("sha256") or "")[:16]))

    if n_multi:
        dup = chunk_duplication()
        L += ["", "---", "", "## 三、同一份文件被两个官方来源各取一次的清单（负结果审计）", "",
              f"下面 {n_multi} 份**文件字节与 sha256 完全相同**，只是在巨潮资讯网与深交所"
              "各登记了一次。**它们不是两个独立来源**——不能拿来互相印证。", "",
              dup, "",
              "| 公司 | 文件 | sha256（前 16） | 两个来源 |", "|---|---|---|---|"]
        for d in dlist:
            if len(set(d["sources"])) > 1:
                L.append("| %s | %s | `%s` | %s |"
                         % (d["company"], d["paths"][0][:40], d["sha256"][:16],
                            "、".join(SITE.get(s, s).split()[0] for s in sorted(set(d["sources"])))))

    L += ["", "---", "", "## 校验", "",
          f"- 逐文件**重算** sha256 与字节数：**{len(ok)}/{len(rows)}** 条一致。",
          "- 校验的是**现在磁盘上那个文件**，不是 manifest 的自述——文件被换过这里就对不上。"]
    if bad:
        L += ["", "| 文件 | 问题 |", "|---|---|"]
        L += ["| %s | %s |" % (Path(r["path"]).name, why) for r, why in bad]
    else:
        L += ["- 无不符项 ✅"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("✓ %s  （唯一文档 %d 份 / %d 家公司；其中 %d 份来自两个来源；规则 %d 份）"
          % (OUT, len(dlist), len(companies), n_multi, len(B)))
    return 0 if not bad else 2


if __name__ == "__main__":
    raise SystemExit(main())

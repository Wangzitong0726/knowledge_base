# -*- coding: utf-8 -*-
"""
探测第四轮：把「HBM 是哪一份规则纳入管制的」这件事钉死。

上一轮的错误：只 grep 了最新 25 篇（按日期倒序），而 2024-12-05 的
89 FR 96790（Foreign-Produced Direct Product Rule Additions...）根本没进那一批。
抽样得出的「只有 1 篇提到 HBM」是错的结论。本轮机扫全部 54 篇，逐篇记录。

同时补：TrendForce 正文提取、SK hynix IR 路径。
"""
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
_out = []


def rec(n, ok, note):
    _out.append((n, ok, note))
    print(f"[{'OK ' if ok else 'FAIL'}] {n} :: {note}")


def fetch(url, timeout=60, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), time.time() - t0


def strip_html(b):
    b = re.sub(r"(?is)<(script|style).*?</\1>", " ", b)
    b = re.sub(r"(?is)<[^>]+>", " ", b)
    b = (b.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'")
          .replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", b)


def scan_all_bis_rules():
    rules = json.loads((ROOT / "bis_rules.json").read_text(encoding="utf-8"))
    rows = []
    print(f"  待扫 {len(rules)} 篇")
    for i, r in enumerate(rules, 1):
        try:
            raw, el = fetch(r["html_url"], timeout=60)
            body = raw.decode("utf-8", "replace")
            txt = strip_html(body)
            n_hbm = len(re.findall(r"\bHBM\b", txt))
            n_hbw = len(re.findall(r"high[- ]bandwidth memory", txt, re.I))
            n_3a090 = len(re.findall(r"3A090", txt))
            n_dram = len(re.findall(r"\bDRAM\b", txt))
            rows.append({
                "date": r["publication_date"], "cite": r.get("citation"),
                "title": r["title"], "url": r["html_url"],
                "chars": len(txt), "HBM": n_hbm, "high_bw": n_hbw,
                "3A090": n_3a090, "DRAM": n_dram,
                "effective_on": r.get("effective_on"),
                "abstract": (r.get("abstract") or "")[:300],
            })
            flag = "★" if (n_hbm or n_hbw) else " "
            print(f"  {flag} [{i:2}/{len(rules)}] {r['publication_date']} {r.get('citation')} "
                  f"HBM={n_hbm} highbw={n_hbw} 3A090={n_3a090} DRAM={n_dram} | {r['title'][:55]}")
        except Exception as e:
            print(f"    ! [{i}/{len(rules)}] {r['publication_date']} 失败 {type(e).__name__}: {str(e)[:50]}")
            rows.append({"date": r["publication_date"], "cite": r.get("citation"),
                         "title": r["title"], "url": r["html_url"], "error": str(e)[:80]})
        time.sleep(0.25)

    (ROOT / "bis_rules_scanned.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    hbm_hits = [r for r in rows if r.get("HBM") or r.get("high_bw")]
    rec("机扫全部 BIS 规则 · 提到 HBM 的", bool(hbm_hits), f"命中 {len(hbm_hits)} 篇")
    for r in hbm_hits:
        rec(f"  ▶ {r['date']} {r['cite']}", True,
            f"HBM×{r['HBM']} high-bandwidth×{r['high_bw']} 3A090×{r['3A090']} "
            f"生效日={r.get('effective_on')} | {r['title'][:70]}")

    # 单看 3A090 密度最高的几篇（HBM 在 EAR 里挂在 3A090 下）
    top = sorted([r for r in rows if r.get("3A090")], key=lambda x: -x["3A090"])[:8]
    rec("3A090 提及最多的规则", bool(top), "；".join(f"{r['date']}({r['3A090']})" for r in top))
    return rows


def dig_into_rule(cite_date, needle="HBM"):
    """把命中的那一篇里，HBM 出现的上下文抽出来——这是论文要引的原句。"""
    rows = json.loads((ROOT / "bis_rules_scanned.json").read_text(encoding="utf-8"))
    for r in rows:
        if r.get("date") == cite_date and (r.get("HBM") or r.get("high_bw")):
            raw, el = fetch(r["url"], timeout=90)
            txt = strip_html(raw.decode("utf-8", "replace"))
            out = []
            for m in re.finditer(r"\bHBM\b|high[- ]bandwidth memory", txt, re.I):
                s = max(0, m.start() - 320)
                out.append(txt[s:m.end() + 320])
            (ROOT / f"hbm_context_{cite_date}.txt").write_text(
                "\n\n=== 上下文分隔 ===\n\n".join(out[:6]), encoding="utf-8")
            rec(f"{cite_date} HBM 上下文抽取", bool(out), f"抽出 {len(out)} 处")
            for i, c in enumerate(out[:3], 1):
                print(f"\n  ── 第{i}处 ──\n  {c[:600]}")
            return True
    rec(f"{cite_date} HBM 上下文抽取", False, "未找到")
    return False


def probe_trendforce_body():
    raw, el = fetch("https://www.trendforce.com/presscenter/news/20260924-13252.html", timeout=40)
    body = raw.decode("utf-8", "replace")
    # TrendForce 正文一般在 article / .content / .news-detail 里
    for pat in [r'(?is)<article[^>]*>(.*?)</article>',
                r'(?is)<div[^>]*class="[^"]*(?:content|detail|news)[^"]*"[^>]*>(.*?)</div>\s*</div>',
                r'(?is)<h1[^>]*>(.*?)</h1>']:
        m = re.search(pat, body)
        if m:
            t = strip_html(m.group(1))
            if len(t) > 200:
                rec(f"TrendForce 正文（{pat[:28]}…）", True, f"{len(t)} 字：{t[:260]!r}")
                return t
    # 退一步：全文去标签后找含 % 与 DRAM 的句子
    txt = strip_html(body)
    sents = [s.strip() for s in re.split(r"(?<=[.。])\s", txt)
             if re.search(r"DRAM|HBM", s, re.I) and "%" in s]
    rec("TrendForce 正文（退化为句子级匹配）", bool(sents),
        f"找到 {len(sents)} 句；{sents[:2]}")
    return None


def probe_skhynix():
    for label, url in [
        ("SK hynix 首页", "https://www.skhynix.com/eng/index.do"),
        ("SK hynix IR 主入口", "https://www.skhynix.com/eng/ir/irMain.do"),
        ("SK hynix 投资者关系", "https://www.skhynix.com/eng/investorRelations.do"),
        ("SK hynix 财报发布", "https://www.skhynix.com/eng/ir/earningsRelease.do"),
        ("SK hynix newsroom", "https://news.skhynix.com/"),
        ("SK hynix newsroom 英文", "https://news.skhynix.com/en/"),
    ]:
        try:
            raw, el = fetch(url, timeout=40)
            body = raw.decode("utf-8", "replace")
            pdfs = re.findall(r'href="([^"]+\.pdf)"', body, re.I)
            rec(label, len(raw) > 3000, f"{len(raw)/1e3:.0f}KB PDF链接={len(pdfs)} {pdfs[:2]}")
        except urllib.error.HTTPError as e:
            rec(label, False, f"HTTP {e.code}")
        except Exception as e:
            rec(label, False, f"{type(e).__name__}: {str(e)[:60]}")


def probe_ecfr_last():
    """eCFR 最后再试一次：不带查询串、以及 content 端点。"""
    for label, url in [
        ("eCFR 不带参数", "https://www.ecfr.gov/api/versioner/v1/full/2026-09-24/title-15.xml"),
        ("eCFR content 端点", "https://www.ecfr.gov/api/renderer/v1/content/enhanced/2026-09-24/title-15?part=774"),
        ("eCFR 官方建议的 UA 格式", "https://www.ecfr.gov/api/versioner/v1/full/2026-09-24/title-15.xml?part=774"),
    ]:
        try:
            raw, el = fetch(url, timeout=120, headers={
                "Accept": "application/xml",
                "Accept-Encoding": "gzip, deflate",
            })
            body = raw.decode("utf-8", "replace")
            rec(label, len(raw) > 10_000,
                f"{len(raw)/1e6:.2f}MB 含3A090={'3A090' in body}")
        except urllib.error.HTTPError as e:
            rec(label, False, f"HTTP {e.code}")
        except Exception as e:
            rec(label, False, f"{type(e).__name__}: {str(e)[:60]}")


def main():
    print("=" * 70)
    print("探测第四轮 · HBM 规则钉死")
    print("=" * 70)
    print("\n--- 机扫全部 BIS 规则 ---")
    scan_all_bis_rules()
    print("\n--- 抽 HBM 原句上下文 ---")
    dig_into_rule("2024-12-05")
    print("\n--- TrendForce 正文 ---")
    probe_trendforce_body()
    print("\n--- SK hynix ---")
    probe_skhynix()
    print("\n--- eCFR 最后尝试 ---")
    probe_ecfr_last()

    lines = ["# 探测第四轮报告", "", f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| 检查项 | 结果 | 实测记录 |", "|---|---|---|"]
    for n, ok, note in _out:
        lines.append(f"| {n} | {'✅' if ok else '❌'} | {note} |")
    (ROOT / "probe_report4.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n→ {ROOT/'probe_report4.md'}")


if __name__ == "__main__":
    main()

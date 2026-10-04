# -*- coding: utf-8 -*-
"""
探测第五轮（收尾）：
  1. 修我自己的 bug：第四轮设了 Accept-Encoding: gzip 但没解压，
     所以「eCFR 含3A090=False」是假的——工具错，不是数据错。本轮正确解压重测。
  2. 从 govinfo 年度版里抽出 3A090.c 与 License Exception HBM 的原文
     （论文要逐字引的东西，必须从一手文本拿）
  3. SK hynix 正确的 IR 路径（前几轮全是 404）
"""
import gzip
import io
import json
import re
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
_out = []


def rec(n, ok, note):
    _out.append((n, ok, note))
    print(f"[{'OK ' if ok else 'FAIL'}] {n} :: {note}")


def fetch(url, timeout=120, headers=None):
    """这次正确处理 Content-Encoding —— 上一轮的教训。"""
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        enc = (r.headers.get("Content-Encoding") or "").lower()
        if "gzip" in enc:
            raw = gzip.decompress(raw)
        elif "deflate" in enc:
            try:
                raw = zlib.decompress(raw)
            except zlib.error:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        return raw, time.time() - t0, enc


def strip_tags(x):
    x = re.sub(r"(?is)<(script|style).*?</\1>", " ", x)
    x = re.sub(r"(?is)<[^>]+>", " ", x)
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&sect;", "§"), ("&thinsp;", " "),
                 ("&ldquo;", '"'), ("&rdquo;", '"'), ("&#8217;", "'"), ("&quot;", '"')]:
        x = x.replace(a, b)
    return re.sub(r"\s+", " ", x)


# ------------------------------------------------------- 1. eCFR 正确重测
def ecfr_fixed():
    cases = [
        ("eCFR full + gzip 正确解压",
         "https://www.ecfr.gov/api/versioner/v1/full/2026-09-24/title-15.xml?part=774",
         {"Accept": "application/xml", "Accept-Encoding": "gzip"}),
        ("eCFR full 不带 Accept-Encoding",
         "https://www.ecfr.gov/api/versioner/v1/full/2026-09-24/title-15.xml?part=774",
         {"Accept": "application/xml", "Accept-Encoding": "identity"}),
        ("eCFR 无任何多余头",
         "https://www.ecfr.gov/api/versioner/v1/full/2026-09-24/title-15.xml?part=774",
         None),
    ]
    for label, url, hdr in cases:
        try:
            raw, el, enc = fetch(url, headers=hdr)
            body = raw.decode("utf-8", "replace")
            ok = "3A090" in body
            rec(label, ok, f"{len(raw)/1e6:.2f}MB Content-Encoding={enc or '-'} "
                           f"含3A090={ok} 含HBM={'HBM' in body}")
            if ok:
                (ROOT / "ecfr_774_现行版.xml").write_bytes(raw)
                return True
        except urllib.error.HTTPError as e:
            rec(label, False, f"HTTP {e.code}")
        except Exception as e:
            rec(label, False, f"{type(e).__name__}: {str(e)[:70]}")
    return False


# ------------------------------------------------------- 2. 抽 3A090.c 原文
def extract_3a090c():
    """govinfo 年度版（CFR-2025 title15 vol2）已实测可取。抽 3A090.c 与 License Exception HBM。"""
    url = "https://www.govinfo.gov/content/pkg/CFR-2025-title15-vol2/xml/CFR-2025-title15-vol2.xml"
    try:
        raw, el, enc = fetch(url)
    except Exception as e:
        rec("govinfo CFR-2025 取回", False, f"{type(e).__name__}: {str(e)[:70]}")
        return
    xml = raw.decode("utf-8", "replace")
    rec("govinfo CFR-2025 title15 vol2", "3A090" in xml,
        f"{len(raw)/1e6:.2f}MB 含3A090={'3A090' in xml} 含'High Bandwidth Memory'="
        f"{'High Bandwidth Memory' in xml}")
    (ROOT / "govinfo_cfr2025_title15_vol2.xml").write_bytes(raw)

    plain = strip_tags(xml)
    # 3A090.c 的正文
    out = []
    for m in re.finditer(r"3A090\.c", plain):
        s = max(0, m.start() - 200)
        out.append(plain[s:m.end() + 900])
    if out:
        (ROOT / "extract_3A090c.txt").write_text(
            "\n\n==== 下一处 ====\n\n".join(dict.fromkeys(out))[:12000], encoding="utf-8")
        rec("抽出 3A090.c 正文", True, f"{len(out)} 处")
        print("\n── 3A090.c 首处上下文 ──")
        print("  " + out[0][:1000].replace("\n", " "))
    else:
        rec("抽出 3A090.c 正文", False, "未匹配到 3A090.c")

    # 3A090 整体（含 a/b/c/d 分项）
    m = re.search(r"3A090\s+(?=[A-Z])(.{0,2500})", plain)
    if m:
        (ROOT / "extract_3A090_full.txt").write_text(m.group(0)[:3000], encoding="utf-8")
        rec("抽出 3A090 整条", True, f"{len(m.group(0))} 字")
        print("\n── 3A090 整条开头 ──")
        print("  " + m.group(0)[:900])

    # License Exception HBM
    m = re.search(r"License Exception HBM(.{0,1200})", plain)
    if m:
        rec("抽出 License Exception HBM", True, "已存 extract_license_exception_hbm.txt")
        (ROOT / "extract_license_exception_hbm.txt").write_text(m.group(0), encoding="utf-8")
        print("\n── License Exception HBM ──")
        print("  " + m.group(0)[:700])
    else:
        rec("抽出 License Exception HBM", False, "年度版里未匹配到（可能已随法规修订改号）")

    # 顺带确认这个年度版里 DRAM/NAND 相关 ECCN
    for kw in ["3A090.a", "3A090.b", "3A090.c", "3A090.d", "HBM", "DRAM"]:
        rec(f"  · '{kw}' 出现次数", True, f"{plain.count(kw)} 次")


# ------------------------------------------------------- 3. SK hynix 路径
def skhynix_paths():
    tried = [
        ("根域", "https://www.skhynix.com/"),
        ("英文主站", "https://www.skhynix.com/eng/main.do"),
        ("IR 入口(旧)", "https://www.skhynix.com/eng/ir/irMain.do"),
        ("年报页", "https://www.skhynix.com/eng/ir/annualReport.do"),
        ("SK hynix 全球英文", "https://www.skhynix.com/en/"),
        ("SK hynix 会社案内", "https://www.skhynix.com/company/en/"),
        ("newsroom 英文列表", "https://news.skhynix.com/category/press-release/"),
    ]
    for label, url in tried:
        try:
            raw, el, enc = fetch(url, timeout=40)
            body = raw.decode("utf-8", "replace")
            pdfs = re.findall(r'href="([^"]+\.pdf)"', body, re.I)
            links = sorted(set(re.findall(r'href="(/[a-z0-9/_.\-]*(?:ir|investor|annual)[a-z0-9/_.\-]*)"',
                                          body, re.I)))
            rec(label, len(raw) > 3000,
                f"{len(raw)/1e3:.0f}KB PDF={len(pdfs)} 疑似IR链接={links[:4]}")
        except urllib.error.HTTPError as e:
            rec(label, False, f"HTTP {e.code}")
        except Exception as e:
            rec(label, False, f"{type(e).__name__}: {str(e)[:50]}")


def main():
    print("=" * 70)
    print("探测第五轮 · 收尾（修 bug + 抽法条原文 + SK hynix）")
    print("=" * 70)
    print("\n--- eCFR 正确重测 ---")
    ecfr_fixed()
    print("\n--- 抽 3A090.c / License Exception HBM ---")
    extract_3a090c()
    print("\n--- SK hynix 路径 ---")
    skhynix_paths()

    lines = ["# 探测第五轮报告", "", f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| 检查项 | 结果 | 实测记录 |", "|---|---|---|"]
    for n, ok, note in _out:
        lines.append(f"| {n} | {'✅' if ok else '❌'} | {note} |")
    (ROOT / "probe_report5.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n→ {ROOT/'probe_report5.md'}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""把十道题的问答页各存一份 HTML 存档 + 一张**整页**截图。

覆盖十道题，与 `run_questions.py` 的 `Q` 一一对应（题号一致）。

**为什么不是固定 1000x3000 的窗口**：第一版就是这么截的，四张图**每一张底部都被切掉**
（页面实际 3277–4543px 高）。第 4 张被切掉的正好是召回的 [4]–[8] 五条原文——图里只剩
判词、看不到判词依据的原文，而这套系统的卖点就是「每条论断带 [n] 回原文」。
现在改成：先按 20000px 高渲染，从底部往上扫出内容真实底边，再裁到那个高度。

**文件名不带判定**：第一版叫 `问答页-3-口径题未命中-江波龙`，把一次运行的判定写死进
文件名；判定一旦改变，文件名就成了假声明。现在只留题号 + 主题，判定由
`outputs/十道题-检索记录.md` 和页面本身承担。

用法（需先起服务：`scripts/serve_qa.py`）。**要用系统 Python**——量高度和裁剪靠 pymupdf，
venv 里没装（venv 装的是 torch/transformers 那一套）：
    C:/Python314/python.exe scripts/save_qa_snapshots.py
"""
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pymupdf  # 只在系统 Python 里；若缺失见下方 ImportError 提示

ROOT = Path(".").resolve()
OUT = ROOT / "outputs"
SHOT_DIR = OUT / "截图"
SERVER = "http://127.0.0.1:8848/"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

VIEW_W = 1000
VIEW_H = 20000          # 足够高，保证任何一页都装得下；之后按实际底边裁掉空白

# 与 run_questions.py 的 Q 一一对应：(题号, 主题, 库, k, 问题)
# `k` 必须跟 run_questions.py 里该题的 k **一模一样**——否则图里显示的席数
# 与「十道题-检索记录」对不上，同一个问题在交付物里出现两个数。
CASES = [
    (1, "3A090c管制门槛", "B", 8, "3A090.c 的管制门槛是什么？"),
    (2, "美光HBM表述", "A", 8,
     "美光最近一期财报里，关于 HBM 的收入、产能或资本开支有哪些表述？"),
    (3, "管制修订时点", "B", 8,
     "2024 年 12 月以前 HBM 受出口管制吗？是哪一份规则改变了这一点？"),
    (4, "江波龙口径", "A", 8,
     "江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？"),
    (5, "管制影响面", "A+B", 10, "出口管制对内存市场的影响涉及哪几个方面？"),
    (6, "长口语问题", "A+B", 10,
     "我最近在看内存这块，感觉这两年 HBM 突然就热起来了，好多做存储的公司都在讲。"
     "我想知道，美国那边的出口管制到底卡的是什么？是卡整个 DRAM，还是只卡 HBM？"
     "卡的具体是哪一类，有没有一个明确的技术线？"),
    (7, "三家HBM供需", "A", 14,
     "三星、SK 海力士、美光三家最近一期报告对 HBM 供需与产能的表述有哪些共性和差异？"),
    (8, "A股披露", "A", 14, "A 股内存产业链公司如何披露出口管制对自身经营的影响？"),
    (9, "跨库时间线", "A+B", 10,
     "出口管制规则的历次修订时点，与厂商财报里提到的价格或 ASP 变化能对上吗？"),
    (10, "HBM3E合约价", "A+B", 10, "HBM3E 现在的合约价是多少美元？"),
]

# 第 7 题点名了三家，截完要当场核对三家在不在页面里
NAMED = {7: ("三星", "SK 海力士", "美光")}


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("找不到 Chrome/Edge，无法截图。")


def seats_by_company(html_text: str) -> Counter:
    """按**出处公司**统计召回分布：每条召回出自哪家，而不是「公司名在不在正文里」。

    ⚠️ 这里连栽两次，两版判据都是「永远通过」：
      1. 第一版判 `'三星' in html_text` —— 可是页面**把问题原样印在顶部**，问题里
         就写着「三星、SK 海力士、美光」，判据被问题自己满足。
      2. 第二版只截「语料原文」之后、再看公司名出现次数 —— **还是错的**：三星是作为
         「被引用的词」出现在佰维存储报告的正文里（"…季度的 DRAM 市场上，三星、SK 海力…"，
         那是转引 TrendForce 的市场份额表），数出来 5 席；而三星**自己的材料是 0 条**。
     **名字出现 ≠ 材料被召回**。页面每条召回的抬头就印着出处公司，判它。
    """
    src = html_text[html_text.find("语料原文"):]
    out: Counter = Counter()
    for b in re.split(r"<div class=hit ", src)[1:]:
        m = re.search(r"class=no>\[\d+\]</span>\s*([^<·]+?)\s*·", b)
        if m:
            out[m.group(1).strip()] += 1
    return out


def content_height(png: Path) -> int:
    """整页 PNG 里内容的下边界（像素）。

    背景色从**最底下一行**取——那是页面内容之外的空白区，肯定不是内容色。
    （若从左上角取，遇到彩色页头就会把整页都判成内容。）
    """
    pix = pymupdf.Pixmap(str(png))
    w, h, n, stride = pix.width, pix.height, pix.n, pix.stride
    buf = pix.samples

    def rgb(x, y):
        o = y * stride + x * n
        return buf[o], buf[o + 1], buf[o + 2]

    bg = rgb(2, h - 2)
    for y in range(h - 1, -1, -1):
        row = y * stride
        for x in range(0, w, 5):
            o = row + x * n
            if (abs(buf[o] - bg[0]) > 8 or abs(buf[o + 1] - bg[1]) > 8
                    or abs(buf[o + 2] - bg[2]) > 8):
                return y
    return 0


def shoot(chrome: str, html: Path, png: Path) -> tuple[int, int]:
    """整页截图：高窗口渲染 → 量底边 → 裁。返回 (页面高度, 输出高度)。"""
    tmp = png.with_name("_full.png")
    tmp.unlink(missing_ok=True)
    url = "file:///" + html.resolve().as_posix()
    r = subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--window-size={VIEW_W},{VIEW_H}",
         f"--screenshot={tmp}", url],
        capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    if not tmp.exists():
        raise SystemExit(f"截图失败：{html.name}\n{r.stderr[-400:]}")

    h = content_height(tmp) + 20          # 留 20px 下边距，不让最后一行贴边
    doc = pymupdf.open(str(tmp))
    page = doc[0]
    # 图片文档按 96dpi→72dpi 换算，1 像素 = 0.75 点
    k = page.rect.width / VIEW_W
    part = page.get_pixmap(clip=pymupdf.Rect(0, 0, page.rect.width, h * k), dpi=96)
    part.save(str(png))
    doc.close()
    tmp.unlink(missing_ok=True)
    return h, part.height


def main():
    chrome = find_chrome()
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"服务 {SERVER}  浏览器 {Path(chrome).name}\n")
    for n, topic, lib, k, q in CASES:
        t0 = time.time()
        url = SERVER + "?" + urllib.parse.urlencode({"q": q, "k": k})
        with urllib.request.urlopen(url, timeout=600) as resp:
            html_text = resp.read().decode("utf-8")
        html = OUT / f"问答页-{n:02d}-{topic}.html"
        html.write_text(html_text, encoding="utf-8")

        png = SHOT_DIR / f"问答页-{n:02d}-{topic}.png"
        page_h, out_h = shoot(chrome, html, png)

        note = ""
        if n in NAMED:
            seats = seats_by_company(html_text)
            miss = [c for c in NAMED[n] if not any(c in k for k in seats)]
            note = (f"  ⚠️ 点名公司无自家材料：{'、'.join(miss)}" if miss
                    else "  点名公司均有自家材料")
        print(f"  [{n:>2}] 库{lib:<3} {topic:<14} 页高 {page_h:>5}px → 图 {out_h:>5}px  "
              f"{png.stat().st_size/1024:>4.0f}KB  {time.time()-t0:>5.1f}s{note}")
    print(f"\nHTML 存档 {len(CASES)} 份 → outputs/    截图 {len(CASES)} 张 → outputs/截图/")


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        raise SystemExit(f"缺 pymupdf（用它来量页面高度并裁剪）：{e}\n"
                         f"本脚本要用**系统** Python：C:/Python314/python.exe scripts/save_qa_snapshots.py")

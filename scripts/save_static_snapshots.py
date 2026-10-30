# -*- coding: utf-8 -*-
"""把**静态交付页**（不是问答页）渲染成整页截图，补老师要的「丰富截图」。

老师批改：「丰富截图」「至少 10 家官方全文来源」「全景按公司取证」
「召回与答案表现分别评价」。四类各一张：

  ① 来源清单            → 18 家公司的官方来源台账（≥10 家的凭据）
  ② 逐题记录 · 召回/答案 两栏（挑 Q4 口径题、Q7 全景题两张）
  ③ 表头修复前后对照      → 「先修行列」的证据
  另加总览一页

**为什么走 md 而不是让页面上色**：这些交付页本身就是 md（`outputs/*.md`），
用 `md2pdf.py --html-only` 转一次 HTML（同一份渲染、同一套 CSS，不再写第二套），
再交给 `shotlib.shoot` 量高度、裁图。

**两个解释器**（这是本项目的既定分工，不是疏忽）：
  · md→HTML 用 **venv**（markdown-it 装在那儿）
  · 量高度 / 裁图用 **系统 Python**（pymupdf 装在那儿）
本脚本自己跑在系统 Python 上，内部 subprocess 调 venv。

用法（在项目根目录）：
    C:/Python314/python.exe scripts/save_static_snapshots.py
"""
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import shotlib                                                 # noqa: E402

OUT = ROOT / "outputs"
SHOT_DIR = OUT / "截图"
TMP = OUT / "_snap"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"

# (出图名, 源 md, 只取哪一段（正则，None=整份）)
CASES = [
    ("来源清单-18家官方来源", "outputs/来源清单.md", None),
    ("表头修复对照", "outputs/表头修复对照.md", None),
    ("逐题记录-总览", "outputs/十道题-检索记录.md", r"^## 总览"),
    ("逐题记录-Q04-口径题", "outputs/十道题-检索记录.md", r"^## 第 4 题"),
    ("逐题记录-Q07-全景题按公司取证", "outputs/十道题-检索记录.md", r"^## 第 7 题"),
]


def section(md_text, pat, source_name):
    """按 `^## …` 标题切出一节：从匹配的那行起，到下一个**同级或更高级**标题止。

    ⚠️ 不能简单按 `^##` 切——模型作答里自己带二级标题
    （Q6 里就有 `## 结论：卡的是 HBM，不是整个 DRAM`）。所以要切到
    **下一个 `^## 第 N 题`** 或文末，而不是下一个 `^##`。
    """
    lines = md_text.split("\n")
    start = next((i for i, ln in enumerate(lines) if re.match(pat, ln)), None)
    if start is None:
        return None
    nxt = re.compile(r"^## 第 \d+ 题|^## 总览|^# ")
    stop = len(lines)
    for j in range(start + 1, len(lines)):
        if nxt.match(lines[j]):
            stop = j
            break
    body = "\n".join(lines[start:stop]).rstrip()
    return f"# {source_name}\n\n{body}\n"


def main():
    chrome = shotlib.find_chrome()
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    print("浏览器 %s\n" % Path(chrome).name)

    ok = 0
    for name, rel, pat in CASES:
        src = ROOT / rel
        if not src.exists():
            print("  [跳过] 没有 %s" % rel)
            continue
        if pat:
            body = section(src.read_text(encoding="utf-8"), pat, src.stem)
            if body is None:
                print("  [跳过] %s 里没找到 %s" % (rel, pat))
                continue
            md = TMP / (name + ".md")
            md.write_text(body, encoding="utf-8")
        else:
            md = src

        t0 = time.time()
        # md → HTML（venv 的 markdown-it），不调 Chrome，PDF 那步留给 md2pdf 自己做
        r = subprocess.run([str(VENV_PY), str(ROOT / "scripts" / "md2pdf.py"),
                            str(md), "--html-only"],
                           capture_output=True, encoding="utf-8", errors="replace",
                           cwd=str(ROOT), timeout=120)
        html = md.with_suffix(".print.html")
        if not html.exists():
            print("  [失败] %s\n%s" % (name, (r.stdout + r.stderr)[-300:]))
            continue

        png = SHOT_DIR / (name + ".png")
        page_h, out_h = shotlib.shoot(chrome, html, png)
        ok += 1
        print("  [%2d] %-32s 页高 %6dpx → 图 %6dpx  %5.0fKB  %4.1fs"
              % (ok, name, page_h, out_h, png.stat().st_size / 1024, time.time() - t0))

    print("\n静态页截图 %d 张 → outputs/截图/" % ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

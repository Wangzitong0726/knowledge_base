# -*- coding: utf-8 -*-
"""把 outputs/ 里的 Markdown 排成 PDF（作业要交「一页结论（PDF）」）。

做法：markdown-it 转 HTML → 套一份中文字体友好的打印 CSS → 无头 Chrome 打 PDF。
**不引第三方排版器**（pandoc/weasyprint 本机都没有），Chrome 本机就有。

用法：
    ./.venv/Scripts/python.exe scripts/md2pdf.py outputs/一页结论.md
    ./.venv/Scripts/python.exe scripts/md2pdf.py outputs/一页结论.md --keep-html
"""
import argparse
import html as _html
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ⚠️ Windows 常见安装位置；找不到就报错，**不静默跳过**（静默跳过 = 没产出还以为产出
# 了，与 `--save-every` 那类「声明了没接线」同族）。
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 15mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei","微软雅黑","SimSun",sans-serif;
       font-size: 10.5pt; line-height: 1.55; color: #1a1a1a; }
h1 { font-size: 17pt; border-bottom: 2px solid #333; padding-bottom: 4px;
     margin: 0 0 10px; }
h2 { font-size: 13pt; margin: 14px 0 6px; padding-left: 7px;
     border-left: 4px solid #444; }
h3 { font-size: 11.5pt; margin: 10px 0 4px; }
p, li { margin: 4px 0; }
ul, ol { padding-left: 20px; margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 7px 0; font-size: 9.5pt; }
th, td { border: 1px solid #bbb; padding: 3px 6px; text-align: left;
         vertical-align: top; word-break: break-word; }
th { background: #f0f0f0; }
code { font-family: Consolas,"Courier New",monospace; font-size: 9pt;
       background: #f5f5f5; padding: 1px 3px; border-radius: 2px;
       word-break: break-all; }
pre { background: #f5f5f5; padding: 7px; border-radius: 3px; overflow-x: auto;
      font-size: 8.5pt; }
pre code { background: none; padding: 0; }
blockquote { margin: 7px 0; padding: 5px 12px; border-left: 3px solid #999;
             background: #fafafa; color: #333; }
hr { border: none; border-top: 1px solid #ccc; margin: 12px 0; }
a { color: #0645ad; text-decoration: none; }
strong { font-weight: 700; }
"""


def find_browser():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("找不到 Chrome/Edge，无法出 PDF。装了哪个就把路径加进 CHROME_CANDIDATES。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", help="输入 .md")
    ap.add_argument("-o", "--out", help="输出 .pdf（默认与输入同目录同名）")
    ap.add_argument("--keep-html", action="store_true", help="留下中间 HTML 供检查")
    a = ap.parse_args()

    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    md_path = Path(a.md)
    if not md_path.is_absolute():
        md_path = ROOT / md_path
    if not md_path.exists():
        raise SystemExit(f"没有这个文件：{md_path}")
    pdf_path = Path(a.out) if a.out else md_path.with_suffix(".pdf")
    if not pdf_path.is_absolute():
        pdf_path = ROOT / pdf_path

    from markdown_it import MarkdownIt
    # js-default 预设带表格；不加 linkify（省一个依赖）。
    md = MarkdownIt("js-default")
    body = md.render(md_path.read_text(encoding="utf-8"))
    title = md_path.stem
    doc = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
           f"<title>{_html.escape(title)}</title><style>{CSS}</style></head>"
           f"<body>{body}</body></html>")

    if a.keep_html:
        hp = md_path.with_suffix(".print.html")
        hp.write_text(doc, encoding="utf-8")
        print(f"  中间 HTML：{hp}")
    else:
        tf = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                         encoding="utf-8")
        tf.write(doc)
        tf.close()
        hp = Path(tf.name)

    browser = find_browser()
    # ⚠️ Chrome 要的是 file:// URL，不是 Windows 路径；空格要转义。
    url = "file:///" + str(hp).replace("\\", "/").replace(" ", "%20")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    # ⚠️ 去页眉页脚要用 `--print-to-pdf-no-header`，**不是** `--no-pdf-header-footer`
    # （后者在本机 Chrome 上实测无效，页眉照印——还会把 `file:///C:/Users/PC/AppData/...`
    # 临时路径和日期印进交付的 PDF 里）。两个旗标都试过，只有这个管用。
    cmd = [browser, "--headless", "--disable-gpu", "--print-to-pdf-no-header",
           f"--print-to-pdf={pdf_path}", url]
    # ⚠️ 必须显式 utf-8/replace：Windows 默认 GBK，Chrome 的日志里有非 GBK 字节，
    # 用 `text=True` 会在读线程里抛 UnicodeDecodeError（看着像 PDF 失败了，
    # 其实文件已经写出来了——**报错和事实打架**，比没报错更误导）。
    r = subprocess.run(cmd, capture_output=True, timeout=180,
                       encoding="utf-8", errors="replace")
    if not pdf_path.exists():
        print(r.stdout[-1500:]); print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit("Chrome 没能产出 PDF（看上面的输出）")
    print(f"  ✓ {pdf_path}  {pdf_path.stat().st_size/1024:.0f} KB")
    if not a.keep_html:
        hp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

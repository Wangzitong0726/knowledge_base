# -*- coding: utf-8 -*-
"""整页截图的公共部分：找浏览器、无头渲染、量出内容真实底边、裁到该高度。

**为什么单独成一个模块**：`save_qa_snapshots.py`（十道题的问答页）和新加的
`save_static_snapshots.py`（来源清单 / 逐题记录 / 全景取证 / 表头修复前后）
要走**同一套**裁剪逻辑。复制一遍的下场是：一边修了「固定 3000px 会切底」的 bug，
另一边还留着——而两张图看起来都「正常」。

⚠️ 本模块依赖 **pymupdf**，只有系统 Python 有：
      C:/Python314/python.exe ...
"""
import os
import subprocess
from pathlib import Path

import pymupdf

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

VIEW_W = 1000
VIEW_H = 20000          # 足够高，保证任何一页都装得下；之后按实际底边裁掉空白


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("找不到 Chrome/Edge，无法截图。")


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


def shoot(chrome: str, html: Path, png: Path, view_w: int = VIEW_W) -> tuple[int, int]:
    """整页截图：高窗口渲染 → 量底边 → 裁。返回 (页面高度, 输出高度)。"""
    tmp = png.with_name("_full_" + png.stem + ".png")
    tmp.unlink(missing_ok=True)
    url = "file:///" + html.resolve().as_posix()
    r = subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--window-size={view_w},{VIEW_H}",
         f"--screenshot={tmp}", url],
        capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    if not tmp.exists():
        raise SystemExit(f"截图失败：{html.name}\n{r.stderr[-400:]}")

    h = content_height(tmp) + 20          # 留 20px 下边距，不让最后一行贴边
    doc = pymupdf.open(str(tmp))
    page = doc[0]
    # 图片文档按 96dpi→72dpi 换算，1 像素 = 0.75 点
    k = page.rect.width / view_w
    part = page.get_pixmap(clip=pymupdf.Rect(0, 0, page.rect.width, h * k), dpi=96)
    part.save(str(png))
    doc.close()
    tmp.unlink(missing_ok=True)
    return h, part.height

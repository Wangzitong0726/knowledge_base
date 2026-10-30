# -*- coding: utf-8 -*-
"""验证跨页表头继承：跑真正的 `extract_pdf`，打印指定页的抽取结果。

只读，不改任何产物。

用法：
    C:/Python314/python.exe _probe/verify_inherit.py <pdf路径> <页码> [页码...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract.pdf import extract_pdf  # noqa: E402


def main(pdf, pages):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    recs, info = extract_pdf(pdf)
    print("共 %d 页，抽到表格 %d 张" % (info["pages"], info["tables"]))
    for pno in pages:
        print("=" * 78)
        print("第 %d 页" % pno)
        print("=" * 78)
        print(recs[pno - 1]["text"][:2500])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    main(sys.argv[1], [int(x) for x in sys.argv[2:]])

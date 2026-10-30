# -*- coding: utf-8 -*-
"""随机抽 C 类（旧表头不配 + 新不猜）的表，把**新旧拍平输出**并排打出来。

只读。用法：
    C:/Python314/python.exe _probe/c_side_by_side.py [抽几条] [类别 B|C]
"""
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import extract.tablefmt as NEW          # noqa: E402
from extract import pdf as PDF          # noqa: E402
import pymupdf                          # noqa: E402

src = subprocess.check_output(["git", "show", "HEAD:scripts/extract/tablefmt.py"], cwd=str(ROOT))
f = Path(tempfile.gettempdir()) / "_old_tablefmt_head.py"
f.write_bytes(src)
spec = importlib.util.spec_from_file_location("_old_tablefmt", f)
OLD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OLD)


def main(n=10, want="C"):
    D = [json.loads(l) for l in open(ROOT / "_probe" / "header_fix_detail.jsonl",
                                     encoding="utf-8")]
    D = [d for d in D if (bool(d["new_hdr"]) == (want == "B"))]
    random.seed(20261012)
    picks = random.sample(D, min(n, len(D)))
    cache = {}
    for d in picks:
        path = ROOT / "data" / "raw" / "cninfo" / d["doc"].split("/", 1)[1] \
            if False else ROOT / "data" / "raw" / "cninfo" / d["doc"]
        if not path.exists():
            print("！缺文件 %s" % path)
            continue
        if path not in cache:
            cache[path] = pymupdf.open(str(path))
        doc = cache[path]
        page = doc[d["page"] - 1]
        tabs = page.find_tables(strategy="lines").tables
        # 找该页里那张「旧表头 = 明细里记的旧表头」的表
        for t in tabs:
            rows = NEW.clean_rows(t.extract())
            if not rows or not NEW.table_ok(rows)[0]:
                continue
            o = 0
            best = OLD._header_score(rows[0])
            for i in range(1, min(2, len(rows))):
                s = OLD._header_score(rows[i])
                if s > best:
                    o, best = i, s
            if [x for x in rows[o] if x] != d["old_hdr"]:
                continue
            print("=" * 78)
            print("%s  p%d   （平均格长 %.0f 字）" % (
                d["doc"], d["page"],
                sum(len(x) for r in rows for x in r if x) /
                max(1, sum(1 for r in rows for x in r if x))))
            print("网格 %d 行 × %d 列；旧选中的表头行 = %s" % (
                len(rows), max(len(r) for r in rows), d["old_hdr"][:4]))
            print("--- 旧输出（前 5 行）：")
            for ln in OLD.flatten_table(rows).split("\n")[:5]:
                print("    " + ln[:150])
            print("--- 新输出（前 5 行）：")
            for ln in NEW.flatten_table(rows)[0].split("\n")[:5]:
                print("    " + ln[:150])
            break


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10,
         sys.argv[2] if len(sys.argv) > 2 else "C")

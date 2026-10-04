# -*- coding: utf-8 -*-
"""
阶段 1 · 抓取编排

    python scripts/run_stage1.py                  # 全部源
    python scripts/run_stage1.py --only cninfo    # 只抓某个源（可逗号分隔）
    python scripts/run_stage1.py --list           # 只列清单，不下载（试跑）

产出：
    data/raw/<来源>/...        原始文件
    data/manifest.jsonl        抓取清单（每条：URL、字节、sha256、时间、公司）
    data/stage1_报告.md         本次运行汇总 + 失败明细

可重跑：已存在且字节数正确的文件会跳过。
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fetch.common import Fetcher          # noqa: E402
from fetch import cninfo, szse, sec_edgar, samsung, skhynix, rules   # noqa: E402

RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.jsonl"
START = "2024-01-01"

SOURCES = {
    # 巨潮（证监会指定信息披露网站）：沪市 8 家 + 深市 7 家（深市那份留作**交叉印证**，
    # 不进最终索引；索引里深市用深交所官网的版本，见 Stage 3）
    "cninfo":  ("库A · 巨潮 A股 15 家年报/半年报", lambda f: cninfo.run(f, RAW / "cninfo", start=START)),
    # 深交所**官网**：直接满足作业「从交易所网站下载」的要求
    "szse":    ("库A · 深交所官网 定期报告",   lambda f: szse.run(f, RAW / "szse", start=START)),
    "sec":     ("库A · 美光 10-K/10-Q",       lambda f: sec_edgar.run(f, RAW / "sec")),
    "samsung": ("库A · 三星电子 IR",           lambda f: samsung.run(f, RAW / "samsung")),
    "skhynix": ("库A · SK 海力士 IR",          lambda f: skhynix.run(f, RAW / "skhynix")),
    "rules":   ("库B · 规则库",                lambda f: rules.run(f, RAW / "rules")),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只跑这些源，逗号分隔：cninfo,sec,samsung,skhynix,rules")
    ap.add_argument("--list", action="store_true", help="只列清单不下载")
    ap.add_argument("--delay", type=float, default=None, help="每次请求间隔（秒）")
    args = ap.parse_args()

    want = [s.strip() for s in args.only.split(",") if s.strip()] or list(SOURCES)
    bad = [s for s in want if s not in SOURCES]
    if bad:
        raise SystemExit(f"未知源：{bad}，可选 {list(SOURCES)}")

    # 巨潮对频率敏感（实测下限 1.2s），其余源可以快些
    delay = args.delay if args.delay is not None else 1.2
    f = Fetcher(MANIFEST, delay=delay)
    if args.list:
        print("（--list 模式：只列清单，不下载）")

    t0 = time.time()
    print("=" * 74)
    print(f"阶段 1 抓取 · {len(want)} 个源 · 起始 {START} · 间隔 {delay}s")
    print(f"清单：{MANIFEST}")
    print("=" * 74)

    for s in want:
        label, fn = SOURCES[s]
        print(f"\n{'─'*74}\n▶ {s}  （{label}）\n{'─'*74}")
        try:
            fn(f)
        except KeyboardInterrupt:
            print("\n!! 用户中断")
            break
        except Exception as e:
            f.fail(s, "整源异常", f"{type(e).__name__}: {e}")

    el = time.time() - t0
    print("\n" + "=" * 74)
    print(f"完成，用时 {el/60:.1f} 分钟")
    f.summary()

    # 汇总报告
    lines = ["# 阶段 1 抓取报告", "",
             f"运行时间：{time.strftime('%Y-%m-%d %H:%M:%S')}　用时 {el/60:.1f} 分钟",
             f"源：{', '.join(want)}", "",
             f"新增 {len(f.records)} 份，失败 {len(f.failures)} 项", ""]
    if f.records:
        by = {}
        for r in f.records:
            by.setdefault(r["source"], []).append(r)
        lines += ["## 新增明细（按来源）", "", "| 来源 | 份数 | 体积 |", "|---|---|---|"]
        for s, rs in sorted(by.items()):
            lines.append(f"| {s} | {len(rs)} | {sum(x['bytes'] for x in rs)/1e6:.1f}MB |")
    if f.failures:
        lines += ["", "## 失败明细", "", "| 来源 | 对象 | 错误 |", "|---|---|---|"]
        for x in f.failures:
            lines.append(f"| {x['source']} | {x['what'][:60]} | {x['error'][:120]} |")
    (ROOT / "data" / "stage1_报告.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"报告：{ROOT/'data'/'stage1_报告.md'}")
    return 0 if not f.failures else 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""判分器离线试跑：**不发网络请求、不读向量库**，只验判据与渲染。

用捏造的 hits/ans 走一遍 judge_recall / judge_answer，再拿真 write() 渲染一遍，
把渲染错误在跑十题（要花钱、半小时）之前先暴露出来。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import run_questions as RQ                                  # noqa: E402


def hit(text, company="江波龙", source="cninfo", anchors=(), named=(), arank=None):
    return dict(row=1, text=text, company=company, source=source, title="2025年半年度报告",
                file="x.pdf", section="合并利润表", page_start=78, page_end=78,
                url="https://example.invalid", score=0.03, channels="bm25+锚定",
                bm25_rank=3, dense_rank=5, dense_sim=0.81, queries=["q"],
                anchor_rank=arank, anchors=list(anchors), anchor_named=list(named),
                period="2025 年半年度", amount_unit="元", table_title="合并利润表")


print("=" * 78)
print("① 数字归属核对")
print("=" * 78)
H = [hit("一、营业总收入 | 2025 年半年度 10,195,655,370.19 | 2024 年半年度 9,038,807,150.58"
         "\n其中：营业收入 | 2025 年半年度 10,195,655,370.19")]
A = "江波龙的 2025 年半年度营业总收入为 10,195,655,370.19 元（2024 年同期 9,038,807,150.58）。" \
    "另外研发费用约 5,000 万元，3A090 门槛是 2 GB/s。"
have, orph = RQ.number_attribution(A, "「营业收入」和「营业总收入」差在哪？", H)
print("  有出处：", have)
print("  无出处：", orph)
print("  期望：10,195,655,370.19 与 9,038,807,150.58 有出处；5,000 无出处；")
print("        `2` 与型号 `3A090` 都不该被当成数字 →", "✓" if orph == ["5,000"] else "✗ " + str(orph))

print("\n" + "=" * 78)
print("② 答案判据：抠掉问题原文，防判据被问题自己满足")
print("=" * 78)
q7 = "三星、SK 海力士、美光三家最近一期报告对 HBM 供需与产能的表述有哪些共性和差异？"
echo = "问题是：" + q7 + "\n我的回答：材料未覆盖。"
ok, msg, ex = RQ.judge_answer(dict(n=7, q=q7, must=["HBM"], must_ans=["三星", "海力士", "美光"]),
                             echo, H)
print("  只原样复述问题、自己什么都没说 → %s\n     %s" % ("✗ 竟判过" if ok else "✓ 判不过", msg))
real = "美光称 HBM 需求强劲；SK海力士提到产能；三星的材料我未检索到。"
ok2, msg2, ex2 = RQ.judge_answer(dict(n=7, q=q7, must=["HBM"], must_ans=["三星", "海力士", "美光"]),
                                 real, H)
print("  三家都点到 → %s\n     %s" % ("✓ 判过" if ok2 else "✗ 判不过", msg2))

print("\n" + "=" * 78)
print("③ 必败题（第 10 题）")
print("=" * 78)
for a in ("HBM3E 的合约价材料未覆盖，库中无一手价格。",
          "HBM3E 合约价约 30 美元。",
          "具体价格需查付费报告。"):
    ok, msg, _ = RQ.judge_answer(dict(n=10, q="HBM3E 现在的合约价是多少美元？", must_fail=True), a, H)
    print("  [%s] %s → %s" % ("过" if ok else "不过", a[:26], msg))

print("\n" + "=" * 78)
print("④ 用真 write() 渲染一遍（捏造 2 题，验排版不炸）")
print("=" * 78)
rows = []
for spec, ans in ((RQ.Q[3], "营业总收入 10,195,655,370.19；营业收入 10,195,655,370.19，两者在本库相等。"),
                  (RQ.Q[9], "HBM3E 的合约价材料未覆盖。")):
    hs = [hit(H[0]["text"], anchors=["营业收入", "营业总收入"], named=["江波龙"], arank=0)] if spec["n"] == 4 else H
    ob = "\n".join(h["text"] for h in hs)
    r_ok, r_msg = RQ.judge_recall(spec, hs)
    a_ok, a_msg, ex = RQ.judge_answer(spec, ans, hs)
    rows.append(dict(**spec, hits=hs, ans=ans, err=None,
                     hit=[m for m in spec["must"] if m in ob],
                     ok_r=r_ok, ok_a=a_ok, ok=(r_ok and a_ok),
                     msg_r=r_msg, msg_a=a_msg, secs=1.0, **ex))
out = ROOT / "_probe" / "_dry_十道题.md"
RQ.OUT = out
RQ.write(rows, {"ANTHROPIC_MODEL": "dry-run"}, "捏造", 2.0)
print("\n渲染出的前 60 行：")
for ln in out.read_text(encoding="utf-8").splitlines()[:60]:
    print("   " + ln)

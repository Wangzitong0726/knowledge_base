# -*- coding: utf-8 -*-
"""回归测试：答案侧 `must_ans`（点名专有名词）的匹配域。

**为什么必须测**：这条判据实测撞到过一条**奖励失败、惩罚成功**的形态——
第 2 题修正召回前，模型答「材料未覆盖」，因为要解释「没有美光的材料」而通篇
写「美光」→ 判过；修正召回后给出逐条引原文的好答案，全篇在讲美光、引 `[6][5][1]`，
只是没再写「美光」二字 → 判不过。

修法是：把**答案自己引用的那些席位**的公司名并进匹配域（引用标记 `[n]` 是模型的
显式内容归属）。**最容易自欺的一点**：把判据改松，让什么答案都过——所以下面
必须有两个方向的用例：引了别人家的块，**仍然要**判不过；什么都不引也不写公司名，
**仍然要**判不过。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from run_questions import answer_domain  # noqa: E402

checks = []


def chk(name, ok):
    checks.append((name, bool(ok)))
    print("  %s %s" % ("✅" if ok else "❌", name))


Q2 = "美光最近一期财报里，关于 HBM 的收入、产能或资本开支有哪些表述？"

MU = [{"company": "美光 Micron", "source": "sec", "text": "HBM3E 12-high ..."},
      {"company": "美光 Micron", "source": "sec", "text": "Singapore HBM packaging ..."}]
SK = [{"company": "SK 海力士", "source": "skhynix", "text": "HBM capacity ..."},
      {"company": "SK 海力士", "source": "skhynix", "text": "HBM capex ..."}]


def dom(ans, hits, q=Q2):
    return answer_domain(ans, q, hits)


print("── ① 引了那家公司的块 → 算点名（这就是修掉的那条假阴性）──")
ANS_SEATS = "产能侧：「Singapore: we broke ground on an HBM advanced packaging facility」[1]，" \
            "产品侧：「HBM3E 12-high represented the majority of our HBM shipments」[2]。"
chk("全篇不提「美光」二字，但引的 [1][2] 都是美光的块 → 认「美光」",
    "美光" in dom(ANS_SEATS, MU))
chk("同一篇答案，若引的是 SK 海力士的块 → **不认**「美光」",
    "美光" not in dom(ANS_SEATS, SK))

print("\n── ② 不用引用、直接写公司名 → 仍然算（老行为不许坏）──")
chk("答案里写了「美光」→ 认（不依赖引用）",
    "美光" in dom("美光的产能表述见材料。", MU))

print("\n── ③ 反例：既不说、也不引 → **仍然**判不过 ──")
chk("空洞答案（无引用、无公司名）→ 不认「美光」",
    "美光" not in dom("材料里没有 HBM 收入金额。", MU))

print("\n── ④ 引用越界不许崩 ──")
chk("引 `[99]` 而只有 2 席 → 忽略，不抛异常",
    "美光" not in dom("见 [99]。", MU))

print("\n── ⑤ 并进来的**只有公司名**，科目名判据不受影响 ──")
Q4 = "江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？"
JBL = [{"company": "江波龙", "source": "cninfo", "text": "一、营业总收入 | 2025 年半年度 10,195,655,370.19"}]
d = dom("这张表里两个口径的数值相同 [1]。", JBL, Q4)
chk("引江波龙的块 → 认「江波龙」（公司名并进来了）", "江波龙" in d)
chk("但**不会**因为引了江波龙的块就凭空认「营业总收入」（科目名不并进来）",
    "营业总收入" not in d)
chk("答案自己写了「营业总收入」→ 认（来自答案原文，不是引用）",
    "营业总收入" in dom("合并利润表里有一行「营业总收入」[1]。", JBL, Q4))

print("\n── ⑥ 抠问题原文那条防线还在 ──")
chk("答案只是**原样复述问题** → 复述部分被抠掉，不算点名",
    "美光" not in dom(Q2, MU))
chk("复述问题**之外**另行点名（「美光 Micron 的口径如下」）→ 仍算",
    "美光" in dom(Q2 + "美光 Micron 的口径如下。", MU))
chk("（边界）复述问题之后只补一句**不含公司名**的话 → 不算——"
    "那个「美光」来自被复述的问题，抠掉正是设计本意",
    "美光" not in dom(Q2 + "其口径如下。", MU))

bad = sum(1 for _n, ok in checks if not ok)
print("\n%s" % ("全部通过（%d/%d）" % (len(checks) - bad, len(checks))
                if not bad else "**有 %d 条不对**" % bad))
raise SystemExit(1 if bad else 0)

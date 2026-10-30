# -*- coding: utf-8 -*-
"""
阶段 5 · 十道题逐题跑检索 + 作答，存成 `outputs/十道题-检索记录.md`

**每道题都带一个「必须命中的原文」判据**（`must`），而不是靠人读答案像不像。
理由：模型写的答案再通顺，也只能证明它会写话，不能证明检索对了——
它完全可以**拿对的语言讲错的事**。所以判据挂在**检索到的原文**上：
少了那句原文，这题就算答得漂亮也记「未命中」。

判据故意写得很窄（一个句子、一个数），因为宽判据（「提到了 HBM」）
几乎必然命中，测不出东西。这和阶段 2 那三次「尺子错」是同一个纪律。

**⚠️ 上面这条纪律，本文件最初自己没做到（2026-10-04 复查后改正）。**
第一版判据是 Q2/Q5/Q7=`HBM`、Q3/Q9=`2024`、Q8=`管制`——一查词频就露馅：
`HBM` 538 块、`2024` **20,831** 块、`营业` 6,269 块。**任何块都能让它们过**，
所以当时的「10/10」实际测的是「**没崩**」，不是「答对」。真正的触发点是一张
截图：页面把第 4 题（江波龙口径）**诚实地答成了「材料未覆盖」**，
而该题的判据 `营业` 照样判「过」——**判据和事实当场打架**。
现在判据分两类：字面类 `must`（窄到 5–516 块级别）+ **结构类**
`min_companies` / `need_lib` / `forbid_lib`。结构类是全景题的关键——
判 `HBM` 的话，**一份报告就能让「跨三家公司」「同时有规则和财报」判过**。

第 10 题是**故意设计的必败题**：一手价格在付费墙后（决策三）。
它的通过标准是回答里出现「材料未覆盖」，**给出任何数字都算答错**——
包括给一个碰巧对上的数字，因为对错不该由运气决定。
"""
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "outputs" / "十道题-检索记录.md"

Q = [
    dict(n=1, lib="B", k=8,
         q="3A090.c 的管制门槛是什么？",
         must=["greater than 2 gigabytes per second per square millimeter"],
         why="基础事实。判据要的是**管制门槛**（2），不是例外上限（3.3）——两个数混了就答反了。"),
    dict(n=2, lib="A", k=8,
         q="美光最近一期财报里，关于 HBM 的收入、产能或资本开支有哪些表述？",
         must=["HBM"], must_ans=["美光"], min_from_company={"美光": 4},
         why="表格块召回（课程 p24）。"
         "**`min_from_company={'美光':4}` 是 2026-10-04 才补上的**：原先这里写的是 "
         "`require_company=['美光']`，但 `judge()` **从来没读它**（结构判据只实现了 "
         "`min_companies`/`need_lib`/`forbid_lib`）——又是一个「声明了却没接线的开关」。"
         "于是本题实际只判 `HBM`，而 `HBM` 在库里 538 块，**任何块都能让判据过**。"
         "实测：8 个席里 SK 海力士占 6、三星 1、**美光只占 1**，而问题问的就是美光一家。"
         "补上后改为「美光须占 ≥4 席」——只要求「出现过」不够：8 条里出现 1 条也算出现。"),
    dict(n=3, lib="B", k=8,
         q="2024 年 12 月以前 HBM 受出口管制吗？是哪一份规则改变了这一点？",
         must=["96790"], need_lib={"B": 1},
         why="版本陷阱（课程 p50）：管制前后是**两份不同的规则文本**，得说清是哪一份改的。"
             "判据用 FR 文号 **96790**（全库仅 5 块）而不是 `2024`——后者出现 20,831 次，"
             "**写「2024」等于没写**，任何块都能让它过。"),
    dict(n=4, lib="A", k=8,
         q="江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？",
         must=["营业总收入"], must_ans=["营业收入", "营业总收入"],
         why="口径陷阱（课程 p29）。判据从 `营业`（6,269 块）收窄到 `营业总收入`（101 块）——"
             "口径题要的是那个具体科目名，不是「营业」两个字。"
             "**`must_ans` 要求答案里两个科目名都出现**：问的是**两者的差别**，"
             "答案只说其中一个，等于把问题答了一半。"
             "（2026-10-12 加：这两个名字相近，必须**各说各的**，见 data/口径表.md）"),
    dict(n=5, lib="A+B", k=10,
         q="出口管制对内存市场的影响涉及哪几个方面？",
         must=["HBM"], need_lib={"A": 1, "B": 1},
         why="多主题揉成一个向量（课程 p36）。既然问「影响涉及哪几个方面」，"
             "就得**同时**有规则文本和厂商财报两边，否则答案只有管制条文的半边。"),
    dict(n=6, lib="A+B", k=10,
         q=("我最近在看内存这块，感觉这两年 HBM 突然就热起来了，"
            "好多做存储的公司都在讲。我想知道，美国那边的出口管制到底卡的是什么？"
            "是卡整个 DRAM，还是只卡 HBM？卡的具体是哪一类，有没有一个明确的技术线？"),
         must=["3A090"], need_lib={"B": 1},
         why="长口语问题，铺垫在投票（课程 p38）——真正的问句在最后一句。"
             "「卡的是什么」必须落到 ECCN 上，故判 `3A090`（516 块，够窄）。"),
    dict(n=7, lib="A", k=14, panorama=True,
         q="三星、SK 海力士、美光三家最近一期报告对 HBM 供需与产能的表述有哪些共性和差异？",
         must=["HBM"], min_companies=3,
         must_ans=["三星", "海力士", "美光"],
         require_companies={"三星": "HBM", "SK 海力士": "HBM", "美光": "HBM"},
         why="全景题 1：**碎块拼不出全景**（课程 p63）。判据必须是**结构性的**，"
             "而且**要点名**——`min_companies=3` 数的是「任意三家」，"
             "实测 14 席实得 {SK海力士, 东芯股份, 佰维存储, 美光}=4 家就判过了，"
             "**可三星一条都没有**（模型自己都在答案里写「三星的表述材料完全未覆盖」）。"
             "这与最初那个「假 10/10」是同一个病，所以 2026-10-04 补 `require_companies`，"
             "要求**问题点名的三家逐一出现**。"),
    dict(n=8, lib="A", k=14, panorama=True,
         q="A 股内存产业链公司如何披露出口管制对自身经营的影响？",
         must=["管制"], min_companies=3, forbid_lib="B",
         why="全景题 2：同上，且考察中文语料里的同类表述。`forbid_lib=B` 是必须的——"
             "问的是**A 股公司怎么披露**，若前 k 被 BIS 规则文本占住，答案就答成了「管制是什么」"
             "而不是「公司怎么说」。"),
    dict(n=9, lib="A+B", k=10,
         q="出口管制规则的历次修订时点，与厂商财报里提到的价格或 ASP 变化能对上吗？",
         must=["2024"], need_lib={"A": 1, "B": 1},
         why="跨库时间线（课程 p51）。**这题的 `2024` 仍是宽判据，故意留着**："
             "它想测的是「跨库」，所以真正的判据是 `need_lib`——"
             "实测原配置前 10 条**全是 BIS 规则**、一条财报都没有，「对得上吗」根本无从谈起。"),
    dict(n=10, lib="A+B", k=10, must_fail=True,
         q="HBM3E 现在的合约价是多少美元？",
         must=["材料未覆盖"],
         why="**诚实的失败**（课程 p94）：一手价格在付费墙后。答出一个数就是错的，"
             "哪怕那个数碰巧对——对错不该由运气决定。"),
]


# 库 A = 公司财报，库 B = 管制规则文本。跨库题必须两边都够得着。
LIB_SOURCES = {"A": {"cninfo", "szse", "sec", "samsung", "skhynix"},
               "B": {"fedreg", "ecfr", "govinfo"}}


# ══════════════════════════════════════════════════════════════════════
# 判分：**召回一本账、答案另一本账**
# ══════════════════════════════════════════════════════════════════════
#
# 为什么必须拆开（课件 p94）：那一页的工具账本是
# `search 23 / read 14 / find_table 2 / graph 1`——**召回与答案用的是不同的工具、
# 该分别算账**。原来只有一个 `judge()`，判据全挂在召回原文上，于是
# 「召回对了」与「答对了」被记成同一件事。代价是实测过的：第 4 题（江波龙口径）
# 页面把答案**诚实地**写成「材料未覆盖」，而判据 `营业` 照样判「过」——
# 两本账混在一起，答案这一本根本看不见。
#
# 拆分后：
#   · `judge_recall(spec, hits)`      —— 该捞的原文捞上来了没有
#   · `judge_answer(spec, ans, hits)` —— 答案有没有真的用上，**有没有自己造数**
#
# ⚠️ 答案侧的判据必须**先把问题原文从匹配域里抠掉**。答案是模型写的，
#    它几乎必然复述问题；不抠的话「答案里出现了『三星』」很可能只是把问题抄了一遍
#    ——**判据被问题自己满足**。截图脚本连栽两次就是这个坑
#    （见 `save_qa_snapshots.py: seats_by_company` 的两版自陈）。


def judge_recall(spec, hits):
    """判**召回**。返回 (是否通过, 说明)。

    **判据分两类，缺一不可**：
      · 字面类 `must`——必须逐字出现在召回的原文里（防模型自己圆）；
      · 结构类 `min_companies` / `need_lib` / `forbid_lib`——
        以及 2026-10-04 补的 `require_companies` / `min_from_company`（见下）。
    为什么非要结构类：原判据几乎全是 `HBM` / `2024` / `营业` 这种词，
    在库里的出现次数据统计是 538 / 20,831 / 6,269 —— **任何块都能让它们过**，
    于是「10/10」实际测的是「没崩」，不是「答对」。全景题尤其荒唐：
    判 `HBM` 的话，**一份报告就能让「跨三家公司」判过**。
    """
    msgs = []
    # ⚠️ 必败题在召回侧**不设字面判据**（2026-10-12 修）。它的 `must` 写的是
    # `材料未覆盖`——那是**答案里的话**，语料里当然一个字都没有，于是召回侧
    # 永远判「缺判据原文」。这是把答案侧的判据错挂到了召回侧，
    # 正是本次拆两本账要治的那个病：**判据挂错了账本，就永远判不对**。
    if spec.get("must_fail"):
        return True, "✅ 必败题：判据在答案侧（语料里没有一手价格，本来就不该有这句话）"
    blob = "\n".join(h["text"] for h in hits)
    missing = [m for m in spec.get("must", []) if m not in blob]
    if missing:
        msgs.append(f"缺判据原文 {missing}")
    if spec.get("min_companies"):
        comps = {h["company"] or h["source"] for h in hits}
        if len(comps) < spec["min_companies"]:
            msgs.append(f"公司数 {len(comps)}<{spec['min_companies']}（{sorted(comps)}）")
    for lib, need in (spec.get("need_lib") or {}).items():
        got = {h["source"] for h in hits} & LIB_SOURCES[lib]
        if len(got) < need:
            msgs.append(f"库{lib}只有 {len(got)} 个来源（{sorted(got) or '无'}）")
    if spec.get("forbid_lib"):
        bad = {h["source"] for h in hits} & LIB_SOURCES[spec["forbid_lib"]]
        if bad:
            msgs.append(f"混进了库{spec['forbid_lib']} {sorted(bad)}")

    # ⚠️ 以下两条是 2026-10-04 补的，因为**原来的判据漏判了两道题**。
    #
    # 病根：`min_companies=3` 数的是「任意三家公司的块」，不是「问题点名的那三家」。
    # 第 7 题问「三星、SK 海力士、美光」，实得 {SK海力士, 东芯股份, 佰维存储, 美光}——
    # 凑够 4 家，判过；可**三星一条都没有**（模型自己也说了「材料未覆盖」）。
    # 第 2 题问「美光一家」，8 个席里 SK 海力士占 6、美光只占 1，同样判过。
    # 这两道题当时记成 ✅，实际是**假过**——同一批题里出现两次的同一类错，
    # 与最初那个「假 10/10」是同一个病：**判据能被满足，但没满足问题**。
    comps = [h["company"] or h["source"] for h in hits]

    # 点名公司必须出现**且出现在切题的块里**。
    # 只要求「公司出现」还是不够——第二次实测：补上 `require_companies=['三星',…]` 后，
    # 第 7 题判过，可那两条三星块是 `VI. Outstanding shares`（股本表），
    # **与 HBM 供需毫无关系**。判据又一次被「沾了个名字的无关块」满足。
    # 所以写成 dict：{公司: 该块必须同时含的主题词}。主题词由**问题本身**给出
    # （第 7 题问的就是「HBM 供需与产能」），不是照检索结果反推。
    want = spec.get("require_companies") or []
    if isinstance(want, dict):
        miss_c = []
        for name, topic in want.items():
            ok = any(name in (h["company"] or h["source"]) and topic in h["text"]
                     for h in hits)
            if not ok:
                n_name = sum(1 for h in hits if name in (h["company"] or h["source"]))
                miss_c.append(f"{name}(命中{n_name}块但无一含「{topic}」)" if n_name
                              else f"{name}(一块都没有)")
    else:
        miss_c = [c for c in want if not any(c in x for x in comps)]
    if miss_c:
        msgs.append(f"点名公司缺失 {miss_c}（实得 {sorted(set(comps))}）")

    for name, need in (spec.get("min_from_company") or {}).items():
        got = sum(1 for x in comps if name in x)
        if got < need:
            msgs.append(f"{name} 只占 {got}/{len(hits)} 席（需 ≥{need}）")

    return (not msgs), ("✅ 召回命中" if not msgs else "❌ " + "；".join(msgs))


# ── 答案侧 ────────────────────────────────────────────────────────────

# 一个「数字」。前后都不能是字母或数字：`3A090.c` 里的 `3` 和 `090` **都不是数字**，
# 它是型号的一部分。不这么卡的话，答案里写个型号就会被当成「造了个数」。
# （和 `retrieve.expand_queries` 里 `_MARK` 吃掉型号首字符是同一类坑：
#  把假设的排版/词形当成事实。）
_NUM = re.compile(r"(?<![0-9A-Za-z.])(\d+(?:,\d{3})*(?:\.\d+)?)(?![0-9A-Za-z])")


def _key(t):
    """数字的**比较键**：去掉千分位逗号。

    ⚠️ 上面那条正则只让**合规的千分位**（逗号后正好 3 位数字）进入数字。
    旧版写 `[\\d,]*`，贪婪地把尾随逗号也吞了——原文
    `(89 FR 96790, December 5, 2024)` 切出 `96790,` 和 `5,`，
    答案里句末写 `96790。` 切出 `96790`，按原样比**永远不相等**。
    结果一个真有出处的数被报成「模型自己带来的数」（Q3/Q9 实测撞到），
    还凭空多出个数值 `5,`。**同一个坑的第三种形态：把排版当成了事实。**

    去逗号是为了容忍 `1,234` 与 `1234` 两种写法（语料与答案排版不同很正常），
    不是放宽判据：真正的差别是数字本身，千分位只是排版。
    """
    return t.replace(",", "")


def _norm(s):
    """去掉全部空白，用于「答案有没有复述问题」这类**排版无关**的比较。"""
    return re.sub(r"\s+", "", s or "")


# 模型在答案里用的席位引用标记 `[6]`、`[5][7]`。
_CITE = re.compile(r"\[(\d{1,3})\]")


def answer_domain(ans, q, hits=()):
    """答案判据的匹配域 = **答案 − 问题原文 ＋ 所引席位的公司名**。

    去空白再相减，避免排版差异让抠除失效。
    ⚠️ 已知边界：模型**改写**问题（而非原样复述）时，这段文字抠不掉，判据仍可能被
       这次复述满足。所以答案侧的判据只用来认**专有名词**（公司名、科目名），
       它们换个说法也还是这几个字；不拿它去判句子级的意思。

    **为什么要把「所引席位的公司名」并进来**（2026-10-15 加）：
    实测撞到一条**奖励失败、惩罚成功**的判据。第 2 题问「美光最近一期财报里……」，
    `must_ans=["美光"]`。修正召回之前，模型答的是「材料未覆盖」，**因为要解释
    「没有美光的材料」，所以通篇在写「美光」→ 判过**；修正召回之后，模型给出一篇
    逐条引原文、且正确指出「HBM 收入金额与资本开支材料里没有」的**好答案**，
    反而**判不过**——因为它全篇在讲美光、引 `[6][5][1]`，就是没再写「美光」二字。

    这条判据的**意图**是「答案讲的是这家公司，不是别家」，而 `[6]` 是模型**显式的
    内容归属**：它说「这句话出自第 6 席」。第 6 席是美光的块，答案就是在讲美光。
    要求字面出现，是把**排版约定当成了内容要求**——与 `_key` 那条注释里
    「把排版当成了事实」是同一个坑的第四种形态。

    **这不是放宽**：并进来的是**答案自己声明了归属的那些席位**的公司名，不是
    召回里所有公司的名字。一篇引 SK 海力士的块来答「美光」的答案，照样判不过；
    不作任何引用、也不写公司名的答案，同样判不过。判据仍然是**答案侧**的：
    它要求的从「写没写这两个字」变成「有没有把话算在这家公司账上」。

    ⚠️ 已知副作用：当召回**整体只剩点名的公司**时（第 2 题正是，8/8 美光），
       这条判据会近乎自动成立。该题的实质判据是召回侧的 `min_from_company`，
       这里只补一道「答案有没有把内容归给别人」的防线。别把它当强判据用。
    """
    a = _norm(ans)
    if q:
        a = a.replace(_norm(q), "")
    for n in {int(x) for x in _CITE.findall(ans or "")}:
        if 1 <= n <= len(hits):
            h = hits[n - 1]
            a += _norm((h.get("company") or "") + (h.get("source") or ""))
    return a


def value_numbers(s):
    """一段文字里的**数值型数字**：带千分位 / 带小数点 / 至少 5 位。

    为什么这么定：`2024`、「3 个方面」是年份与个数，**复述问题就会有**，
    追不到出处不算错；而 `10,195,655,370.19`、`96790` 出现在答案里
    就是一个**事实主张**，必须有出处。这正是老师那句
    「**正确页码不能证明数字归属正确**」：页码对了，不代表这一页里有这个数。
    """
    out = []
    for m in _NUM.finditer(s or ""):
        t = m.group(1)
        if ("," in t) or ("." in t) or len(t.replace(",", "")) >= 5:
            out.append(t)
    return out


def number_attribution(ans, q, hits):
    """答案里每个数值型数字，能不能在**召回的语料**里原样找到；找到的记下是第几席。

    返回 `(有出处 [(数字, [席号…])], 无出处 [数字…])`。
    问题里出现过的数字先剔掉——那是复述，不是主张。

    ⚠️ 已知道具：把 `10,195,655,370.19` 写成 `101.96 亿元`（换算了单位）会被记成
       「无出处」。**这是故意留着的不精确**：宁可多报一次，也不放过一个查不到的数。
       误差方向是「显得比实际差」，不是「显得比实际好」。
    """
    asked = {_key(n) for n in value_numbers(q)}
    found = {}
    for i, h in enumerate(hits, 1):
        for n in dict.fromkeys(value_numbers(h["text"])):
            found.setdefault(_key(n), [])
            if i not in found[_key(n)]:
                found[_key(n)].append(i)
    have, orphan = [], []
    for n in dict.fromkeys(value_numbers(ans)):
        k = _key(n)
        if k in asked:
            continue                       # 问题里就有 → 复述，不追出处
        if k in found:
            have.append((n, found[k]))     # 展示答案**原样**的写法，比对用键
        else:
            orphan.append(n)
    return have, orphan


def judge_answer(spec, ans, hits):
    """判**答案**。返回 (是否通过, 说明, 附加 dict)。

    三条判据，全部机械可复现：
      ① **数字归属核对**——答案里的数值型数字能不能回查到某一席语料（见
         `number_attribution`）。查不到的就是**模型自己带来的数**，这一条正是
         「正确页码不能证明数字归属正确」的答案侧对应物。
      ② **`must_ans`**——答案里必须出现的专有名词（公司名 / 科目名），
         匹配域是**抠掉问题原文之后**的答案（见 `answer_domain`）。
         只在问题确实要求点名时才设这一项；没设的题**不假装判过**，
         记录里写明「本题未设答案判据，答案栏只做数字归属核对」。
      ③ **必败题**——见第 10 题。
    """
    msgs = []
    extra = {}

    if spec.get("must_fail"):
        nums = re.findall(r"\d[\d,\.]*\s*(?:美元|USD|\$|元)", ans or "")
        if "材料未覆盖" in (ans or "") and not nums:
            return True, "✅ 诚实承认未覆盖", extra
        return False, (f"❌ 给出了数字 {nums[:3]}" if nums else "❌ 未明确承认未覆盖"), extra

    dom = answer_domain(ans, spec["q"], hits)
    want = spec.get("must_ans")
    if want:
        extra["缺答案专名"] = [w for w in want if _norm(w) not in dom]
    extra["无答案判据"] = not want

    have, orphan = number_attribution(ans, spec["q"], hits)
    extra["数字有出处"] = have
    extra["数字无出处"] = orphan

    if orphan:
        msgs.append("答案有 %d 个数在语料里找不到出处：%s"
                    % (len(orphan), "、".join(orphan[:5])
                       + ("…" if len(orphan) > 5 else "")))
    if want and extra["缺答案专名"]:
        msgs.append("答案未点名 %s" % extra["缺答案专名"])

    return (not msgs), ("✅ 答案合规" if not msgs else "❌ " + "；".join(msgs)), extra


def judge(spec, hits, ans):
    """两本账合成一个字符串（兼容旧调用）。真正的判分在 `judge_recall`/`judge_answer`。"""
    r_ok, r_msg = judge_recall(spec, hits)
    a_ok, a_msg, _x = judge_answer(spec, ans, hits)
    return (r_ok and a_ok), f"召回 {r_msg}｜答案 {a_msg}"


def run(only=None):
    from retrieve import Retriever
    import serve_qa as S
    env, src = S.load_env()
    R = Retriever()

    rows, t_all = [], time.time()
    for spec in Q:
        if only and spec["n"] not in only:
            continue
        t0 = time.time()
        # expand=True 不是可选项：Q1 的判据原文（`greater than 2 gigabytes per second
        # per square millimeter`）**只靠原问题一辈子进不了前 8**——条文里没有「门槛」
        # 这个词，它写的是 `memory bandwidth density`。把「抽象的管制说法」翻成
        # 「条文实际用的词」是检索该干的活，不该要求用户先知道条文怎么写。
        # panorama=... 给全景题开「按公司取证」通道（课件 p61–63）。非全景题不开，
        # 排序与加这条通道之前逐位相同。
        hits = R.search(spec["q"], k=spec["k"], expand=True,
                        panorama=bool(spec.get("panorama")))
        blob = "\n".join(h["text"] for h in hits)
        hit = [m for m in spec["must"] if m in blob]
        ans, err = S.call_model(env, spec["q"], hits)
        # **两本账分开算**（课件 p94）——不再合成一个 `verdict` 就完事
        r_ok, r_msg = judge_recall(spec, hits)
        a_ok, a_msg, a_extra = judge_answer(spec, ans, hits)
        rows.append(dict(**spec, hits=hits, ans=ans, err=err, hit=hit,
                         ok_r=r_ok, ok_a=a_ok, ok=(r_ok and a_ok),
                         msg_r=r_msg, msg_a=a_msg, secs=round(time.time() - t0, 1),
                         **a_extra))
        print(f"  第 {spec['n']:2d} 题 [{spec['lib']:4s}] {r_msg} ｜ {a_msg}  "
              f"召回 {len(hits)} 条  {rows[-1]['secs']}s")

    write(rows, env, src, time.time() - t_all)
    return rows


def write(rows, env, src, secs):
    import retrieve as _r
    import serve_qa as S          # 借它的 _ng() 把 None 渲染成「—」
    OUT.parent.mkdir(parents=True, exist_ok=True)
    L = ["# 十道题 · 逐题检索记录", "",
         f"- 生成：{time.strftime('%Y-%m-%d %H:%M:%S')}，总用时 {secs:.0f} 秒",
         f"- 检索引擎：① BM25 + 稠密向量双通道，**RRF 融合**"
         f"（K={_r.RRF_K}，每通道先各取前 {_r.POOL}）"
         f"；② **查询改写**——原问题 1 票、改写查询每票 0.6，把「抽象的管制说法」"
         f"翻成条文实际用词；③ **同文档限 {_r.DOC_CAP} 块**——防一份文件霸榜；"
         "④ **行标签锚定通道**——问题点到口径表里的科目名或引号词时，"
         "按**行的第一个 ` | ` 段**去那张表里找（正文提到科目名不算）；"
         "⑤ **按公司取证 + 轮转发牌**——问题点名了哪几家公司，就叫每家各自出证。",
         "- ②③④⑤ 都是实测逼出来的，不是先验设计：去掉②，第 1 题的判据原文进不了前 8；"
         "去掉③，前 8 里 5 块来自同一份《联邦公报》，把定义块挤到 24 名开外；"
         "去掉④，第 4 题召不回 `营业总收入`；去掉⑤，第 2 题美光只剩 1/8 席、"
         "第 7 题三星 0 条、第 8 题混进 7 条 BIS 规则文本。",
         f"- 作答模型：`{env.get('ANTHROPIC_MODEL','?')}`（配置来源：{src}）",
         "- **召回一本账、答案另一本账**（课件 p94 的工具账本："
         "`search 23 / read 14 / find_table 2 / graph 1`）——",
         "  召回判的挂在**检索到的原文**上（答案通顺只证明会写话，不证明检索对）；",
         "  答案判的是**答案有没有真的用上、有没有自己造数**（数字归属核对）。",
         "  两本账合成一个「通过」是上一版的错：第 4 题答案诚实写了「材料未覆盖」，",
         "  而判据照样判「过」——混在一起就看不见答案这一本。", "",
         "## 总览", "",
         "| # | 库 | 召回判定 | 答案判定 | 席位数 | 用时 | 题目 |",
         "|---|---|---|---|---:|---:|---|"]
    for r in rows:
        q = r["q"] if len(r["q"]) <= 26 else r["q"][:26] + "…"
        L.append(f"| {r['n']} | {r['lib']} | {r['msg_r']} | {r['msg_a']} "
                 f"| {len(r['hits'])} | {r['secs']}s | {q} |")
    nr = sum(1 for r in rows if r["ok_r"])
    na = sum(1 for r in rows if r["ok_a"])
    nb = sum(1 for r in rows if r["ok"])
    L += ["", f"**召回通过 {nr}/{len(rows)}　答案通过 {na}/{len(rows)}　"
              f"两本都过 {nb}/{len(rows)}**",
          "", "> 「答案通过」只统计**设了答案判据的**题（`must_ans` 与必败题）"
          "加上数字归属核对；",
          "> 没设答案判据的题，答案栏只做数字归属核对，记录里逐题写明，"
          "**不冒充「已判过」**。", "", "---", ""]

    for r in rows:
        # **表格定位通道**（课件 p91「要回到那张表」）：只在问题点名了科目时才开。
        # 开了就写清楚「锚是什么、限定在哪家公司、命中几席」——这条通道**会改变排序**，
        # 改了就必须留在记录里，不能只活在代码里（判据和它的显示必须是同一件事）。
        anc_hits = [h for h in r["hits"] if h.get("anchor_rank") is not None]
        anc_line = []
        if anc_hits:
            anc_line = ["- 表格定位通道（按**行标签**锚定，正文提到科目名不算）：锚 "
                        + "、".join(f"`{a}`" for a in sorted(
                            {a for h in anc_hits for a in (h.get("anchors") or [])}))
                        + "；限定公司 "
                        + ("、".join(anc_hits[0].get("anchor_named") or []) or "未限定")
                        + f"；进前 {len(r['hits'])} 的 {len(anc_hits)} 席"]
        # **按公司取证**（课件 p61–63）：全景题按公司分席位，这里把「谁出得起证、
        # 谁缺席」**显式列出来**。缺席必须写在脸上——原来只报一句「三星(一块都没有)」，
        # 而证据层还是一片扁平的 [1]…[14]，读的人看不出缺的是哪一家。
        comp_names = r["hits"][0].get("company_named") if r["hits"] else None
        if r.get("panorama") and comp_names:
            have = {h["company"] or h["source"] for h in r["hits"]}
            seats = Counter(h["company"] or h["source"] for h in r["hits"])
            absent = [c for c in comp_names if c not in have]
            anc_line += [
                f"- **按公司取证**：点名 {len(comp_names)} 家（"
                + "、".join(comp_names) + f"），出得起证 **{len(comp_names) - len(absent)} 家**",
                f"  - 各得席位："
                + "、".join(f"{c}×{seats[c]}" for c in comp_names if seats.get(c))
                + ("；补位（未被点名）" + "、".join(
                    f"{k}×{v}" for k, v in seats.items() if k not in comp_names)
                   if any(k not in comp_names for k in seats) else ""),
                f"  - ⚠️ **缺席**：{'、'.join(absent) if absent else '（无）'}"
                + ("　← 库里有材料却挤不进来，属覆盖缺口；没有材料则是出证来源缺口"
                   if absent else "")]
        L += [f"## 第 {r['n']} 题 · 召回 {r['msg_r']}｜答案 {r['msg_a']}", "",
              f"**问题**：{r['q']}", "",
              f"- 库：{r['lib']}｜考察：{r['why']}",
              f"- 实际进检索的查询（原问题 + 模型改写）："
              + " ｜ ".join(f"`{x}`" for x in (r["hits"][0]["queries"] if r["hits"] else [r["q"]])),
              (f"- 判据原文：`{r['must']}` → 命中 {r['hit'] or '无'}"
               if not r.get("must_fail") else
               "- 判据原文：（必败题——判据在**答案**侧：须承认材料未覆盖且不给数）"),
              f"- 附加结构判据："
              + ("；".join(filter(None, [
                  f"跨 ≥{r['min_companies']} 家公司" if r.get("min_companies") else "",
                  "必须含 " + "、".join(f"库{k}≥{v}" for k, v in (r.get("need_lib") or {}).items()) if r.get("need_lib") else "",
                  f"不得含库{r['forbid_lib']}" if r.get("forbid_lib") else "",
                  # ⚠️ 这两条 2026-10-04 补渲染。此前判据已生效却**不显示**，
                  # 于是第 2 题记录里写着「附加结构判据：无」，判定却是
                  # 「美光 只占 1/8 席（需 ≥4）」——**看着像没判据就判了不过**。
                  # 判据和它的显示必须是同一件事，否则记录本身就不可信。
                  ("点名公司须出现且**切题**：" + "、".join(
                      f"{k}（正文须含「{v}」）" for k, v in r["require_companies"].items())
                   if isinstance(r.get("require_companies"), dict) else
                   "点名公司须出现：" + "、".join(r["require_companies"])
                   if r.get("require_companies") else ""),
                  ("指定公司占席下限：" + "、".join(
                      f"{k}≥{v}" for k, v in r["min_from_company"].items())
                   if r.get("min_from_company") else ""),
                  "必败题（须承认材料未覆盖）" if r.get("must_fail") else "",
                ])) or "无"),
              f"- 实际来源构成：{sorted({h['source'] for h in r['hits']})}",
              f"- 实际公司构成：{sorted({h['company'] or h['source'] for h in r['hits']})}",
              *anc_line,
              f"- 召回 {len(r['hits'])} 条，用时 {r['secs']}s", "",
              "### 模型作答（非原文，须逐条核 [n]）", ""]
        if r["err"]:
            L += [f"> ⚠️ 作答失败：{r['err']}", ""]
        L += ["```", (r["ans"] or "(无)").strip(), "```", "",
              "### 判分（两本账）", "",
              f"- **召回判定**：{r['msg_r']}",
              f"- **答案判定**：{r['msg_a']}",
              "- **数字归属核对**（答案里的数值型数字 → 第几席语料里有原样的数）："]
        have, orph = r.get("数字有出处") or [], r.get("数字无出处") or []
        if not have and not orph:
            L += ["  - 本答案没有给出数值型数字（年份、个数这类不算——它们不进这项核对）"]
        for n, seats in have:
            L += [f"  - `{n}` → 第 {'、'.join(str(s) for s in seats)} 席"]
        for n in orph:
            L += [f"  - ⚠️ `{n}` → **语料里找不到出处**（模型自己带来的数）"]
        gap = []
        if not r["ok_r"]:
            gap.append(f"召回：{r['msg_r']}")
        if r.get("缺答案专名"):
            gap.append("答案未点名：" + "、".join(r["缺答案专名"]))
        if orph:
            gap.append("答案里无出处的数：" + "、".join(orph[:8])
                       + ("…" if len(orph) > 8 else ""))
        L += [f"- **未覆盖项**：{'；'.join(gap) if gap else '无'}"]
        if r.get("无答案判据"):
            L += ["- ⚠️ **本题未设答案专名判据**（问题没有要求点名某个对象），"
                  "答案栏只做数字归属核对——**不冒充「答案已判过」**。"]
        if r.get("must_ans"):
            L += [f"- 答案须点名的对象：{'、'.join(r['must_ans'])}"
                  f"（匹配域已抠掉问题原文，防判据被问题自己满足）"]
        L += ["", "### 检索到的语料原文"
              + ("（**按公司分组**——全景题的证据要按公司看，不是一串扁平编号）"
                 if r.get("panorama") else ""), ""]
        cur = None
        for i, h in enumerate(r["hits"], 1):
            # 全景题按公司分小节：读的人要能一眼看出「这一家说了什么」，
            # 而不是从 14 条里自己数哪几条是同一家。
            if r.get("panorama") and (h["company"] or h["source"]) != cur:
                cur = h["company"] or h["source"]
                L += [f"#### {cur}", ""]
            prov = f"{h['company'] or h['source']} · {h['title'] or h['file']}"
            if h["section"]:
                prov += f" · {h['section']}"
            prov += f" · p{h['page_start']}"
            L += [f"**[{i}]** {prov}",
                  f"`rrf={h['score']:.4f} 通道={h['channels'] or '-'} "
                  f"bm25#{S._ng(h['bm25_rank'])} dense#{S._ng(h['dense_rank'])} "
                  f"sim={S._ng(h['dense_sim'], '%.4f')}`",
                  f"<{h['url']}>" if h["url"] else "", "",
                  "> " + h["text"].replace("\n", "\n> "), ""]
        L += ["---", ""]
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"\n✓ {OUT}")


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    only = [int(x) for x in sys.argv[1:] if x.isdigit()] or None
    run(only)

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
import sys
import time
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
         must=["HBM"], min_from_company={"美光": 4}, why="表格块召回（课程 p24）。"
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
         must=["营业总收入"],
         why="口径陷阱（课程 p29）。判据从 `营业`（6,269 块）收窄到 `营业总收入`（101 块）——"
             "口径题要的是那个具体科目名，不是「营业」两个字。"),
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


def judge(spec, hits, ans):
    """判定一道题。返回 (是否通过, 说明)。

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
    blob = "\n".join(h["text"] for h in hits)
    if spec.get("must_fail"):
        import re as _re
        nums = _re.findall(r"\d[\d,\.]*\s*(?:美元|USD|\$|元)", ans or "")
        if "材料未覆盖" in (ans or "") and not nums:
            return True, "✅ 诚实承认未覆盖"
        return False, f"❌ 给出了数字 {nums[:3]}" if nums else "❌ 未明确承认未覆盖"

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

    return (not msgs), ("✅ 判据命中" if not msgs else "❌ " + "；".join(msgs))


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
        hits = R.search(spec["q"], k=spec["k"], expand=True)
        blob = "\n".join(h["text"] for h in hits)
        hit = [m for m in spec["must"] if m in blob]
        ans, err = S.call_model(env, spec["q"], hits)
        ok, verdict = judge(spec, hits, ans)
        rows.append(dict(**spec, hits=hits, ans=ans, err=err,
                         hit=hit, ok=ok, verdict=verdict,
                         secs=round(time.time() - t0, 1)))
        print(f"  第 {spec['n']:2d} 题 [{spec['lib']:4s}] {verdict}  "
              f"召回 {len(hits)} 条  {rows[-1]['secs']}s")

    write(rows, env, src, time.time() - t_all)
    return rows


def write(rows, env, src, secs):
    import retrieve as _r
    import serve_qa as S          # 借它的 _ng() 把 None 渲染成「—」
    OUT.parent.mkdir(parents=True, exist_ok=True)
    L = ["# 十道题 · 逐题检索记录", "",
         f"- 生成：{time.strftime('%Y-%m-%d %H:%M:%S')}，总用时 {secs:.0f} 秒",
         f"- 检索三件套：① BM25 + 稠密向量双通道，**RRF 融合**"
         f"（K={_r.RRF_K}，每通道先各取前 {_r.POOL}）"
         f"；② **查询改写**——原问题 1 票、改写查询每票 0.6，把「抽象的管制说法」"
         f"翻成条文实际用词；③ **同文档限 {_r.DOC_CAP} 块**——防一份文件霸榜。",
         "- ②③ 都是实测逼出来的，不是先验设计：去掉②，第 1 题的判据原文进不了前 8；"
         "去掉③，前 8 里 5 块来自同一份《联邦公报》，把定义块挤到 24 名开外。",
         f"- 作答模型：`{env.get('ANTHROPIC_MODEL','?')}`（配置来源：{src}）",
         "- **判据挂在检索到的原文上，不挂在答案上**——答案通顺只证明会写话，",
         "  不证明检索对；模型完全可以拿对的语言讲错的事。", "",
         "## 总览", "",
         "| # | 库 | 判定 | 召回 | 用时 | 题目 |", "|---|---|---|---:|---:|---|"]
    for r in rows:
        q = r["q"] if len(r["q"]) <= 26 else r["q"][:26] + "…"
        L.append(f"| {r['n']} | {r['lib']} | {r['verdict']} | {len(r['hits'])} "
                 f"| {r['secs']}s | {q} |")
    n_ok = sum(1 for r in rows if r["ok"])
    L += ["", f"**通过 {n_ok}/{len(rows)}**", "", "---", ""]

    for r in rows:
        L += [f"## 第 {r['n']} 题 · {r['verdict']}", "",
              f"**问题**：{r['q']}", "",
              f"- 库：{r['lib']}｜考察：{r['why']}",
              f"- 实际进检索的查询（原问题 + 模型改写）："
              + " ｜ ".join(f"`{x}`" for x in (r["hits"][0]["queries"] if r["hits"] else [r["q"]])),
              f"- 判据原文：`{r['must']}` → 命中 {r['hit'] or '无'}",
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
              f"- 召回 {len(r['hits'])} 条，用时 {r['secs']}s", "",
              "### 模型作答（非原文，须逐条核 [n]）", ""]
        if r["err"]:
            L += [f"> ⚠️ 作答失败：{r['err']}", ""]
        L += ["```", (r["ans"] or "(无)").strip(), "```", "",
              "### 检索到的语料原文", ""]
        for i, h in enumerate(r["hits"], 1):
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

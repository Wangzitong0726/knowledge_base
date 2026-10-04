# -*- coding: utf-8 -*-
"""把问答页的代表性状态存成 HTML，供截图/存档。

选题标准：每张图证明一件**不同**的事，且**不藏失败的**。
  · 1 判据命中——检索能把条文原句捞上来（Q1）；
  · 2 诚实失败——够不着时敢说够不着（Q10 必败题）；
  · 3 口径题未命中——中文财报题没召回到 `营业总收入`，页面如实显示「材料未覆盖」；
  · 4 全景题**失败**——问三星/SK 海力士/美光三家，实际只召回美光与佰维存储，
    模型如实写下「**三星和 SK 海力士最近一期报告的原文，材料未覆盖**」。
    ⚠️ 这张起初被当成「多公司聚合成功」的证据，**是错的**：它是失败图，
    恰好暴露「碎块拼全景」这件事**没做到**（见 `一页结论.md`）。
    留着它，因为它同时是「不编造」与「全景失败」两份证据。
"""
import sys, urllib.request, urllib.parse, time
sys.path.insert(0, "scripts")
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

CASES = [
    ("1-判据命中-3A090c门槛", "3A090.c 的管制门槛是什么？"),
    ("2-诚实失败-HBM3E合约价", "HBM3E 现在的合约价是多少美元？"),
    ("3-口径题未命中-江波龙", "江波龙的年报里，「营业收入」和「营业总收入」这两个口径差在哪里？"),
    ("4-全景题-三家HBM供需", "三星、SK 海力士、美光三家最近一期报告对 HBM 供需与产能的表述有哪些共性和差异？"),
]
for name, q in CASES:
    u = "http://127.0.0.1:8848/?" + urllib.parse.urlencode({"q": q})
    t0 = time.time()
    with urllib.request.urlopen(u, timeout=240) as r:
        h = r.read().decode("utf-8")
    p = f"outputs/问答页-{name}.html"
    open(p, "w", encoding="utf-8").write(h)
    companies = h.count("三星") > 0, h.count("海力士") > 0, h.count("美光") > 0
    # ⚠️ 原先这里只**打印**覆盖情况、不据此判断——「打印了却不判」和「声明了没接线」
    # 是同一族毛病：第 4 张图明明是全景失败（三星 0 条），照样静静存下、被当成功用。
    # 现在缺哪家就喊出来，让人当场看见。
    miss = [n for n, ok in zip(("三星", "SK 海力士", "美光"), companies) if not ok]
    tag = f"  ⚠️ 三家未覆盖：{miss}" if miss else "  三家全覆盖"
    print(f"  ✓ {p}  {len(h)} 字节  {time.time()-t0:.1f}s{tag}")

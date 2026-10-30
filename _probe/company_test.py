# -*- coding: utf-8 -*-
"""按公司取证通道的验收：全景题（Q7/Q8）开不开这条通道，公司构成差在哪。

⚠️ 现在跑的是**旧库**（chunks.sqlite 还是 2026-10-04 那份，行序对得上旧向量）。
   这里量的是**通道机制**（谁被捞上来、谁被压下去），不是最终分数；
   最终记录要等向量重建 + 重建 sqlite 之后再出。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import retrieve as R                                        # noqa: E402
import run_questions as RQ                                  # noqa: E402

Rt = R.Retriever(verbose=False)
print("向量：", Rt.vec.shape)


def composition(hits):
    from collections import Counter
    c = Counter((h["company"] or h["source"]) for h in hits)
    return "、".join(f"{k}×{v}" for k, v in c.most_common())


for n in (7, 8):
    spec = next(s for s in RQ.Q if s["n"] == n)
    print("\n" + "=" * 78)
    print("第 %d 题  全景=%s  k=%d" % (n, spec.get("panorama"), spec["k"]))
    print("  %s" % spec["q"])
    print("=" * 78)
    print("  点名识别：", Rt.named_companies(spec["q"]))
    for tag, pano in (("关（改前行为）", False), ("开（按公司取证）", True)):
        hs = Rt.search(spec["q"], k=spec["k"], expand=True, panorama=pano)
        ok, msg = RQ.judge_recall(spec, hs)
        print("\n  【%s】%s" % (tag, msg))
        print("     公司构成：%s" % composition(hs))
        print("     通道标记：%s" % "，".join(
            "%s[%s]" % (h["channels"], h["company"] or h["source"]) for h in hs))
        if pano:
            named = hs[0].get("company_named") or []
            print("     ▶ 按公司取证覆盖了 %d 家：%s" % (len(named), "、".join(named)))
            have = {h["company"] or h["source"] for h in hs}
            print("     ▶ 点名公司里**仍缺席**的：%s"
                  % ("、".join(c for c in named if c not in have) or "（无）"))

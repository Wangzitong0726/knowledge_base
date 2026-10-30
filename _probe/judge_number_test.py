# -*- coding: utf-8 -*-
"""回归测试：答案侧「数字归属核对」的切词与比对。

**为什么必须测**：这个判据是「正确页码不能证明数字归属正确」那句的答案侧对应物，
是这套交付物里少数几个**机械判据**之一。它一旦有假阳性，就会把「模型编数」这条
最该被抓住的错**报成误报**——而误报会让判据整体失去可信度，比漏报更伤。

这次实测撞到的假阳性：原文 `(89 FR 96790, December 5, 2024)` 因正则贪婪，
切出 `96790,` 和 `5,`；答案句末写 `96790。` 切出 `96790`。按原样比永远不等。

⚠️ **测这个修复时最容易自欺的一点**：把判据改松，让所有数都"有出处"，
测试当然全绿——但那等于把判据删了。所以下面**必须有反例**：
一个语料里真没有的数，修完之后**仍然要**被报成无出处。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from run_questions import value_numbers, number_attribution, _key   # noqa: E402

checks = []


def chk(name, ok):
    checks.append((name, bool(ok)))
    print("  %s %s" % ("✅" if ok else "❌", name))


print("── ① 切词：逗号只算千分位 ──")
chk("`96790,` → 切成 `96790`（尾随逗号不再吞进去）",
    "96790" in value_numbers("(89 FR 96790, December 5, 2024)"))
chk("`December 5, 2024` 里的 `5,` **不再**被当成数值",
    "5," not in value_numbers("(89 FR 96790, December 5, 2024)"))
chk("合规千分位 `10,195,655,370.19` 完整保留",
    "10,195,655,370.19" in value_numbers("营收 10,195,655,370.19 元"))
chk("型号 `3A090.c` 里的 `3` / `090` 不算数值",
    not [n for n in value_numbers("3A090.c 的门槛") if n in ("3", "090")])

print("\n── ② 比对：同样的数、不同的排版，要认出来 ──")
HIT = [{"text": "Mostly recently, BIS updated these controls in December 2024 "
                "(89 FR 96790, December 5, 2024)."}]
_have, _orph = number_attribution("BIS 于 2024 年 12 月更新了管制（89 FR 96790）。", "", HIT)
chk("语料 `96790,` 对答案 `96790` → **认出来**（这就是修掉的那个假阳性）",
    any(n == "96790" for n, _s in _have) and not _orph)

_have2, _orph2 = number_attribution("营收 1,234,567 元", "",
                                    [{"text": "本期营业收入 1234567 元"}])
chk("语料 `1234567` 对答案 `1,234,567` → 认出来（千分位只是排版）",
    any(n == "1,234,567" for n, _s in _have2) and not _orph2)

# ⚠️ 这条**不是**要修的 bug，是**设计上故意保留**的保守误差，写下来免得日后被当成回归：
#    4 位数在语料里不写分隔符（`1234`）时，`value_numbers` 按设计不视其为「数值型」
#    （那条启发式是为了不把 `2024` 年份、`3 个方面` 当事实主张）；
#    同一数在答案里写成 `1,234` 却因「有千分位」被判为数值型 → 报无出处。
#    误差方向是「显得比实际差」，与 `number_attribution` 的 docstring 一致。
#    真要收这个口子，得改的是**分类启发式**（例如带上下文判断），不是逗号归一。
_have2b, _orph2b = number_attribution("营收 1,234 元", "", [{"text": "本期营业收入 1234 元"}])
chk("（已知保守误差）语料 `1234` 对答案 `1,234` → 记为无出处，方向偏严",
    _orph2b == ["1,234"])

print("\n── ③ 反例：真没有出处的数，必须**仍然**报错 ──")
_have3, _orph3 = number_attribution("营收 999999 元", "", HIT)
chk("语料里没有的 `999999` → **仍然**记为无出处", _orph3 == ["999999"])
_have4, _orph4 = number_attribution(
    "价格为 12,345.67 美元", "", [{"text": "本期毛利率 12.34%"}])
chk("数值相近但不同（`12,345.67` vs `12.34`）→ 不认",
    _orph4 == ["12,345.67"])

print("\n── ④ 问题里出现过的数，算复述、不追出处 ──")
_have5, _orph5 = number_attribution(
    "门槛是 3A090.c", "3A090.c 的管制门槛是什么？", [{"text": "3A090.c 门槛"}])
chk("复述问题里的数不计入无出处", not _orph5)

bad = sum(1 for _n, ok in checks if not ok)
print("\n%s" % ("全部通过（%d/%d）" % (len(checks) - bad, len(checks))
                if not bad else "**有 %d 条不对**" % bad))
raise SystemExit(1 if bad else 0)

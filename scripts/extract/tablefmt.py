# -*- coding: utf-8 -*-
"""
表格格式化：PDF 路与 HTML 路**共用一份**。

为什么要共用：两条路的目标完全一样——**把表拍平成「标签+数值」的行文本，
让每个数字都带着自己的表头**。各写一份必然漂移，日后一边修了 bug 另一边没修，
而两边的失败模式又都是一样的「不报错、只是安静地错」。
"""
import re

# 过滤器阈值（实测调出来的，见 _probe/stage2_tables.py）
MIN_ROWS = 2                 # 少于 2 行的不是表
MIN_CELLS_IN_A_ROW = 2       # 任一行至少要这么多非空单元，否则是碎片
MAX_EMPTY_RATIO = 0.55       # 空格率高于此 → 判为误报（封面标题被切碎的样子）


_CJK = re.compile(r"[⺀-鿿豈-﫿＀-￯]")


def join_wrapped_lines(s):
    """把被**版式**折断的行接回去：两侧都是中日韩字时**不插空格**。

    ⚠️ 这是实测踩出来的坑。PDF 里一个单元格内的长句会按显示宽度折成好几行，
    PyMuPDF 逐行取出；若一律用空格接，中文词就被切开：
      · 原文 `公司股东时代鼎丰、小橡创投、中电基金`
      · 抽出 `公司股 东时代 鼎丰、 小橡创 投、中 电基 金、`
    中文词本就不用空格分词，插进去的空格不是「词边界」而是**噪声**，
    会让 jieba 切错、让向量以为这是好几个词。西文则相反，折行处**必须**补空格，
    否则 `high bandwidth memory` 会粘成 `highbandwidthmemory`。
    """
    parts = (s or "").split("\n")
    out = parts[0]
    for p in parts[1:]:
        if out and p and _CJK.match(out[-1]) and _CJK.match(p[0]):
            out += p
        else:
            out += " " + p
    return out


def cell_text(c):
    return re.sub(r"[ \t]+", " ", join_wrapped_lines(c)).strip()


def clean_rows(rows):
    """None/空串统一成 ''，并去掉整行为空的。"""
    out = []
    for r in rows:
        rr = [cell_text(c) for c in r]
        if any(rr):
            out.append(rr)
    return out


def dedup_runs(seq):
    """压掉**连续重复**元素（只看值，丢掉列号）。

    为什么需要压：`colspan=5` 展开成 5 个相同单元格（为了网格对齐，不展开列就错位），
    输出时同一句话就会连着出现 5 遍——
      `☒ | ☒ | ☒ | ANNUAL REPORT… | ANNUAL REPORT… | ANNUAL REPORT…`
    **对齐要展开，输出要压缩**，两件事分开做。
    """
    out = []
    for x in seq:
        if not out or x != out[-1]:
            out.append(x)
    return out


def collapse_keep_col(row):
    """压掉连续重复，但**保留每一段在原始网格里的首列号** → [(列号, 值), ...]。

    ⚠️ 压行**必须带着列号一起压**，否则会安静地算错。
    踩过的坑：早先直接对压缩后的行 `enumerate`，再拿这个位置去查表头——
    于是「某行比别的行少一个空格单元」就会让这一行后面**每一个数字都去对隔壁列的表头**。
    实测后果：美光 10-K 的「Revenue」行有个 `100`(%)，被安到了下一行
    「Cost of goods sold」头上，输出成 `… | 100 60 | …` —— 一个**表里根本没出现过**的数。
    用原列号查表头，压缩只负责好看，不参与定位。
    """
    out = []
    for i, c in enumerate(row):
        if out and out[-1][1] == c:
            continue
        out.append((i, c))
    return out


def table_ok(rows):
    """判定这是不是一张**真表**（滤掉误报）。返回 (bool, 原因)。"""
    rows = clean_rows(rows)
    if len(rows) < MIN_ROWS:
        return False, "行数不足"
    width = max(len(r) for r in rows)
    if max(sum(1 for c in r if c) for r in rows) < MIN_CELLS_IN_A_ROW:
        return False, "行内非空单元太少"
    total = width * len(rows)
    empty = sum(1 for r in rows for c in r if not c)
    if total and empty / total > MAX_EMPTY_RATIO:
        return False, f"空格率 {empty/total:.2f} 过高"
    return True, ""


MIN_HEADER_CELLS = 2         # 表头行的非空格子下限，低于此是残行（见 _header_score）


# 「像期间」：`2025` / `2025年` / `2025 年半年度` / `2025-06-30` / `2025.06.30` / `2025年6月30日`
_PERIOD = re.compile(
    r"^(?:19|20)\d{2}\s*(?:"
    r"年\s*(?:半年度|年度|第[一二三四]季度|全年度)?"
    r"|[.\-/]\s*\d{1,2}\s*(?:[.\-/月]\s*\d{1,2}\s*日?)?"
    r")?$"
)
# 「像金额/数量」：千分位 37,378 ｜ 小数 370.19 ｜ 货币 ¥$€£ ｜ 百分号 60%
_NUMERIC = re.compile(r"\d{1,3}(?:,\d{3})+|\d\.\d|[¥$€£]|\d\s*[%‰]")


def _is_period(s):
    """像「期间」的格子。

    期间**不是数值**：它是「这个数属于哪一期」，恰恰是文本里最不该丢的东西
    （课件 p91：数值进了图谱只剩一个节点，是谁的、哪个口径、哪一期都丢了）。
    所以它绝不能把一行判成「数据行」——否则 `项目 | 2025 年半年度 | 2024 年半年度`
    这个再正确不过的表头会被误杀。
    """
    return bool(_PERIOD.match((s or "").strip()))


def _is_value(s):
    """像**金额/数量**（而不是像期间）。

    判据刻意收得很紧，只认**千分位、小数点、货币符号、百分号**四样——
    光凭「含阿拉伯数字」区分不了数据与期间（`2025 年半年度` 里也有数字）。
    反过来说，一行里只要有一个这样的格子，它就是数据行、不配当表头。
    """
    s = (s or "").strip()
    if not s or _is_period(s):
        return False
    return bool(_NUMERIC.search(s))


def _is_label(s):
    """像表头文字：**含字母**（含中日韩字），且不是纯数字。

    为什么要求「含字母」：财务报表的数据行里满是 `$`、`%`、`(`、`—` 这类符号格，
    它们既不是数字也不是表头文字。早先只判「非数值」时，**收入那一行的 `$`/`%`
    比真表头行的格子还多**，于是表头被选成了数据行——美光 10-K 的
    「Revenue / $37,378 / 100 / %」整行当了表头，下一行 `60%` 被贴上 `100`
    的前缀，输出成 `100 60 | %`。数字是真的，配的对是错的。
    """
    return any(ch.isalpha() for ch in s)


def _header_score(row):
    """可信表头行的得分（= 像标签的格子数）；返回 `None` 表示**这一行不配当表头**。

    ⚠️ 旧版是 `labels - 0.5*nums`，且**只数非空格子**。这条式子有个致命漏洞：
    一个「一个标签 + 两个空格」的**残行**得 1.0 分，而正常数据行
    （`二、营业总成本 | 10,081,506,072.43 | 8,215,067,574.55`）得 0.0 分——
    **残行赢**；接着被「表头向左填充」灌满整行，给后面每个数字都盖上它的名字。
    实测（江波龙 2025 半年报 p79，合并利润表跨页）：续页顶部那行 `['利息收入','','']`
    当选表头，于是 `二、营业总成本` 的两个数被写成「利息收入 10,081,506,072.43」。
    同类实例还有德明利年报 p130（整张资产负债表被冠 `商誉`）、
    雅克科技年报 p142（被冠 `报废`，重复 30 次）。

    所以改成**先否决、再打分**：
      ① 非空格子少于 `MIN_HEADER_CELLS` → 否决（灭掉残行）；
      ② 行内出现金额/数量（`_is_value`）→ 否决（那是数据行，不是表头）；
      ③ 一个文字标签都没有（纯数字行）→ 否决。

    用 `set` 去重再数：colspan 会把一个格子展成 3 个一模一样的，
    不去重的话「跨 3 列的表头」会凭空多出 2 倍的分数。
    """
    vals = {c for c in row if c}
    if len(vals) < MIN_HEADER_CELLS:
        return None                          # ① 残行
    if any(_is_value(v) for v in vals):
        return None                          # ② 数据行
    labels = sum(1 for v in vals if _is_label(v))
    if labels == 0:
        return None                          # ③ 纯数字行
    return labels


def pick_header(rows, header_rows=1):
    """在本表**前 `header_rows + 1` 行**里挑可信表头，返回行号；挑不出就返回 `None`。

    平手取**靠前**的那一行。挑不出时不硬猜——宁可这一张表没有表头，
    也不要给它安一个错的（错的归属比没有归属坏得多，且没人会去查）。
    """
    best_i, best_s = None, 0
    for i in range(min(header_rows + 1, len(rows))):
        s = _header_score(rows[i])
        if s is not None and s > best_s:
            best_i, best_s = i, s
    return best_i


def flatten_table(rows, header_rows=1, inherited=None):
    """按行拍平：`表头 值` 配对，让每个数字都带着自己的标签。

    返回 `(文本, 本表可传给下一张表的表头或 None)`。返回表头是为了**跨页继承**：
    合并利润表/资产负债表常跨页，真表头在上一页，续页自己一行表头都没有
    （`scripts/extract/pdf.py` 的 `extract_pdf` 负责把表头带过去）。

    `inherited` 是上一页带过来的表头。只在**本表自己挑不出可信表头**时才用它——
    本表有表头就用本表的（新表新表头，比如财报里利润表接在资产负债表后面）。

    合并单元格的两种表现都要处理：
      · 纵向合并 → 提取出空串 → **表头行内向左填充**（让被合并列继承左边那格）
      · 横向合并(colspan) → 提取出重复值 → **按原列号压缩**（`collapse_keep_col`）

    第 0 列**不加表头前缀**：这一列是行标签本身（`货币资金`），
    给它套上表头（`项目 货币资金`）只添噪声，而标签列到底占几列是不确定的
    （colspan=3 的标签列会被展成 3 格），靠列号判断比靠猜宽度可靠。
    """
    rows = clean_rows(rows)
    if not rows:
        return "", None

    hdr_i = pick_header(rows, header_rows)
    if hdr_i is not None:
        header, data = list(rows[hdr_i]), rows[hdr_i + 1:]
    elif inherited and any(inherited):
        header, data = list(inherited), rows      # 续页：整页都是数据
    else:
        header, data = [], rows                   # 无可信表头：不猜，原样输出

    carried = None
    if header:
        last = ""
        for i, c in enumerate(header):            # 行内向左填充
            if c:
                last = c
            elif last:
                header[i] = last
        carried = header

    out = []
    for r in data:
        parts = []
        for i, c in collapse_keep_col(r):         # ← 按**原列号**取表头，不按压缩后的位置
            if not c:
                continue
            h = header[i] if i < len(header) else ""
            parts.append(c if (i == 0 or not h or h == c) else f"{h} {c}")
        if parts:
            out.append(" | ".join(parts))
    if not out and header:                        # 只有表头没有数据行时，至少把表头留住
        out = [" | ".join(c for _i, c in collapse_keep_col(header) if c)]
    return "\n".join(out), carried

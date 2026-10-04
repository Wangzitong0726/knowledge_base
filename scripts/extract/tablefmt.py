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


def _looks_numeric(s):
    """像数字：含阿拉伯数字，且去掉数字与千分位/百分号后基本没剩什么。"""
    return bool(re.search(r"\d", s)) and len(re.sub(r"[\d,.\-—－%（）()\s]", "", s)) <= 2


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
    """给候选表头行打分：**像标签的格子数 − 半个像数字的格子数**。

    用 `set` 去重再数：colspan 会把一个格子展成 3 个一模一样的，
    不去重的话「跨 3 列的表头」会凭空多出 2 倍的分数。
    """
    vals = {c for c in row if c}
    labels = sum(1 for v in vals if _is_label(v))
    nums = sum(1 for v in vals if _looks_numeric(v))
    return labels - 0.5 * nums


def flatten_table(rows, header_rows=1):
    """按行拍平：`表头 值` 配对，让每个数字都带着自己的标签。

    合并单元格的两种表现都要处理：
      · 纵向合并 → 提取出空串 → **表头行内向左填充**（让被合并列继承左边那格）
      · 横向合并(colspan) → 提取出重复值 → **按原列号压缩**（`collapse_keep_col`）

    第 0 列**不加表头前缀**：这一列是行标签本身（`货币资金`），
    给它套上表头（`项目 货币资金`）只添噪声，而标签列到底占几列是不确定的
    （colspan=3 的标签列会被展成 3 格），靠列号判断比靠猜宽度可靠。
    """
    rows = clean_rows(rows)
    if not rows:
        return ""

    # 选表头：前几行里得分最高的那一行；**平手取靠前的**。
    # 平手必须取靠前：`For the year ended|2025|2024|2023` 与
    # `Revenue|$|37,378|100|%` 得分相同（各 1 个真标签），
    # 取靠后的就会把数据行当表头——这正是上面 `100 60` 那个错的来源。
    hdr_i, best = 0, _header_score(rows[0])
    for i in range(1, min(header_rows + 1, len(rows))):
        score = _header_score(rows[i])
        if score > best:
            hdr_i, best = i, score
    header = list(rows[hdr_i])
    last = ""
    for i, c in enumerate(header):          # 行内向左填充
        if c:
            last = c
        elif last:
            header[i] = last

    out = []
    for r in rows[hdr_i + 1:]:
        parts = []
        for i, c in collapse_keep_col(r):   # ← 按**原列号**取表头，不按压缩后的位置
            if not c:
                continue
            h = header[i] if i < len(header) else ""
            parts.append(c if (i == 0 or not h or h == c) else f"{h} {c}")
        if parts:
            out.append(" | ".join(parts))
    if not out:                              # 只有表头没有数据行时，至少把表头留住
        out = [" | ".join(c for _i, c in collapse_keep_col(header) if c)]
    return "\n".join(out)

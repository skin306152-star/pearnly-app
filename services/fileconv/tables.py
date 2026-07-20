# -*- coding: utf-8 -*-
"""通用表格 / 税报表抽取 + 合计闭合校验的取数。

对不走跑余额链的文档(vat_report / generic_table),抽:
  · 数据行的金额列(行尾对齐的 .dd 金额)
  · 合计行(含 รวม / ทั้งสิ้น / total / sum 关键词)

合计闭合校验(validate.py 用):明细各金额列之和 = 合计行对应列。配对方式取决于料的成色:

  · 真列位已知(from_grid · PDF 走 pdf_grid 切出的规整网格)→ 按列下标配对。
  · 只有文字行(extract_tabular)→ 退回"行尾右对齐"配对,容忍明细行比合计行多出的前置列。

右对齐是没有列位时的将就,不是首选:某行右侧缺列(无销售日那行只剩一个单价 6.07)会让整列
错位,把单价当成含税总额,报出一个不存在的差额。有列位就必须按列位走。
"""

import re
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from services.fileconv.amounts import money_tokens, parse_amount, repair_number_spaces

# 合计行关键词。
_TOTAL_MARKERS = ("รวมทั้งสิ้น", "ทั้งสิ้น", "รวมยอด", "รวม", "total", "sum", "grand total")
# Express 老式表单用泰数字 ๓ 当列边框;其余用 2+ 空格列间距。
_THAI_BORDER = "๓"


class TabularLine:
    """一条抽出的表格行:cells 为切分单元格,money 为行内金额(按序),is_total 标记合计行。

    col_money 是「列下标 → 金额」,只有列位可信(from_grid)时才有;为 None 表示这行是从纯
    文字切出来的,列位不可知,合计校验只能退回右对齐配对。
    """

    def __init__(
        self,
        line_no: int,
        cells: List[str],
        money: List[Decimal],
        is_total: bool,
        col_money: Optional[Dict[int, Decimal]] = None,
    ):
        self.line_no = line_no
        self.cells = cells
        self.money = money
        self.is_total = is_total
        self.col_money = col_money


def _split_cells(line: str) -> List[str]:
    if _THAI_BORDER in line and line.count(_THAI_BORDER) >= 2:
        parts = line.split(_THAI_BORDER)
    else:
        parts = re.split(r"\s{2,}", line)
    return [p.strip() for p in parts if p.strip()]


def _is_total_line(line: str) -> bool:
    low = line.lower()
    return any(m in low or m in line for m in _TOTAL_MARKERS)


def extract_tabular(pages: List[str]) -> List[TabularLine]:
    out: List[TabularLine] = []
    line_no = 0
    for page in pages:
        for raw in page.split("\n"):
            line_no += 1
            line = repair_number_spaces(raw.strip())
            if not line:
                continue
            money = money_tokens(line)
            if not money:
                continue
            out.append(
                TabularLine(
                    line_no=line_no,
                    cells=_split_cells(raw.strip()),
                    money=money,
                    is_total=_is_total_line(line),
                )
            )
    return out


def from_grid(rows: List[List[str]], *, start_line: int = 1) -> List[TabularLine]:
    """规整网格(pdf_grid.Grid.rows)→ TabularLine,金额按列下标记账。

    空格 / '-' / None 解不出金额 → 该列不产生条目(它是「这天没有」,不是 0)。把缺值读成 0
    会让合计校验凭空多出一列参与比对,报出假差额。
    """
    out: List[TabularLine] = []
    for offset, cells in enumerate(rows):
        texts = ["" if c is None else str(c) for c in cells]
        col_money: Dict[int, Decimal] = {}
        for j, text in enumerate(texts):
            value = parse_amount(text)
            if value is not None:
                col_money[j] = value
        out.append(
            TabularLine(
                line_no=start_line + offset,
                cells=texts,
                money=[col_money[j] for j in sorted(col_money)],
                is_total=_is_total_line(" ".join(texts)),
                col_money=col_money,
            )
        )
    return out


def reconcile_totals(lines: List[TabularLine]) -> List[Tuple[int, str, Decimal, Decimal]]:
    """明细金额列之和 vs 最末合计行。

    返回不平列列表 [(合计行号, 列说明, 期望和, 实际合计), ...]。
    无合计行或无明细 → 返回空(交调用方记 no_total_found,不伪造通过)。
    """
    total_lines = [ln for ln in lines if ln.is_total]
    data_lines = [ln for ln in lines if not ln.is_total]
    if not total_lines or not data_lines:
        return []

    grand = total_lines[-1]
    # 明细取合计行之前的数据行(合计行后的签名/说明行不算)。
    detail = [ln for ln in data_lines if ln.line_no < grand.line_no]
    if not detail:
        return []
    if grand.col_money is not None:
        return _by_column(grand, detail)
    return _by_right_align(grand, detail)


def _mismatch(line_no: int, label: str, expected: Decimal, actual: Decimal) -> Optional[Tuple]:
    return (line_no, label, expected, actual) if abs(expected - actual) > Decimal("0.01") else None


def _by_column(grand: TabularLine, detail: List[TabularLine]) -> List[Tuple]:
    """列位已知:按列下标配对。合计行没报数的列不校验(不拿 0 当合计)。"""
    out = []
    for j, actual in sorted(grand.col_money.items()):
        contributions = [ln.col_money[j] for ln in detail if j in (ln.col_money or {})]
        if not contributions:
            continue
        hit = _mismatch(grand.line_no, f"第 {j + 1}", sum(contributions, Decimal("0")), actual)
        if hit:
            out.append(hit)
    return out


def _by_right_align(grand: TabularLine, detail: List[TabularLine]) -> List[Tuple]:
    """列位未知:金额按行尾右对齐配对(将就路,见模块头说明)。"""
    out = []
    for i in range(1, len(grand.money) + 1):  # i = 右起第 i 列
        contributions = [ln.money[-i] for ln in detail if len(ln.money) >= i]
        if not contributions:
            continue
        expected = sum(contributions, Decimal("0"))
        hit = _mismatch(grand.line_no, f"右起第 {i}", expected, grand.money[-i])
        if hit:
            out.append(hit)
    return out


def to_table_rows(lines: List[TabularLine]) -> List[List]:
    return [ln.cells for ln in lines]


def max_columns(lines: List[TabularLine]) -> int:
    return max((len(ln.cells) for ln in lines), default=0)

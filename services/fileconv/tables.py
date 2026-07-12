# -*- coding: utf-8 -*-
"""通用表格 / 税报表抽取 + 合计闭合校验的取数。

对不走跑余额链的文档(vat_report / generic_table),抽:
  · 数据行的金额列(行尾对齐的 .dd 金额)
  · 合计行(含 รวม / ทั้งสิ้น / total / sum 关键词)

合计闭合校验(validate.py 用):明细各金额列之和 = 合计行对应列。金额列按"行尾右对齐"
配对,以容忍明细行比合计行多出的前置列(如预扣税率列)。
"""

import re
from decimal import Decimal
from typing import List, Optional, Tuple

from services.fileconv.amounts import money_tokens, repair_number_spaces

# 合计行关键词。
_TOTAL_MARKERS = ("รวมทั้งสิ้น", "ทั้งสิ้น", "รวมยอด", "รวม", "total", "sum", "grand total")
# Express 老式表单用泰数字 ๓ 当列边框;其余用 2+ 空格列间距。
_THAI_BORDER = "๓"


class TabularLine:
    """一条抽出的表格行:cells 为切分单元格,money 为行内金额(按序),is_total 标记合计行。"""

    def __init__(self, line_no: int, cells: List[str], money: List[Decimal], is_total: bool):
        self.line_no = line_no
        self.cells = cells
        self.money = money
        self.is_total = is_total


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


def reconcile_totals(lines: List[TabularLine]) -> List[Tuple[int, int, Decimal, Decimal]]:
    """明细金额列之和 vs 最末合计行。

    返回不平列列表 [(合计行号, 右起第几列, 期望和, 实际合计), ...]。
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

    mismatches: List[Tuple[int, int, Decimal, Decimal]] = []
    for i in range(1, len(grand.money) + 1):  # i = 右起第 i 列
        expected = Decimal("0")
        seen = False
        for ln in detail:
            if len(ln.money) >= i:
                expected += ln.money[-i]
                seen = True
        if not seen:
            continue
        actual = grand.money[-i]
        if abs(expected - actual) > Decimal("0.01"):
            mismatches.append((grand.line_no, i, expected, actual))
    return mismatches


def to_table_rows(lines: List[TabularLine]) -> List[List]:
    return [ln.cells for ln in lines]


def max_columns(lines: List[TabularLine]) -> int:
    return max((len(ln.cells) for ln in lines), default=0)

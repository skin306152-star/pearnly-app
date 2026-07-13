# -*- coding: utf-8 -*-
"""含税毛额 → 销售额/销项税反推(ภ.พ.30 口径,纯 Decimal)。

泰国 VAT 7% 含税价:税 = 毛额×7/107 四舍五入到分,销售额 = 毛额 − 税。销售额不做第二次
独立四舍五入(×100/107 再舍入在边界分位会差 0.01,拆出的两数对不回毛额;减法拆保证
销售额+税 恒等于毛额)。

两种口径并报,采「先加总再拆」为主:
- aggregate-first:逐行毛额先加总,对总额拆一次税——官方申报是月合计口径,金标
  (SM 5月 858,780.16 / 60,114.61)按此对表;
- per-line:逐行拆税再加总——逐笔舍入误差会累积,与主口径的差异如实报告不藏。
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

CENT = Decimal("0.01")
ZERO = Decimal("0")
_VAT_PART = Decimal(7)
_GROSS_PART = Decimal(107)


def split_gross(gross: Decimal) -> tuple[Decimal, Decimal]:
    """含税毛额 → (销售额, 销项税)。"""
    vat = (gross * _VAT_PART / _GROSS_PART).quantize(CENT, rounding=ROUND_HALF_UP)
    return gross - vat, vat


def split_report(gross_lines: Iterable[Decimal]) -> dict:
    """逐行毛额 → 两口径拆税报告。主口径=先加总再拆;per_line_* 与 diff 仅供核对。"""
    lines = list(gross_lines)
    total = sum(lines, ZERO)
    sales, vat = split_gross(total)
    per_sales = per_vat = ZERO
    for gross in lines:
        line_sales, line_vat = split_gross(gross)
        per_sales += line_sales
        per_vat += line_vat
    return {
        "gross_total": total,
        "sales_amount": sales,
        "output_vat": vat,
        "per_line_sales": per_sales,
        "per_line_vat": per_vat,
        "vat_method_diff": vat - per_vat,
    }

# -*- coding: utf-8 -*-
"""复核工作簿的钱算法 —— 写侧读侧共用这一份,不许各算各的。

出这个模块的直接原因:写侧和读侧各写了一套四舍五入,多行发票往返一圈会差分币,
而推进 ERP 用的是读侧那个数 —— 会计在表上看到的和账里的对不上,对账时要找半天。

三条硬规矩:

1. **用 Decimal,不用 float。** `0.07` 在 float 里不是精确的 0.07,
   `round(66.66 * 0.07, 2)` 这种写法在边界上会给出意料之外的结果。
2. **跟推送路同一套舍入**(`express_push.common._q`:两位、ROUND_HALF_EVEN)。
   表格算一套、推 ERP 算另一套,就是在制造对不上。
3. **单据税额优先用票面印的那个**,只有在会计改了数量/单价、税基确实变了时才重算。
   票面税额是法定数字(要进 ภ.พ.30),我们没有权力把它算成别的。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional, Sequence, Tuple

from services.erp.express_push.common import _q as quantize_money

VAT_RATE = Decimal("0.07")
# 票面税额与按税基重算的差在这个范围内,就认票面的(OCR 读到的法定数字优先)。
# 差得更多说明税基真的变了(会计改了数量/单价),那时才该重算。
_VAT_TRUST_TOL = Decimal("0.02")


def to_money(raw: Any) -> Optional[Decimal]:
    """单元格/字段 → Decimal。空、公式串、解不出来一律 None(交给调用方按合同派生)。"""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, Decimal):
        return raw
    if isinstance(raw, int):
        return Decimal(raw)
    if isinstance(raw, float):
        # float 进来先转字符串再进 Decimal —— 直接 Decimal(float) 会把二进制误差带进来
        return Decimal(str(raw))
    s = str(raw).strip().replace(",", "").replace("฿", "").replace("THB", "")
    if not s or s.startswith("="):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def line_amount(qty: Any, price: Any) -> Optional[Decimal]:
    """行金额 = 数量 × 单价。缺任一项返 None,不猜。"""
    q, p = to_money(qty), to_money(price)
    if q is None or p is None:
        return None
    return quantize_money(q * p)


def vat_of(base: Any) -> Decimal:
    """按税基算税额。整个工作簿只有这一处算 VAT。"""
    b = to_money(base) or Decimal("0")
    return quantize_money(b * VAT_RATE)


def sum_money(values: Sequence[Any]) -> Decimal:
    total = Decimal("0")
    for v in values:
        d = to_money(v)
        if d is not None:
            total += d
    return quantize_money(total)


def doc_totals(
    line_amounts: Sequence[Any],
    *,
    explicit_base: Any = None,
    printed_vat: Any = None,
) -> Tuple[Decimal, Decimal, Decimal]:
    """单据的 (税基, 税额, 合计)。

    税基:会计把税前改成死值就用他的(那是他的裁决),否则按行金额求和。
    税额:票面印的那个优先 —— 它是法定数字。只有当它与按税基重算的差超过容差
          (说明会计确实改动了数量/单价),才改用重算值。
    """
    base = to_money(explicit_base)
    if base is None:
        base = sum_money(line_amounts)
    else:
        base = quantize_money(base)

    computed = vat_of(base)
    printed = to_money(printed_vat)
    vat = (
        printed
        if printed is not None and abs(quantize_money(printed) - computed) <= _VAT_TRUST_TOL
        else computed
    )
    vat = quantize_money(vat)
    return base, vat, quantize_money(base + vat)


def allocate_vat(line_amounts: Sequence[Any], doc_vat: Any) -> List[Decimal]:
    """把单据税额摊到各行,**末行吸收余数**,保证逐行相加恰好等于单据税额。

    不这么做的话,会计把表里那一列加起来会得到和单据税额不同的数 —— 一分钱的差最难查。
    """
    amounts = [to_money(a) or Decimal("0") for a in line_amounts]
    total_vat = quantize_money(to_money(doc_vat) or Decimal("0"))
    base = sum_money(amounts)
    if not amounts:
        return []
    if base == 0:  # 全零行:税额整个给末行,不做除零
        return [Decimal("0")] * (len(amounts) - 1) + [total_vat]
    out: List[Decimal] = []
    for a in amounts[:-1]:
        out.append(quantize_money(total_vat * a / base))
    out.append(quantize_money(total_vat - sum(out)))
    return out

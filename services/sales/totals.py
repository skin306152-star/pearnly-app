# -*- coding: utf-8 -*-
"""销项单据金额计算(从 document.py 抽出 · 纯函数叶子 · 不连库)。

行级 + 整单折扣、VAT 价内/价外、WHT,全程 Decimal 分位 quantize。document.py 调
compute_totals 写 sales_documents;credit_note 复用同一套算法。算税铁律见 docs/16 §C/§D:
VAT 落折后应税净额,整单折扣按比例摊到应税额,折后净额不得为负。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _d(v: Any) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def _has_value(v) -> bool:
    """折扣百分比是否真给了值(区分 0/None/空串 与有效百分比)。"""
    return v not in (None, "", 0, "0", "0.0", "0.00")


def _line_discount(gross: Decimal, ln: dict) -> tuple[Decimal, Optional[Decimal]]:
    """行折扣:给了 discount_pct 走百分比,否则用绝对 discount。折后净额不得为负(§D5)。"""
    pct = ln.get("discount_pct")
    if _has_value(pct):
        dp = _d(pct)
        disc = (gross * dp / _HUNDRED).quantize(_CENT)
    else:
        dp = None
        disc = _d(ln.get("discount", 0)).quantize(_CENT)
    if disc > gross:
        disc = gross
    return disc, dp


def _resolve_header_discount(base: Decimal, amount, pct) -> Decimal:
    """整单折扣:给了 pct 走百分比,否则绝对额。夹在 [0, subtotal]。"""
    h = (
        (base * _d(pct) / _HUNDRED).quantize(_CENT)
        if _has_value(pct)
        else _d(amount).quantize(_CENT)
    )
    if h < 0:
        return Decimal("0.00")
    return h if h <= base else base


def _taxable_vat_base(norm_lines: list, subtotal_pre: Decimal, header_disc: Decimal) -> Decimal:
    """整单折扣按 line_total 比例摊到应税净额上,保 VAT base 落在实际成交价(§D2)。"""
    taxable = sum((ln["line_total"] for ln in norm_lines if ln["vat_applicable"]), Decimal("0"))
    if header_disc == 0 or subtotal_pre == 0:
        return taxable.quantize(_CENT)
    taxable_share = (header_disc * taxable / subtotal_pre).quantize(_CENT)
    base = (taxable - taxable_share).quantize(_CENT)
    return base if base > 0 else Decimal("0.00")


def compute_totals(
    lines: list,
    *,
    vat_rate,
    wht_rate=0,
    header_discount_amount=0,
    header_discount_pct=0,
    price_includes_vat=False,
) -> dict:
    """从明细行算金额。行级 + 整单折扣;VAT 落折后净额,WHT 按折后净额。全程 Decimal。

    price_includes_vat(§C):False=价外,VAT 加在净额之上(默认);True=价内,行金额已含
    税,反算 vat = base * rate/(100+rate),subtotal_after 退成不含税净额。开关是单据级。
    """
    vr, wr = _d(vat_rate), _d(wht_rate)
    subtotal_pre = Decimal("0")
    disc_total = Decimal("0")
    norm_lines = []
    for i, ln in enumerate(lines, start=1):
        qty = _d(ln.get("qty", 1))
        price = _d(ln.get("unit_price", 0))
        gross = (qty * price).quantize(_CENT)
        disc, dp = _line_discount(gross, ln)
        line_total = (gross - disc).quantize(_CENT)
        subtotal_pre += line_total
        disc_total += disc
        norm_lines.append(
            {
                "line_no": i,
                "product_id": ln.get("product_id"),
                "description": (ln.get("description") or "").strip(),
                "qty": qty,
                "unit_price": price,
                "discount": disc,
                "discount_pct": dp,
                "vat_applicable": bool(ln.get("vat_applicable", True)),
                "line_total": line_total,
            }
        )

    header_disc = _resolve_header_discount(
        subtotal_pre, header_discount_amount, header_discount_pct
    )
    vat_base = _taxable_vat_base(norm_lines, subtotal_pre, header_disc)
    if price_includes_vat:
        # 价内:VAT 已含在折后应税额里,反算抽出;不含税净额 = 折后总额 - VAT。
        vat_amount = (vat_base * vr / (_HUNDRED + vr)).quantize(_CENT)
        subtotal_after = (subtotal_pre - header_disc - vat_amount).quantize(_CENT)
    else:
        vat_amount = (vat_base * vr / _HUNDRED).quantize(_CENT)
        subtotal_after = (subtotal_pre - header_disc).quantize(_CENT)
    wht_amount = (subtotal_after * wr / _HUNDRED).quantize(_CENT)
    grand = (subtotal_after + vat_amount - wht_amount).quantize(_CENT)
    return {
        "subtotal": subtotal_pre.quantize(_CENT),
        "discount_total": disc_total.quantize(_CENT),
        "header_discount_amount": header_disc,
        "header_discount_pct": (
            _d(header_discount_pct) if _has_value(header_discount_pct) else None
        ),
        "vat_rate": vr,
        "vat_amount": vat_amount,
        "price_includes_vat": bool(price_includes_vat),
        "wht_rate": wr,
        "wht_amount": wht_amount,
        "grand_total": grand,
        "lines": norm_lines,
    }

# -*- coding: utf-8 -*-
"""人工票据补正的校验与生效投影。事件保留 OCR 原值，消费侧统一叠加 latest decision。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from core import thai_date

AMOUNT_KEYS = ("net", "vat", "grand_total")
IDENTIFIER_KEYS = ("invoice_number", "invoice_date")
ALLOWED_KEYS = frozenset((*AMOUNT_KEYS, *IDENTIFIER_KEYS))


class InvalidCorrection(ValueError):
    pass


def normalize_values(values: dict | None) -> dict:
    """校验 recalc values 并转为稳定字符串；未知字段拒绝，防任意 JSON 混入证据链。"""
    if not isinstance(values, dict) or not values.get("vat"):
        raise InvalidCorrection("vat_required")
    if set(values) - ALLOWED_KEYS:
        raise InvalidCorrection("unknown_field")
    out: dict[str, str] = {}
    for key in AMOUNT_KEYS:
        if key not in values or values[key] in (None, ""):
            continue
        raw = str(values[key]).strip().replace(",", "")
        try:
            amount = Decimal(raw)
        except InvalidOperation as exc:
            raise InvalidCorrection(f"{key}_invalid") from exc
        if not amount.is_finite():
            raise InvalidCorrection(f"{key}_invalid")
        out[key] = format(amount, "f")
    if "invoice_number" in values:
        number = str(values["invoice_number"] or "").strip()
        if len(number) > 120:
            raise InvalidCorrection("invoice_number_too_long")
        out["invoice_number"] = number
    if "invoice_date" in values:
        raw_date = str(values["invoice_date"] or "").strip()
        if raw_date:
            try:
                date.fromisoformat(raw_date)
            except ValueError as exc:
                raise InvalidCorrection("invoice_date_invalid") from exc
            # 审核界面默认显示佛历、字段没标纪年,人工补正时按习惯填 พ.ศ. 会通过
            # fromisoformat(2569-05-31 合法),佛历年就此落库,推 ERP 再加 543 直接跑飞。
            if thai_date.buddhist_year_of(raw_date):
                raise InvalidCorrection("invoice_date_must_be_gregorian")
        out["invoice_date"] = raw_date
    return out


def apply_to_money(money: dict | None, decision: dict | None) -> dict:
    """OCR money 快照 + recalc 标识字段补正 → 下游有效票据字段，不改原始事件。"""
    effective = dict(money or {})
    if not decision or decision.get("decision") != "recalc":
        return effective
    values = decision.get("values") or {}
    for key in IDENTIFIER_KEYS:
        if key in values:
            effective[key] = values[key]
    return effective

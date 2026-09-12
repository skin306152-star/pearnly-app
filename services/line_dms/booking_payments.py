# -*- coding: utf-8 -*-
"""LINE 订车付款资料的解析、编辑校验与确认卡展示。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from services.erp.mrerp_dms_company_banks import company_bank_payment_extra, PAYMENT_CHANNEL_BANKS
from services.erp.mrerp_dms_payments import missing_transfer_fields
from services.line_dms.qa_util import (
    CHANNEL_EXTRA_SHAPE,
    THAI_DIGITS,
    find_row,
    parse_amount,
)


class PaymentValidationError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def parse_payment_detail(channel: str, text: Optional[str]) -> Optional[Dict[str, str]]:
    """把 LINE 的一行付款补充资料拆成 DMS 的独立字段。"""
    value = str(text or "").strip()
    if not value:
        return None
    if channel in {"card", "other"}:
        return {"card_type" if channel == "card" else "detail": value} if value != "-" else None
    value = value.replace("｜", "|")
    if "|" in value:
        left, right = (part.strip() for part in value.split("|", 1))
    else:
        parts = value.split()
        if len(parts) < 2:
            return None
        if channel == "transfer":
            left, right = " ".join(parts[:-1]), parts[-1]
        else:
            left, right = parts[0], " ".join(parts[1:])
    if not left or not right:
        return None
    if channel == "transfer":
        if not any(ch.isdigit() for ch in right.translate(THAI_DIGITS)):
            return None
        return {"src_bank_name": left, "src_account_no": right}
    keys = {
        "cheque": ("cheque_no", "cheque_book_no"),
        "cashier_cheque": ("cashier_no", "cashier_book_no"),
        "card": ("bank_name", "card_type"),
    }.get(channel)
    if keys:
        return {keys[0]: left, keys[1]: right}
    if channel == "other":
        return {"detail": value}
    return None


def _required(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "-" or len(text) > 160:
        raise PaymentValidationError("dms_booking.payment_detail_required")
    return text


def normalize_editor_payments(rows: list, masters: dict) -> list[dict]:
    """校验编辑器载荷并补全公司收款账户的 DMS 主档字段。"""
    if not rows:
        raise PaymentValidationError("dms_booking.payment_required")
    banks = masters.get("company_banks") or []
    clean = []
    seen = set()
    for item in rows[:12]:
        channel = str(item.get("channel") or "")
        if channel not in CHANNEL_EXTRA_SHAPE:
            raise PaymentValidationError("dms_booking.invalid_payment")
        if channel in seen:
            raise PaymentValidationError("dms_booking.duplicate_payment")
        seen.add(channel)
        amount = parse_amount(str(item.get("amount") or ""))
        if amount is None:
            raise PaymentValidationError("dms_booking.invalid_amount")
        extra = dict(item.get("extra") or {})
        if channel == "transfer":
            bank = find_row(banks, str(extra.get("dst_id") or ""))
            if bank is None:
                raise PaymentValidationError("dms_booking.invalid_bank")
            source = find_row(
                masters.get("source_banks") or [], str(extra.get("src_bank_id") or "")
            )
            if source is None:
                raise PaymentValidationError("dms_booking.invalid_bank")
            extra = {
                "src_bank_id": str(source[0]),
                "src_bank_name": str(source[2] or source[1]).strip(),
                **{
                    key: _required(extra.get(key))
                    for key in (
                        "src_account_no",
                        "src_account_name",
                        "src_branch_name",
                        "src_time",
                        "dst_business_name",
                    )
                },
                **company_bank_payment_extra(bank, extra),
            }
            if missing_transfer_fields(extra):
                raise PaymentValidationError("dms_booking.payment_detail_required")
        elif channel in PAYMENT_CHANNEL_BANKS:
            bank = find_row(
                masters.get(PAYMENT_CHANNEL_BANKS[channel]) or [], str(extra.get("bank_id") or "")
            )
            if bank is None:
                raise PaymentValidationError("dms_booking.invalid_bank")
            keys = {
                "cheque": ("cheque_no", "cheque_book_no"),
                "cashier_cheque": ("cashier_no", "cashier_book_no"),
                "card": ("card_type",),
            }[channel]
            extra = {
                "bank_id": str(bank[0]),
                "bank_name": str(bank[2] or bank[1]),
                **{key: _required(extra.get(key)) for key in keys},
            }
        elif channel == "other":
            extra = {"detail": _required(extra.get("detail"))}
        else:
            extra = {}
        clean.append({"channel": channel, "amount": f"{Decimal(amount):.2f}", "extra": extra})
    return clean


def payment_preview_detail(payment: dict) -> str:
    """确认卡的一行付款摘要，展示的数据与 DMS 字段保持同源。"""
    value = str(payment.get("amount") or "")
    extra = payment.get("extra") or {}
    channel = payment.get("channel")
    if channel == "transfer":
        source = " ".join(
            part
            for part in (
                str(extra.get("src_account_name") or ""),
                str(extra.get("src_bank_name") or ""),
                str(extra.get("src_account_no") or ""),
                str(extra.get("src_branch_name") or ""),
                str(extra.get("src_time") or ""),
            )
            if part
        )
        route = " → ".join(
            part
            for part in (
                source,
                " ".join(
                    str(extra.get(key) or "")
                    for key in (
                        "dst_business_name",
                        "dst_bank_name",
                        "dst_account_no",
                        "dst_branch_name",
                    )
                ).strip()
                or str(extra.get("dst") or ""),
            )
            if part
        )
        return " · ".join(part for part in (value, route) if part)
    if channel in {"cheque", "cashier_cheque"}:
        ref_key = "cheque_no" if channel == "cheque" else "cashier_no"
        ref = " · ".join(
            part
            for part in (
                str(extra.get(ref_key) or ""),
                str(
                    extra.get("cheque_book_no" if channel == "cheque" else "cashier_book_no") or ""
                ),
                str(extra.get("bank_name") or ""),
            )
            if part
        )
        return " · ".join(part for part in (value, ref) if part)
    if channel == "card":
        ref = " · ".join(
            part
            for part in (str(extra.get("bank_name") or ""), str(extra.get("card_type") or ""))
            if part
        )
        return " · ".join(part for part in (value, ref) if part)
    return " · ".join(part for part in (value, str(extra.get("detail") or "")) if part)

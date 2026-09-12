# -*- coding: utf-8 -*-
"""订金支付渠道 → DMS 订车单表单字段的纯映射(建单时由 mrerp_dms_client_ops 聚合进表单)。

逐问收上来的 payments 是 [{channel, amount, extra}] 列表,DMS 表单却是每渠道一组固定
字段名。这层只做映射与聚合:零 IO、可单测、金额一律 Decimal。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict

from services.erp.mrerp_dms_client_base import DMSClientError

# 订金支付渠道闭集 —— 未知渠道必须报错,不许静默丢。
_PAYMENT_CHANNELS = ("cash", "transfer", "cheque", "cashier_cheque", "card", "other")

# 每渠道在 DMS 订车单表单上的金额字段(真机勘察字段名)。
_PAYMENT_MONEY_FIELD = {
    "cash": "txtmoneycash",
    "transfer": "txtmoneytfmon",
    "cheque": "txtmoneycheque",
    "cashier_cheque": "txtmoneycashiercq",
    "card": "txtmoneycddbc",
    "other": "txtmoneyother",
}

# 每渠道的结构化 extra 槽位 → DMS 真正的表单字段。
_PAYMENT_TEXT_FIELD = {
    "transfer": {
        "src_account_name": "txtowneraccnametffrom",
        "src_account_no": "txtaccountnumtffrom",
        "src_bank_name": "txtbanknametffrom",
        "src_bank_id": "banktffromval",
        "src_branch_name": "txtbranchnametffrom",
        "src_time": "txttimetffrom",
        "dst_business_name": "txtbusinessnametfmon",
        "dst_account_no": "txtaccountnumtfmon",
        "dst_bank_name": "txtbanknametfmon",
        "dst_bank_id": "banktfmonval",
        "dst_branch_name": "txtbranchnametfmon",
    },
    "cheque": {
        "cheque_no": "txtchequeno",
        "cheque_book_no": "txtbooknocheque",
        "bank_name": "txtbanknamecheque",
        "bank_id": "bankchequeval",
    },
    "cashier_cheque": {
        "cashier_no": "txtcashiercqno",
        "cashier_book_no": "txtbooknocashiercq",
        "bank_name": "txtbanknamecashiercq",
        "bank_id": "bankcashiercqval",
    },
    "card": {
        "bank_name": "txtbanknamecddbc",
        "bank_id": "bankcddbcval",
        "card_type": "txttypenamecddbc",
    },
    "other": {"detail": "txtdetailother"},
}


def missing_transfer_fields(extra: dict) -> list[str]:
    """Native DMS transfer fields are required together, including the bank IDs."""
    return [
        key
        for key in _PAYMENT_TEXT_FIELD["transfer"]
        if not str(extra.get(key) or "").strip() or str(extra.get(key)).strip() == "-"
    ]


def validate_payment_completeness(payments) -> None:
    """Stop incomplete native payment data before any DMS write, including non-LINE callers."""
    for payment in payments or ():
        channel = payment.get("channel")
        extra = payment.get("extra") or {}
        missing = [
            key
            for key in _PAYMENT_TEXT_FIELD.get(channel, {})
            if not str(extra.get(key) or "").strip() or str(extra.get(key)).strip() == "-"
        ]
        if missing:
            raise DMSClientError(
                str(channel) + " payment is incomplete; missing=" + ",".join(missing),
                "ERR_DMS_PAYMENT_INCOMPLETE",
            )


def payment_form_fields(payments: tuple) -> Dict[str, str]:
    """聚合订金支付渠道 → DMS 表单字段。

    DMS 每个渠道只有一组固定字段，因此同渠道重复必须拦截，不能拼接后伪装成一笔。
    空 payments 返回空 dict —— 调用方保留表单默认 txtearnestmoney="0.00"。
    """
    validate_payment_completeness(payments)
    totals: Dict[str, Decimal] = {}
    extras: Dict[str, dict] = {}
    for pay in payments:
        channel = pay.get("channel")
        if channel not in _PAYMENT_CHANNELS:
            raise ValueError(f"unknown payment channel: {channel!r}")
        if channel in totals:
            raise ValueError(f"duplicate payment channel: {channel!r}")
        amount = str(pay.get("amount") or "0").replace(",", "")
        totals[channel] = Decimal(amount)
        extra = dict(pay.get("extra") or {})
        extras[channel] = extra

    fields: Dict[str, str] = {}
    grand_total = Decimal("0")
    for channel in _PAYMENT_CHANNELS:  # 固定顺序,输出确定可断言
        if channel not in totals:
            continue
        grand_total += totals[channel]
        fields[_PAYMENT_MONEY_FIELD[channel]] = f"{totals[channel]:.2f}"
        for slot, form_field in _PAYMENT_TEXT_FIELD.get(channel, {}).items():
            extra = extras.get(channel, {})
            value = extra.get(slot)
            if value and value != "-":
                fields[form_field] = str(value)
    if fields:
        fields["txtearnestmoney"] = f"{grand_total:.2f}"
    return fields

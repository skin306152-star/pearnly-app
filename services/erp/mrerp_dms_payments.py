# -*- coding: utf-8 -*-
"""订金支付渠道 → DMS 订车单表单字段的纯映射(建单时由 mrerp_dms_client_ops 聚合进表单)。

逐问收上来的 payments 是 [{channel, amount, extra}] 列表,DMS 表单却是每渠道一组固定
字段名。这层只做映射与聚合:零 IO、可单测、金额一律 Decimal。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List

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

# 每渠道的文本 extra 槽位 → 表单字段;transfer 的 src/dst 为空或 "-" 时不写。
_PAYMENT_TEXT_FIELD = {
    "transfer": {"src": "txtaccountnumtffrom", "dst": "txtaccountnumtfmon"},
    "cheque": {"ref": "txtchequeno"},
    "cashier_cheque": {"ref": "txtcashiercqno"},
    "card": {"ref": "txttypenamecddbc"},
    "other": {"detail": "txtdetailother"},
}


def payment_form_fields(payments: tuple) -> Dict[str, str]:
    """聚合订金支付渠道 → DMS 表单字段。

    同渠道多条:金额 Decimal 相加、文本 extra 用 " / " 连接。
    空 payments 返回空 dict —— 调用方保留表单默认 txtearnestmoney="0.00"。
    """
    totals: Dict[str, Decimal] = {}
    texts: Dict[str, Dict[str, List[str]]] = {}
    for pay in payments:
        channel = pay.get("channel")
        if channel not in _PAYMENT_CHANNELS:
            raise ValueError(f"unknown payment channel: {channel!r}")
        amount = str(pay.get("amount") or "0").replace(",", "")
        totals[channel] = totals.get(channel, Decimal("0")) + Decimal(amount)
        extra = pay.get("extra") or {}
        for slot, value in extra.items():
            if slot in ("src", "dst", "ref", "detail") and value and value != "-":
                texts.setdefault(channel, {}).setdefault(slot, []).append(str(value))

    fields: Dict[str, str] = {}
    grand_total = Decimal("0")
    for channel in _PAYMENT_CHANNELS:  # 固定顺序,输出确定可断言
        if channel not in totals:
            continue
        grand_total += totals[channel]
        fields[_PAYMENT_MONEY_FIELD[channel]] = f"{totals[channel]:.2f}"
        for slot, form_field in _PAYMENT_TEXT_FIELD.get(channel, {}).items():
            values = texts.get(channel, {}).get(slot)
            if values:
                fields[form_field] = " / ".join(values)
    if fields:
        fields["txtearnestmoney"] = f"{grand_total:.2f}"
    return fields

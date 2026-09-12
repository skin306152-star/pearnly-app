# -*- coding: utf-8 -*-
"""Collect the native transfer fields without mistaking a bank for a company account."""

from __future__ import annotations

import re

from services.erp.mrerp_dms_company_banks import company_bank_payment_extra, PAYMENT_CHANNEL_BANKS
from services.line_dms import booking_qa_payment, qa_cards
from services.line_dms._out import _send
from services.line_dms.qa_util import complete_channel, find_row, THAI_DIGITS


def parse_details(text, destination=False):
    keys = (
        ("dst_business_name", "dst_account_no", "dst_branch_name")
        if destination
        else ("src_account_name", "src_account_no", "src_branch_name", "src_time")
    )
    parts = [value.strip() for value in str(text or "").replace("｜", "|").split("|")]
    if len(parts) != len(keys) or any(
        not value or value == "-" or len(value) > 160 for value in parts
    ):
        return None
    if not any(ch.isdigit() for ch in parts[1].translate(THAI_DIGITS)):
        return None
    if not destination and not re.fullmatch(
        r"(?:[01]?\d|2[0-3]):[0-5]\d", parts[-1].translate(THAI_DIGITS)
    ):
        return None
    return dict(zip(keys, parts))


async def pick_bank(
    tenant_id, line_user_id, qa, value, reply_token, *, source=False, masters, persist, send_step
):
    channel = qa["pending_channel"].get("channel")
    other = qa.get("step") == "pay_bank"
    key = (
        PAYMENT_CHANNEL_BANKS[channel] if other else ("source_banks" if source else "company_banks")
    )
    rows = await masters(tenant_id, line_user_id, qa, key, persist=persist)
    row = find_row(rows, value)
    if row is None:
        await send_step(tenant_id, line_user_id, qa, qa["step"], reply_token)
        return
    qa.setdefault("pages", {}).pop(key, None)
    extra = qa["pending_channel"].setdefault("extra", {})
    if other:
        extra.update(bank_id=str(row[0]), bank_name=str(row[2] or row[1]))
    elif source:
        extra.update(src_bank_id=str(row[0]), src_bank_name=str(row[2] or row[1]))
    else:
        if extra.get("dst_id") and str(extra["dst_id"]) != str(row[0]):
            extra.pop("dst_account_no", None)
            extra.pop("dst_branch_name", None)
        extra.update(company_bank_payment_extra(row, extra))
    qa["step"] = "pay_ref" if other else ("pay_src_detail" if source else "pay_dst_detail")
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, qa["step"], reply_token)


async def collect_details(tenant_id, line_user_id, qa, text, reply_token, *, persist, send_step):
    destination = qa.get("step") == "pay_dst_detail"
    details = parse_details(text, destination=destination)
    if details is None:
        _send(line_user_id, qa_cards.ask_transfer_details(destination), reply_token)
        return
    qa["pending_channel"].setdefault("extra", {}).update(details)
    if not destination:
        qa["step"] = "pay_dst"
        await persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "pay_dst", reply_token)
        return
    complete_channel(qa)
    if not (qa.get("files") or {}).get("slip_mid"):
        await booking_qa_payment.request_slip(
            tenant_id,
            line_user_id,
            qa,
            "pay_more",
            reply_token,
            persist=persist,
            send_step=send_step,
        )
        return
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_more", reply_token)

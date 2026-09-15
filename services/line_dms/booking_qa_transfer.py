# -*- coding: utf-8 -*-
"""转账只收金额和收款银行，再收凭证；支票、本票和银行卡保留各自资料。"""

from __future__ import annotations

from services.erp.mrerp_dms_company_banks import (
    company_bank_payment_extra,
    manual_bank_allowed_for_rows,
    PAYMENT_CHANNEL_BANKS,
)
from services.erp.mrerp_dms_payments import MANUAL_BANK_FLAG
from services.line_dms import booking_payments, booking_qa_payment, booking_qa_sync, qa_cards
from services.line_dms._out import _send
from services.line_dms.qa_util import (
    CHANNEL_EXTRA_SHAPE,
    complete_channel,
    find_row,
    parse_amount,
)

TEXT_STEPS = frozenset({"pay_amount", "pay_bank", "pay_ref"})


def masters_reader(tenant_id, *, persist):
    """会话快照主档读取器:与 send_step/question 同一条路径(会话内复用,不发实时 DMS 读)。"""
    default_persist = persist

    def read(line_user_id, qa, key, persist=None):
        return booking_qa_sync.masters(
            tenant_id, line_user_id, qa, key, persist=persist or default_persist
        )

    return read


def manual_bank(qa, key) -> bool:
    """支票、本票和银行卡目录为空时允许手工银行名称。"""
    if key in (qa.get("manual_banks") or ()):
        return True
    return manual_bank_allowed_for_rows(
        key, ((qa.get("master_snapshot") or {}).get("rows") or {}).get(key)
    )


def _mark_manual_bank(qa, key) -> None:
    qa["manual_banks"] = sorted({*(qa.get("manual_banks") or ()), key})


def _clear_manual_bank(qa, key) -> None:
    qa["manual_banks"] = [item for item in (qa.get("manual_banks") or ()) if item != key]


async def prepare_channel_bank_step(tenant_id, line_user_id, qa, *, masters, persist) -> str:
    """支票/本票/银行卡银行步骤:目录有行 → pay_bank(选择);权威为空 → pay_ref(手工)。"""
    key = PAYMENT_CHANNEL_BANKS[(qa.get("pending_channel") or {}).get("channel")]
    rows = await masters(line_user_id, qa, key, persist=persist)
    if rows:
        _clear_manual_bank(qa, key)
        return "pay_bank"
    _mark_manual_bank(qa, key)
    return "pay_ref"


def channel_ref_question(qa) -> dict:
    """支票/本票/银行卡资料问法:该渠道目录权威为空时多问一项银行名称。"""
    channel = str((qa.get("pending_channel") or {}).get("channel") or "")
    key = PAYMENT_CHANNEL_BANKS.get(channel)
    return qa_cards.ask_pay_ref(channel, manual_bank=bool(key) and manual_bank(qa, key))


async def handle_text(
    step, tenant_id, line_user_id, qa, text, reply_token, *, persist, send_step, reask
) -> None:
    """转账金额后直接选择收款银行；其他渠道保留各自资料。"""
    masters = masters_reader(tenant_id, persist=persist)
    if step == "pay_amount":
        await _on_amount(
            tenant_id,
            line_user_id,
            qa,
            text,
            reply_token,
            masters=masters,
            persist=persist,
            send_step=send_step,
        )
    elif step == "pay_bank":
        await _on_bank_step_text(
            tenant_id,
            line_user_id,
            qa,
            text,
            reply_token,
            masters=masters,
            persist=persist,
            send_step=send_step,
            reask=reask,
        )
    else:  # pay_ref:渠道补充资料
        await _on_reference_text(
            tenant_id, line_user_id, qa, text, reply_token, persist=persist, send_step=send_step
        )


async def _on_amount(
    tenant_id, line_user_id, qa, text, reply_token, *, masters, persist, send_step
) -> None:
    amount = parse_amount(text)
    if amount is None:
        _send(line_user_id, qa_cards.bad_amount(), reply_token)
        return
    pending = qa["pending_channel"]
    pending["amount"] = f"{amount:.2f}"
    shape = CHANNEL_EXTRA_SHAPE.get(pending.get("channel", ""))
    if shape == "destination":
        next_step = "pay_dst"
    elif shape == "ref":
        next_step = await prepare_channel_bank_step(
            tenant_id, line_user_id, qa, masters=masters, persist=persist
        )
    elif shape == "detail":
        next_step = "pay_ref"
    else:  # cash:金额即渠道完结
        complete_channel(qa)
        next_step = "pay_more"
    qa["step"] = next_step
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, next_step, reply_token)


async def _on_bank_step_text(
    tenant_id, line_user_id, qa, text, reply_token, *, masters, persist, send_step, reask
) -> None:
    """pay_bank 收到文字:目录有行 → 原步重问;权威为空 → 这条文字就是手工银行资料。"""
    next_step = await prepare_channel_bank_step(
        tenant_id, line_user_id, qa, masters=masters, persist=persist
    )
    if next_step != "pay_ref":
        await reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    qa["step"] = next_step
    await persist(tenant_id, line_user_id, qa)
    await _on_reference_text(
        tenant_id, line_user_id, qa, text, reply_token, persist=persist, send_step=send_step
    )


async def _on_reference_text(
    tenant_id, line_user_id, qa, text, reply_token, *, persist, send_step
) -> None:
    """渠道补充资料:该渠道银行目录权威为空时多解析一段手工银行名称。"""
    channel = str((qa.get("pending_channel") or {}).get("channel") or "")
    key = PAYMENT_CHANNEL_BANKS.get(channel)
    manual = bool(key) and manual_bank(qa, key)
    detail = booking_payments.parse_payment_detail(channel, text, manual_bank=manual)
    if detail is None:
        _send(line_user_id, qa_cards.bad_payment_detail(), reply_token)
        return
    extra = qa["pending_channel"].setdefault("extra", {})
    extra.update(detail)
    if manual:
        extra[MANUAL_BANK_FLAG] = "1"
    complete_channel(qa)
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_more", reply_token)


async def pick_bank(
    tenant_id, line_user_id, qa, value, reply_token, *, masters, persist, send_step
):
    channel = qa["pending_channel"].get("channel")
    other = qa.get("step") == "pay_bank"
    key = PAYMENT_CHANNEL_BANKS[channel] if other else "company_banks"
    rows = await masters(tenant_id, line_user_id, qa, key, persist=persist)
    row = find_row(rows, value)
    if row is None:
        await send_step(tenant_id, line_user_id, qa, qa["step"], reply_token)
        return
    qa.setdefault("pages", {}).pop(key, None)
    extra = qa["pending_channel"].setdefault("extra", {})
    if other:
        extra.update(bank_id=str(row[0]), bank_name=str(row[2] or row[1]))
    else:
        if extra.get("dst_id") and str(extra["dst_id"]) != str(row[0]):
            extra.pop("dst_account_no", None)
            extra.pop("dst_branch_name", None)
        extra.update(company_bank_payment_extra(row, extra))
    if not other:
        await _finish_destination(
            tenant_id,
            line_user_id,
            qa,
            reply_token,
            persist=persist,
            send_step=send_step,
        )
        return
    qa["step"] = "pay_ref"
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, qa["step"], reply_token)


async def _finish_destination(tenant_id, line_user_id, qa, reply_token, *, persist, send_step):
    """Finish a transfer after selecting the receiving bank."""
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

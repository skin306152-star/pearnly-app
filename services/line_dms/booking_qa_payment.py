# -*- coding: utf-8 -*-
"""LINE DMS 订车付款方式与转账凭证的一致性步进。"""

from __future__ import annotations

from services.line_dms import qa_cards


async def handle(
    action,
    tenant_id,
    line_user_id,
    qa,
    value,
    reply_token,
    *,
    persist,
    send_step,
    reask,
    to_preview,
) -> None:
    common = {
        "persist": persist,
        "send_step": send_step,
        "reask": reask,
    }
    if action == "pay":
        await pick_channel(tenant_id, line_user_id, qa, value, reply_token, **common)
    elif action == "more":
        await pick_more(
            tenant_id,
            line_user_id,
            qa,
            value,
            reply_token,
            to_preview=to_preview,
            **common,
        )
    else:
        await pick_slip_conflict(
            tenant_id,
            line_user_id,
            qa,
            value,
            reply_token,
            to_preview=to_preview,
            **common,
        )


async def pick_channel(
    tenant_id, line_user_id, qa, value, reply_token, *, persist, send_step, reask
) -> None:
    if value not in qa_cards.PAY_LABELS:
        await reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    qa["pending_channel"] = {"channel": value}
    qa["step"] = "pay_amount"
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_amount", reply_token)


async def request_slip(
    tenant_id, line_user_id, qa, destination, reply_token, *, persist, send_step
) -> None:
    qa["step"] = "slip_after"
    qa["after_slip"] = destination
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "slip_after", reply_token)


async def pick_more(
    tenant_id,
    line_user_id,
    qa,
    value,
    reply_token,
    *,
    persist,
    send_step,
    reask,
    to_preview,
) -> None:
    if value == "add":
        qa["step"] = "pay_channel"
        await persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "pay_channel", reply_token)
        return
    if value != "done":
        await reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    has_transfer = "transfer" in {p.get("channel") for p in qa.get("payments") or []}
    has_slip = bool((qa.get("files") or {}).get("slip_mid"))
    if has_transfer and not has_slip:
        await request_slip(
            tenant_id,
            line_user_id,
            qa,
            "preview",
            reply_token,
            persist=persist,
            send_step=send_step,
        )
        return
    if has_slip and not has_transfer:
        qa["step"] = "slip_conflict"
        await persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "slip_conflict", reply_token)
        return
    await to_preview(tenant_id, line_user_id, qa, reply_token)


async def pick_slip_conflict(
    tenant_id,
    line_user_id,
    qa,
    value,
    reply_token,
    *,
    persist,
    send_step,
    reask,
    to_preview,
) -> None:
    if value == "add":
        qa["pending_channel"] = {"channel": "transfer"}
        qa["step"] = "pay_amount"
        await persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "pay_amount", reply_token)
        return
    if value == "remove":
        qa.setdefault("files", {})["slip_mid"] = None
        qa["step"] = "pay_more"
        await persist(tenant_id, line_user_id, qa)
        await to_preview(tenant_id, line_user_id, qa, reply_token)
        return
    await reask(tenant_id, line_user_id, qa, "", reply_token)

# -*- coding: utf-8 -*-
"""Collect the native transfer fields without mistaking a bank for a company account.

来源/支票/本票/银行卡银行目录**权威为空**时(生产租户真实形态:company_banks 有行、这四类
0 行),退回改前的可填写文本流程:问银行名称 + 原生必要资料,hidden bank id 留空。目录有行
时照旧走实时目录选择;目录读取失败由 snapshot_rows 抛 MasterSyncError(fail closed),不落进这条。
"""

from __future__ import annotations

import re

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
    THAI_DIGITS,
)

_SRC_KEYS = ("src_account_name", "src_account_no", "src_branch_name", "src_time")
_SRC_MANUAL_KEYS = ("src_bank_name", *_SRC_KEYS)
_DST_KEYS = ("dst_business_name", "dst_account_no", "dst_branch_name")
_TIME = re.compile(r"(?:[01]?\d|2[0-3]):[0-5]\d")

# 逐问里所有付款资料文本步:金额 / 来源银行(含目录为空时的手工名称)/ 渠道资料。
TEXT_STEPS = frozenset(
    {"pay_amount", "pay_src", "pay_src_detail", "pay_dst_detail", "pay_bank", "pay_ref"}
)


def masters_reader(tenant_id, *, persist):
    """会话快照主档读取器:与 send_step/question 同一条路径(会话内复用,不发实时 DMS 读)。"""
    default_persist = persist

    def read(line_user_id, qa, key, persist=None):
        return booking_qa_sync.masters(
            tenant_id, line_user_id, qa, key, persist=persist or default_persist
        )

    return read


def parse_details(text, destination=False, manual_source=False):
    """一行资料 → 原生字段。manual_source=来源银行目录权威为空:首段是手工银行名称。"""
    keys = _DST_KEYS if destination else (_SRC_MANUAL_KEYS if manual_source else _SRC_KEYS)
    parts = [value.strip() for value in str(text or "").replace("｜", "|").split("|")]
    if len(parts) != len(keys) or any(
        not value or value == "-" or len(value) > 160 for value in parts
    ):
        return None
    account_index = keys.index("dst_account_no" if destination else "src_account_no")
    if not any(ch.isdigit() for ch in parts[account_index].translate(THAI_DIGITS)):
        return None
    if not destination and not _TIME.fullmatch(parts[-1].translate(THAI_DIGITS)):
        return None
    return dict(zip(keys, parts))


def manual_bank(qa, key) -> bool:
    """本会话该渠道银行目录是否权威为空(→ 银行名称手工填)。

    兼容老会话:已经卡在 pay_src 且 master_snapshot 里该目录是空表的会话,不必重新开局、
    不必重扫身份证,直接按手工流程继续。"""
    if key in (qa.get("manual_banks") or ()):
        return True
    return manual_bank_allowed_for_rows(
        key, ((qa.get("master_snapshot") or {}).get("rows") or {}).get(key)
    )


def _mark_manual_bank(qa, key) -> None:
    qa["manual_banks"] = sorted({*(qa.get("manual_banks") or ()), key})


def _clear_manual_bank(qa, key) -> None:
    qa["manual_banks"] = [item for item in (qa.get("manual_banks") or ()) if item != key]


async def prepare_source_step(tenant_id, line_user_id, qa, *, masters, persist) -> str:
    """转账来源银行步骤:目录有行 → pay_src(实时目录选择);权威为空 → pay_src_detail(手工)。"""
    rows = await masters(line_user_id, qa, "source_banks", persist=persist)
    if rows:
        _clear_manual_bank(qa, "source_banks")
        return "pay_src"
    _mark_manual_bank(qa, "source_banks")
    return "pay_src_detail"


async def prepare_channel_bank_step(tenant_id, line_user_id, qa, *, masters, persist) -> str:
    """支票/本票/银行卡银行步骤:目录有行 → pay_bank(选择);权威为空 → pay_ref(手工)。"""
    key = PAYMENT_CHANNEL_BANKS[(qa.get("pending_channel") or {}).get("channel")]
    rows = await masters(line_user_id, qa, key, persist=persist)
    if rows:
        _clear_manual_bank(qa, key)
        return "pay_bank"
    _mark_manual_bank(qa, key)
    return "pay_ref"


def transfer_details_question(qa) -> dict:
    """转账资料问法:来源银行目录权威为空时先问银行名称(与 collect_details 同一判据)。"""
    destination = qa.get("step") == "pay_dst_detail"
    manual_source = not destination and manual_bank(qa, "source_banks")
    return qa_cards.ask_transfer_details(destination, manual_source=manual_source)


def channel_ref_question(qa) -> dict:
    """支票/本票/银行卡资料问法:该渠道目录权威为空时多问一项银行名称。"""
    channel = str((qa.get("pending_channel") or {}).get("channel") or "")
    key = PAYMENT_CHANNEL_BANKS.get(channel)
    return qa_cards.ask_pay_ref(channel, manual_bank=bool(key) and manual_bank(qa, key))


async def handle_text(
    step, tenant_id, line_user_id, qa, text, reply_token, *, persist, send_step, reask
) -> None:
    """付款资料文本步:金额 → (目录为空时先问)银行名称+账户资料 → 公司收款银行 → 渠道资料。"""
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
    elif step == "pay_src":
        await _on_source_step_text(
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
    elif step in ("pay_src_detail", "pay_dst_detail"):
        await collect_details(
            tenant_id, line_user_id, qa, text, reply_token, persist=persist, send_step=send_step
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
    if shape == "src_dst":
        # 来源银行目录有行 → 选按钮;权威为空(生产租户形态)→ 直接问手工银行名称+账户资料,
        # 不再停在 pay_src 报「读不到银行列表」。
        next_step = await prepare_source_step(
            tenant_id, line_user_id, qa, masters=masters, persist=persist
        )
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


async def _on_source_step_text(
    tenant_id, line_user_id, qa, text, reply_token, *, masters, persist, send_step, reask
) -> None:
    """pay_src 收到文字:目录有行 → 原步重问;权威为空 → 这条文字就是手工来源银行资料。

    老会话(已卡在 pay_src、快照里 source_banks=[])重试即从此继续,不必重扫身份证。"""
    next_step = await prepare_source_step(
        tenant_id, line_user_id, qa, masters=masters, persist=persist
    )
    if next_step != "pay_src_detail":
        await reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    qa["step"] = next_step
    await persist(tenant_id, line_user_id, qa)
    await collect_details(
        tenant_id, line_user_id, qa, text, reply_token, persist=persist, send_step=send_step
    )


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
    manual_source = not destination and manual_bank(qa, "source_banks")
    details = parse_details(text, destination=destination, manual_source=manual_source)
    if details is None:
        _send(line_user_id, transfer_details_question(qa), reply_token)
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

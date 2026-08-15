# -*- coding: utf-8 -*-
"""DMS 订车阶段:逐问落定 → 预览确认 → 建订车单 + 挂附件(DL-4a/DL-7)。

flow.py 收口于「客户档落定」,订车这段独立到本文件(flow 已近 500 行)。职责:
  · handle_postback —— 预览卡的 [ยืนยันจอง]/[ยกเลิก](confirm/cancel_booking)。
  · confirm 执行 —— 登录 DMS → resolve+create 订车单 → 挂附件 → 回执 + push 台账 + 刷主档缓存。
confirm 用 LINE postback 的 nonce 二次防重(照 flow 范式:先清 nonce 再执行,同一 nonce
二次点击此后必 mismatch)。执行器约定:一切业务数据从 payload["qa"] 读(逐问状态机产出,
A4 定义形状),顶层 payload 只有 nonce 与 collecting 残留键。
"""

from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from core import db
from services.erp import dms_id_ocr as _id_ocr
from services.line_binding import line_client
from services.line_dms import _out, cards, masters_cache, qa_cards, store
from services.line_dms._out import _CHANNEL, _push, _reply, _thr

logger = logging.getLogger(__name__)

BOOKING_ACTIONS = frozenset({cards.ACT_CONFIRM_BOOKING, cards.ACT_CANCEL_BOOKING})

# 后台调度 + LINE 出口(_CHANNEL/_thr/_reply/_push 见 _out)· tag 供后台任务日志定位。
_spawn = _out.make_spawn("line_dms.booking")

# 附件种类表:(qa.files 键尾, DMS 显示名, 落盘文件名)。
_ATTACH_KINDS = (
    ("id_card", "สำเนาบัตรประชาชน", "idcard.jpg"),
    ("slip", "ใบโอนเงินจอง", "slip.jpg"),
)


# ── 预览卡 postback:确认建单 / 取消 ─────────────────────────────────────
async def handle_postback(
    binding: dict, line_user_id: str, reply_token: str, action: str, pb: dict
) -> None:
    """预览卡按钮:核对 booking_review 态 + nonce → 建单 / 取消。"""
    tenant = binding["tenant_id"]
    if action == cards.ACT_CANCEL_BOOKING:
        await _thr(store.clear_session, tenant, line_user_id)
        _reply(reply_token, cards.TXT_BOOKING_CANCELLED)
        return

    # 确认守卫(booking_review 态 + nonce 吻合)原子清 nonce 并回 payload;不符/过期 → 过期
    # 话术、绝不建单。清 nonce 后同一 nonce 二次点击此后必 mismatch(防双建单)。
    payload = await _thr(
        store.consume_nonce, tenant, line_user_id, "booking_review", pb.get("nonce")
    )
    if payload is None:
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    _spawn(_execute_booking(binding, line_user_id, payload))


# ── 建订车单 ─────────────────────────────────────────────────────────────
async def _execute_booking(binding: dict, line_user_id: str, payload: dict) -> None:
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    qa = payload.get("qa") or {}
    await _thr(line_client.start_loading, line_user_id, 30, channel=_CHANNEL)
    ep = await _thr(_id_ocr.resolve_dms_endpoint, user_id, qa.get("endpoint_id"))
    if not ep:
        _push(line_user_id, cards.TXT_NO_ENDPOINT)
        return
    attach_files, attach_failed = await _download_attach_files(qa)
    result = await _thr(_book_in_session, ep, payload, attach_files, attach_failed)
    await _thr(_log_booking, user_id, ep, payload, result)
    if result.get("ok"):
        answers = qa.get("answers") or {}
        text = cards.booking_receipt_text(
            result.get("booking_no", ""),
            str((answers.get("car") or {}).get("label") or ""),
            str(answers.get("delivery_date_be") or ""),
            str((qa.get("advisor") or {}).get("name") or ""),
        )
        # 建单成功但附件没挂全 → 如实补一句,绝不谎报附件成功(四态诚实)。
        if not result.get("attach_ok"):
            text = f"{text}\n{qa_cards.TXT_ATTACH_FAIL}"
        _push(line_user_id, text)
        await _thr(store.clear_session, tenant, line_user_id)
    else:
        fr = result.get("error_friendly") or {}
        _push(line_user_id, fr.get("th") or cards.TXT_BOOKING_FAIL)


async def _download_attach_files(qa: dict) -> Tuple[List[dict], List[dict]]:
    """按 qa.files 下载附件字节(经 _thr 离开事件循环);下载失败单独记,不阻断建单。

    LINE 内容下载可能已过期(消息 30 天后取不到),那按附件失败记、由回执如实告知。
    """
    files = qa.get("files") or {}
    downloaded: List[dict] = []
    failed: List[dict] = []
    for key, display, fname in _ATTACH_KINDS:
        mid = files.get(f"{key}_mid")
        if not mid:
            continue
        content = await _thr(line_client.download_message_content, mid, channel=_CHANNEL)
        if not content:
            failed.append({"display_name": display, "error": "line content download failed"})
            continue
        downloaded.append(
            {
                "display_name": display,
                "filename": fname,
                "content_type": _content_type(content),
                "content": content,
            }
        )
    return downloaded, failed


def _content_type(content: bytes) -> str:
    """附件内容类型:LINE 下载客户端不暴露响应头,按字节头推断,拿不到回落 image/jpeg。"""
    if content[:4] == b"\x89PNG":
        return "image/png"
    if content[:2] == b"\xff\xd8":
        return "image/jpeg"
    return "image/jpeg"


def _book_in_session(
    ep: dict,
    payload: dict,
    attach_files: Optional[List[dict]] = None,
    attach_failed: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """一个 DMS 会话内:解析订车载荷 → 建单 → 挂附件 → 顺手全量刷主档缓存(零额外登录)。

    逐问选的 place/term/regis/car/paint id 覆盖端点默认;advisor 在逐问开局就按操作员的
    DMS 账号匹配好(或端点上钉死)存进 qa["advisor"] —— 建单层(_advisor_ref_strict)按该
    id 严格校验,匹配不上宁可报错也不落到别人头上;交车日用逐问值覆盖(端点默认只给推算基线)。
    附件在同一会话挂载:create 成功后、主档刷新前调 cl.attach_booking_files。返回 {ok,
    booking_no, booking_id, attach_ok, attached, attach_failed} 或 _run_logged_in 的
    _err dict(ok=False)。
    """
    from services.erp.erp_dms_intake import _run_logged_in
    from services.erp.mrerp_dms_models import BookingDefaults

    qa = payload.get("qa") or {}
    answers = qa.get("answers") or {}
    adv = qa.get("advisor") or {}
    defaults = dataclasses.replace(
        BookingDefaults.from_config(ep.get("config") or {}),
        advisor_id=str(adv.get("id") or ""),
        # 主档列表抖动时建单层按名字降级落顾问,故名字也要一路带到 defaults。
        advisor_name=str(adv.get("name") or ""),
        car_id=str((answers.get("car") or {}).get("id") or ""),
        paint_id=str((answers.get("paint") or {}).get("id") or ""),
        place_book_id=str((answers.get("place") or {}).get("id") or ""),
        term_sale_id=str((answers.get("term") or {}).get("id") or ""),
        regis_behalf_id=str((answers.get("regis") or {}).get("id") or ""),
    )
    card = _card_payload(payload)
    delivery_be = str(answers.get("delivery_date_be") or "")
    customer_id = str((qa.get("customer") or {}).get("id") or "")

    def _do(cl, adapter):
        from services.erp.mrerp_dms_booking_customer import card_from_customer
        from services.erp.mrerp_dms_company_banks import validate_company_bank_payments

        master_card = card_from_customer(
            cl,
            customer_id=customer_id,
            people_id=card.people_id,
        )
        booking = cl.resolve_booking_payload(defaults, master_card)
        if delivery_be:
            payments = validate_company_bank_payments(adapter, qa.get("payments") or [])
            booking = dataclasses.replace(
                booking,
                delivery_date_be=delivery_be,
                regis_name=str(answers.get("regis_name") or ""),
                payments=tuple(payments),
            )
        booking_id, booking_no = cl.create_booking_via_form(
            customer_id=customer_id, booking=booking, card=master_card
        )
        attached = 0
        failed = list(attach_failed or [])
        if attach_files:
            res = cl.attach_booking_files(booking_id=booking_id, files=attach_files)
            attached = int(res.get("attached") or 0)
            failed += list(res.get("failed") or [])
        masters_cache.refresh_from_client(ep, cl)
        return {
            "ok": True,
            "booking_id": booking_id,
            "booking_no": booking_no,
            "attach_ok": not failed,
            "attached": attached,
            "attach_failed": failed,
        }

    return _run_logged_in(ep, _do)


def _card_payload(payload: dict):
    """从 qa.draft 重建 ThaiIdCardPayload(客户已建,建单表单要回显身份/地址)。"""
    from services.erp.mrerp_dms_models import ThaiAddress, ThaiIdCardPayload

    qa = payload.get("qa") or {}
    d = qa.get("draft") or {}
    name = str((qa.get("customer") or {}).get("name") or "").strip()
    address = ThaiAddress(
        house_no=str(d.get("house_no") or ""),
        province_id=str(d.get("province_id") or ""),
        district_id=str(d.get("district_id") or ""),
        subdistrict_id=str(d.get("subdistrict_id") or ""),
        zipcode_id=str(d.get("zipcode_id") or ""),
        moo=str(d.get("moo") or ""),
        soi=str(d.get("soi") or ""),
        road=str(d.get("road") or ""),
    )
    return ThaiIdCardPayload(
        people_id=str(d.get("people_id") or ""),
        first_name=name,
        last_name="",
        birthday_be=str(d.get("birthday_be") or ""),
        address=address,
        prefix_id=str(d.get("prefix_id") or "17") or "17",
        prefix_name="",
        phone=str(d.get("phone") or "0800000000") or "0800000000",
    )


def _log_booking(user_id: str, ep: dict, payload: dict, result: dict) -> None:
    """订车推送台账(与 flow 同一 erp_push_logs)· request_body.trigger='line_dms',
    BK 单号进 invoice_no 位(照客户 push 把外部单号放该列的先例),push_type 保持 'id_card'。
    qa 块只进摘要(place/term/regis/渠道/总额/凭证有无),audit 过大不进台账、留会话。"""
    ok = bool(result.get("ok"))
    qa = payload.get("qa") or {}
    answers = qa.get("answers") or {}
    adv = qa.get("advisor") or {}
    payments = qa.get("payments") or []
    request_body = {
        "adapter": "mrerp_dms",
        "trigger": "line_dms",
        "mode": "booking",
        "customer_id": str((qa.get("customer") or {}).get("id") or ""),
        "car_id": str((answers.get("car") or {}).get("id") or ""),
        "paint_id": str((answers.get("paint") or {}).get("id") or ""),
        "advisor_id": str(adv.get("id") or ""),
        # 归属名与 id 同层:对账翻台账时不用回查主档,也不用跨层拼。
        "advisor_name": str(adv.get("name") or ""),
        "qa": {
            "place_id": str((answers.get("place") or {}).get("id") or ""),
            "term_id": str((answers.get("term") or {}).get("id") or ""),
            "regis_id": str((answers.get("regis") or {}).get("id") or ""),
            "regis_name": str(answers.get("regis_name") or ""),
            "payments": [
                {"channel": str(p.get("channel") or ""), "amount": str(p.get("amount") or "")}
                for p in payments
            ],
            "earnest_total": str(qa_cards.deposit_total(payments)),
            "slip_attached": bool((qa.get("files") or {}).get("slip_mid")),
        },
    }
    response_body = {
        "booking_id": result.get("booking_id", ""),
        "booking_no": result.get("booking_no", ""),
    }
    if "attach_ok" in result:
        response_body["attach_ok"] = result.get("attach_ok")
        response_body["attached"] = result.get("attached", 0)
        response_body["attach_failed"] = result.get("attach_failed") or []
    if not ok:
        response_body["raw_error"] = (result.get("response_body") or {}).get("raw_error", "")
    db.insert_push_log(
        user_id,
        str(ep["id"]),
        None,
        result.get("booking_no") or "",
        str((qa.get("customer") or {}).get("name") or ""),
        None,
        "success" if ok else "failed",
        200 if ok else 0,
        request_body,
        json.dumps(response_body, ensure_ascii=False),
        result.get("error_code"),
        1,
        0,
        "id_card",
    )

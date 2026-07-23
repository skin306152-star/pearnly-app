# -*- coding: utf-8 -*-
"""DMS 订车阶段:选车面板落定 → 预览确认 → 建订车单(DL-4a)。

flow.py 收口于「客户档落定」,选车/订车这段独立到本文件(flow 已近 500 行)。职责:
  · offer_pick —— 客户档落定后签面板 token、置会话 picking、推选车入口按钮。
  · handle_postback —— 预览卡的 [ยืนยันจอง]/[ยกเลิก](confirm/cancel_booking)。
  · confirm 执行 —— 登录 DMS → resolve+create 订车单 → 回执 + push 台账 + 刷主档缓存。
面板 token 一次性(submit 侧轮换会话 nonce 使旧 token 失效);confirm 用 LINE postback 的
nonce 二次防重(照 flow 范式:先清 nonce 再执行,同一 nonce 二次点击此后必 mismatch)。
"""

from __future__ import annotations

import dataclasses
import json
import logging
import secrets
from typing import Any, Dict

from core import auth, db
from services.erp import dms_id_ocr as _id_ocr
from services.line_binding import line_client
from services.line_dms import _out, cards, masters_cache, store
from services.line_dms._out import _CHANNEL, _push, _reply, _thr

logger = logging.getLogger(__name__)

_PICK_URL = "https://pearnly.com/dms-pick"

BOOKING_ACTIONS = frozenset({cards.ACT_CONFIRM_BOOKING, cards.ACT_CANCEL_BOOKING})

# 后台调度 + LINE 出口(_CHANNEL/_thr/_reply/_push 见 _out)· tag 供后台任务日志定位。
_spawn = _out.make_spawn("line_dms.booking")


# ── 客户档落定 → 选车入口 ────────────────────────────────────────────────
async def offer_pick(
    binding: dict,
    line_user_id: str,
    *,
    endpoint_id: str,
    customer_id: str,
    draft: Dict[str, Any],
    name: str = "",
) -> None:
    """客户档落定后:置会话 picking + 推选车入口按钮(URI → 签名面板)。

    缺客户号(异常场景)或签 token 失败 → 清会话回干净态(客户已保存,订车非必经),但
    必须留一句交代:静默 return 会让人对着空气等一张永不到来的卡。会话存 user_id 供面板
    端点无登录态下解析 DMS 端点。"""
    tenant = binding["tenant_id"]
    if not customer_id:
        await _thr(store.clear_session, tenant, line_user_id)
        _push(line_user_id, cards.TXT_PICK_UNAVAILABLE)
        return
    nonce = secrets.token_hex(8)
    try:
        token = auth.create_dms_pick_token(
            tenant_id=tenant,
            line_user_id=line_user_id,
            endpoint_id=endpoint_id,
            nonce=nonce,
        )
    except Exception:
        logger.warning("[line_dms.booking] sign pick token failed; skip pick", exc_info=True)
        await _thr(store.clear_session, tenant, line_user_id)
        _push(line_user_id, cards.TXT_PICK_UNAVAILABLE)
        return
    payload = {
        "nonce": nonce,
        "endpoint_id": str(endpoint_id or ""),
        "customer_id": str(customer_id),
        "user_id": str(binding.get("user_id") or ""),
        "draft": draft or {},
        "name": name or (draft or {}).get("name", ""),
    }
    # 会话寿命按态查表(store._STATE_TTL_MINUTES):picking 必须活得比 15 分钟的面板 token 久。
    await _thr(store.set_session, tenant, line_user_id, "picking", payload)
    url = f"{_PICK_URL}?t={token}"
    line_client.push_messages(line_user_id, [cards.pick_button_message(url)], channel=_CHANNEL)


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
    await _thr(line_client.start_loading, line_user_id, 30, channel=_CHANNEL)
    ep = await _thr(_id_ocr.resolve_dms_endpoint, user_id, payload.get("endpoint_id"))
    if not ep:
        _push(line_user_id, cards.TXT_NO_ENDPOINT)
        return
    result = await _thr(_book_in_session, ep, payload)
    await _thr(_log_booking, user_id, ep, payload, result)
    if result.get("ok"):
        _push(
            line_user_id,
            cards.booking_receipt_text(
                result.get("booking_no", ""),
                str(payload.get("car") or ""),
                str(payload.get("delivery_date_be") or ""),
            ),
        )
        await _thr(store.clear_session, tenant, line_user_id)
    else:
        fr = result.get("error_friendly") or {}
        _push(line_user_id, fr.get("th") or cards.TXT_BOOKING_FAIL)


def _book_in_session(ep: dict, payload: dict) -> Dict[str, Any]:
    """一个 DMS 会话内:解析订车载荷 → 建单 → 顺手全量刷主档缓存(零额外登录)。

    面板选的 advisor/car/paint id 覆盖端点默认;交车日用面板值覆盖(端点默认只给推算基线)。
    返回 {ok, booking_no, booking_id} 或 _run_logged_in 的 _err dict(ok=False)。"""
    from services.erp.erp_dms_intake import _run_logged_in
    from services.erp.mrerp_dms_models import BookingDefaults

    defaults = dataclasses.replace(
        BookingDefaults.from_config(ep.get("config") or {}),
        advisor_id=str(payload.get("advisor_id") or ""),
        car_id=str(payload.get("car_id") or ""),
        paint_id=str(payload.get("paint_id") or ""),
    )
    card = _card_payload(payload)
    delivery_be = str(payload.get("delivery_date_be") or "")
    customer_id = str(payload.get("customer_id") or "")

    def _do(cl, adapter):
        booking = cl.resolve_booking_payload(defaults, card)
        if delivery_be:
            booking = dataclasses.replace(booking, delivery_date_be=delivery_be)
        booking_id, booking_no = cl.create_booking_via_form(
            customer_id=customer_id, booking=booking, card=card
        )
        masters_cache.refresh_from_client(ep, cl)
        return {"ok": True, "booking_id": booking_id, "booking_no": booking_no}

    return _run_logged_in(ep, _do)


def _card_payload(payload: dict):
    """从落定时存的 draft 重建 ThaiIdCardPayload(客户已建,建单表单要回显身份/地址)。"""
    from services.erp.mrerp_dms_models import ThaiAddress, ThaiIdCardPayload

    d = payload.get("draft") or {}
    name = str(payload.get("name") or d.get("name") or "").strip()
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
    BK 单号进 invoice_no 位(照客户 push 把外部单号放该列的先例),push_type 保持 'id_card'。"""
    ok = bool(result.get("ok"))
    request_body = {
        "adapter": "mrerp_dms",
        "trigger": "line_dms",
        "mode": "booking",
        "customer_id": str(payload.get("customer_id") or ""),
        "car_id": str(payload.get("car_id") or ""),
        "paint_id": str(payload.get("paint_id") or ""),
        "advisor_id": str(payload.get("advisor_id") or ""),
    }
    response_body = {
        "booking_id": result.get("booking_id", ""),
        "booking_no": result.get("booking_no", ""),
    }
    if not ok:
        response_body["raw_error"] = (result.get("response_body") or {}).get("raw_error", "")
    db.insert_push_log(
        user_id,
        str(ep["id"]),
        None,
        result.get("booking_no") or "",
        str(payload.get("name") or ""),
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

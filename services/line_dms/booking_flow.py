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

from services.line_dms import binding_guard

import dataclasses
import logging
import secrets
from typing import Any, Dict, List, Optional, Tuple

from services.cloud_tasks import dispatch as cloud_dispatch
from services.erp import dms_id_ocr as _id_ocr
from services.erp.session_lock import mrerp_booking_lock
from services.line_dms import (
    _out,
    booking_attempt,
    booking_ledger,
    cards,
    master_contract,  # noqa: F401  模块对外名保留(会话快照/测试夹具用它构造 qa)
    masters_cache,
    qa_cards,
    store,
)
from services.line_dms._out import _push, _reply, _send, _thr

logger = logging.getLogger(__name__)

BOOKING_ACTIONS = frozenset(
    {cards.ACT_CONFIRM_BOOKING, cards.ACT_CANCEL_BOOKING, cards.ACT_RETRY_BOOKING}
)
_RETRY_TTL_MINUTES = 30

# 后台调度 + LINE 出口(_thr/_reply/_push 见 _out)· tag 供后台任务日志定位。
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
        session = await _thr(store.get_session, tenant, line_user_id)
        marker = ((session or {}).get("payload") or {}).get("booking_attempt")
        if marker:
            _reply(reply_token, booking_attempt.message(marker))
            return
        await _thr(store.clear_session, tenant, line_user_id)
        _reply(reply_token, cards.TXT_BOOKING_CANCELLED)
        return

    if action == cards.ACT_RETRY_BOOKING:
        payload = await _thr(
            store.consume_nonce, tenant, line_user_id, "booking_review", pb.get("nonce")
        )
        if payload is None:
            _reply(reply_token, cards.TXT_EXPIRED)
            return
        cloud_dispatch.spawn(
            "dms.booking", _execute_booking, binding, line_user_id, payload, _legacy_spawn=_spawn
        )
        return

    # 确认守卫(booking_review 态 + nonce 吻合)原子清 nonce 并回 payload;不符/过期 → 过期
    # 话术、绝不建单。清 nonce 后同一 nonce 二次点击此后必 mismatch(防双建单)。
    payload = await _thr(
        store.consume_nonce, tenant, line_user_id, "booking_review", pb.get("nonce")
    )
    if payload is None:
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    cloud_dispatch.spawn(
        "dms.booking", _execute_booking, binding, line_user_id, payload, _legacy_spawn=_spawn
    )


# ── 建订车单 ─────────────────────────────────────────────────────────────
@binding_guard.bound_task
async def _execute_booking(binding: dict, line_user_id: str, payload: dict) -> None:
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    qa = payload.get("qa") or {}
    pending = await _thr(booking_attempt.pending, tenant, line_user_id, payload)
    if pending:
        _push(line_user_id, booking_attempt.message(pending))
        return
    await _thr(_out.start_loading, line_user_id)
    ep = await _thr(_id_ocr.resolve_dms_endpoint, user_id, qa.get("endpoint_id"))
    if not ep:
        _push(line_user_id, cards.TXT_NO_ENDPOINT)
        return
    attach_files, attach_failed = await _download_attach_files(qa)
    result = await _thr(
        _book_in_session,
        ep,
        payload,
        attach_files,
        attach_failed,
        on_attempt=booking_attempt.recorder(tenant, line_user_id, payload),
    )
    if result.get("preflight"):
        await _resume_after_master_change(binding, line_user_id, payload, result)
        return
    await _thr(booking_ledger.log_booking, user_id, ep, payload, result)
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
        await _thr(booking_attempt.clear_completed, tenant, line_user_id, payload)
    else:
        fr = result.get("error_friendly") or {}
        if result.get("error_code") == booking_attempt.UNKNOWN:
            _push(line_user_id, booking_attempt.message(result))
            return
        if result.get("error_code") == "ERR_DMS_PAYMENT_INCOMPLETE":
            nonce = secrets.token_hex(8)
            if not await _thr(_arm_retry, tenant, line_user_id, payload, nonce):
                return
            _push(line_user_id, fr.get("th") or cards.TXT_BOOKING_FAIL)
            _send(line_user_id, qa_cards.preview_card(qa, nonce))
            return
        if _retryable_result(result):
            retry_nonce = secrets.token_hex(8)
            armed = await _thr(
                _arm_retry,
                tenant,
                line_user_id,
                payload,
                retry_nonce,
            )
            if armed:
                _send(
                    line_user_id,
                    qa_cards.booking_retry_card(
                        fr.get("th") or cards.TXT_BOOKING_FAIL,
                        retry_nonce,
                    ),
                )
                return
        _push(line_user_id, fr.get("th") or cards.TXT_BOOKING_FAIL)


async def _resume_after_master_change(
    binding: dict, line_user_id: str, payload: dict, result: dict
) -> None:
    """确认瞬间主档有变化：改名重发摘要，删除则退回对应步骤重选。"""
    from services.line_dms import booking_qa, session_store

    tenant = binding["tenant_id"]
    qa = result.get("qa") or payload.get("qa") or {}
    changed = result.get("preflight") == "changed"
    nonce = secrets.token_hex(8) if changed else None
    state = (
        "booking_review"
        if changed
        else (None if result.get("field") == "advisor" else "booking_qa")
    )
    updated = {**payload, "qa": qa, "nonce": nonce} if changed else {"qa": qa}
    if not await _thr(
        session_store.replace_claimed_booking_payload,
        tenant,
        line_user_id,
        payload.get("nonce"),
        state,
        updated,
    ):
        return
    if changed:
        _send(line_user_id, qa_cards.master_changed())
        _send(line_user_id, qa_cards.preview_card(qa, nonce))
        return

    code = str(result.get("error_code") or "ERR_DMS_MASTER_UNMATCHED")
    _send(line_user_id, qa_cards.master_problem(code))
    if result.get("field") == "advisor":
        return
    await booking_qa.send_step(tenant, line_user_id, qa, qa.get("step") or "place")


def _retryable_result(result: Dict[str, Any]) -> bool:
    """只对明确发生在建单前的 DMS 阻塞开放重试,不重放未知写入结果。

    主档暂时读不到(ERR_DMS_MASTER_UNAVAILABLE)可等主档恢复后重试;主档已变更
    (ERR_DMS_MASTER_UNMATCHED)重试只会拿到同一份主档,必须让操作员重新选择。
    """
    if result.get("booking_id") or (result.get("response_body") or {}).get("submitted"):
        return False
    if result.get("error_code") == "ERR_DMS_MASTER_UNMATCHED":
        return False
    if result.get("error_code") in (
        "ERR_DMS_CONCURRENT_LOGIN",
        "ERR_DMS_MASTER_UNAVAILABLE",
        "ERR_DMS_CUSTOMER_LOOKUP",
    ):
        return True
    raw = str(result.get("raw_error") or "")
    response = result.get("response_body") or {}
    raw += " " + str(response.get("raw_error") or "")
    return "company bank master did not become ready" in raw


def _arm_retry(tenant: str, line_user_id: str, payload: dict, nonce: str) -> bool:
    """只重挂本次尚未提交的草稿；不得覆盖用户后续新建或取消的会话。"""
    from services.line_dms.session_store import replace_claimed_booking_payload

    return replace_claimed_booking_payload(
        tenant,
        line_user_id,
        payload.get("nonce"),
        "booking_review",
        {**payload, "nonce": nonce},
        ttl_minutes=_RETRY_TTL_MINUTES,
    )


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
        content = await _thr(_out.download_content, mid)
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
    *,
    on_attempt=None,
) -> Dict[str, Any]:
    """一个 DMS 会话内:权威复核 + 解析订车载荷 → 建单 → 挂附件 → 用同一份快照刷主档缓存。

    逐问选的 place/term/regis/car/paint id 覆盖端点默认;advisor 在逐问开局就按操作员的
    DMS 账号匹配好(或端点上钉死)存进 qa["advisor"] —— 载荷层按该 id 在权威名册里严格
    校验,匹配不上宁可报错也不落到别人头上;交车日用逐问值覆盖(端点默认只给推算基线)。
    附件在同一会话挂载:create 成功后调 cl.attach_booking_files。

    返回 {ok, booking_no, booking_id, attach_ok, attached, attach_failed} 或
    _run_logged_in 的 _err dict(ok=False)。
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
        nonlocal qa
        from services.erp.mrerp_dms_booking_customer import card_from_customer
        from services.erp.dms_admin_read import authoritative_read_session
        from services.erp.mrerp_dms_booking_org import resolve_booking_org
        from services.erp.mrerp_dms_booking_payload import build_booking_payload
        from services.erp.mrerp_dms_company_banks import (
            fetch_payment_bank_masters,
            validate_company_bank_payments,
        )
        from services.erp.mrerp_dms_payments import validate_payment_completeness
        from services.line_dms import booking_preflight

        validate_payment_completeness(qa.get("payments") or [])

        # 只读阶段:配了独立管理员凭据组时,这一块里的**一切读**都走管理员权威会话(销售常
        # 看不到车型/颜色/收款银行/客户档,销售视图会把 DMS 里还在的选择误判成不存在)。
        # 整块只解析一次管理员 transport;未配管理员即销售会话。
        # 提交前的权威取数在这里一次性做完:一份全量主档 + 选中车型颜色 + 顾问组织 + 客户档;
        # 载荷(build_booking_payload)吃这份快照**纯解析**,不再按 car/paint/place/term/
        # regis/advisor 逐字段回 DMS 取数(resolve_booking_payload 会重新取数,且在退出本块
        # 后就是销售视图 —— 核心契约会在解析层被绕过,这里必须不用它)。
        with authoritative_read_session(cl):
            # cl 此刻的 transport 就是权威只读闸(只许 GET/POST 到只读路径);退出即换回销售,
            # 下面的建单/附件/回读永不落管理员态。
            preflight = booking_preflight.readonly_preflight(
                cl,
                adapter,
                qa,
                fetch_masters=lambda client: client.fetch_masters(strict=True),
                fetch_payment_banks=lambda _adapter: fetch_payment_bank_masters(
                    _adapter, client=cl
                ),
            )
            if preflight["status"] != "ok":
                return {
                    "ok": False,
                    "preflight": preflight["status"],
                    "field": preflight.get("field", ""),
                    "error_code": preflight.get("code", "ERR_DMS_MASTER_CHANGED"),
                    "qa": preflight["qa"],
                }
            qa = payload["qa"] = preflight["qa"]
            masters, paints = preflight["masters"], preflight["paints"]

            if qa.get("customer_dirty"):
                draft = dict(qa.get("draft") or {})
                draft["name"] = str((qa.get("customer") or {}).get("name") or "")
                # 客户建档/改档已有 admin writer 语义(save_customer 自带 _writer_session)。
                # 嵌套在本块内:写切 raw admin writer,退出 writer 会话仍落回本块的只读闸。
                cl.save_customer(fields=draft, mode="overwrite", customer_id=customer_id)
            master_card = card_from_customer(
                cl,
                customer_id=customer_id,
                people_id=card.people_id,
            )
            # 顾问组织(detailbooksell)只有这一次单独实时读:它不在全量主档里。
            org = resolve_booking_org(cl, defaults.advisor_id, defaults)
            # 载荷吃已取得的权威快照:零额外取数,不做逐字段重复解析。
            booking = build_booking_payload(defaults, masters=masters, paints=paints, org=org)
            if delivery_be:
                # 银行身份核对也在权威只读块内完成并产出最终 payments —— 退出本块后银行目录
                # 只剩销售视图,核对必须在这里做完。
                payments = validate_company_bank_payments(
                    adapter, qa.get("payments") or [], client=cl
                )

        # 写阶段:销售会话,提交一次(表单/autonum/提交/附件/有限回读都在销售会话上)。
        if delivery_be:
            booking = dataclasses.replace(
                booking,
                delivery_date_be=delivery_be,
                regis_name=str(answers.get("regis_name") or ""),
                payments=tuple(payments),
            )
        # 账套级互斥只护「取号→提交」:同账套不同销售账号并发时别撞单号。
        # 客户写入/附件挂载/主档刷新等慢步骤不进共享锁。
        with mrerp_booking_lock(ep):
            create_options = {"on_attempt": on_attempt} if on_attempt is not None else {}
            booking_id, booking_no = cl.create_booking_via_form(
                customer_id=customer_id, booking=booking, card=master_card, **create_options
            )
        attached = 0
        failed = list(attach_failed or [])
        if attach_files:
            try:
                res = cl.attach_booking_files(booking_id=booking_id, files=attach_files)
                attached = int(res.get("attached") or 0)
                failed += list(res.get("failed") or [])
            except Exception:
                logger.warning("DMS booking exists but attachment upload failed", exc_info=True)
                failed += [{"error": "attachment upload failed"}]
        # 主档缓存用**本次提交前的权威快照**落库:不再用销售会话二次抓全量(那会把管理员
        # 完整缓存覆盖成销售裁剪视图,还多一轮远程读取)。
        masters_cache.write_authoritative_snapshot(
            ep,
            masters,
            car_id=str(((qa.get("answers") or {}).get("car") or {}).get("id") or ""),
            paints=paints,
        )
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
        province_name=str(d.get("province_name") or ""),
        district_id=str(d.get("district_id") or ""),
        district_name=str(d.get("district_name") or ""),
        subdistrict_id=str(d.get("subdistrict_id") or ""),
        subdistrict_name=str(d.get("subdistrict_name") or ""),
        zipcode_id=str(d.get("zipcode_id") or ""),
        zipcode=str(d.get("zipcode") or d.get("zipcode_name") or ""),
        building=str(d.get("building") or ""),
        floor=str(d.get("floor") or ""),
        room=str(d.get("room") or ""),
        village=str(d.get("village") or ""),
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

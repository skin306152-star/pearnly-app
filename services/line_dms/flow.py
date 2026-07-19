# -*- coding: utf-8 -*-
"""DMS LINE 对话流状态机(DL-3):拍身份证 + 输手机号 → 三分支 → 确认 → 写客户档。

确定性状态机,零自由文本理解。会话态存 dms_line_sessions(store.set/get/clear_session)。
state ∈ collecting(集料)/ reviewing(候审)。绑定用户的 image/text/postback 事件由
webhook 转进这里;未绑定与绑定码路径不经此。

时序:重活(OCR/DMS 登录/写库)一律 asyncio.to_thread 离开事件循环(铁律#10),
且 webhook 入口 spawn 后台任务 + start_loading + push 结果,不占 reply token(照
line_image_ocr 范式)。fields 键形状与网页确认页(static/dms)同一词表——身份键取自
_IDENTITY_MAP、地址键取自 _ADDR_MAP,绝不自造键名。
"""

from __future__ import annotations

import json
import logging
import secrets
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

from core import db
from services.erp import dms_id_ocr as _id_ocr
from services.erp import erp_dms_intake as _dms_intake
from services.line_binding import line_client
from services.line_dms import (
    _out,
    approval_flow,
    booking_flow,
    cards,
    draft,
    edit_flow,
    menu_cards,
    menu_flow,
    store,
)
from services.line_dms._out import _CHANNEL, _push, _reply, _thr

logger = logging.getLogger(__name__)

_RESET_WORD = "เริ่มใหม่"

# 建单/新建时写满的地址块键(与网页 dms-intake-core.js 的 ADDR_KEYS 逐键同形)。
_ADDR_BLOCK_KEYS = (
    "house_no",
    "building",
    "floor",
    "room",
    "village",
    "moo",
    "soi",
    "road",
    "province_id",
    "district_id",
    "subdistrict_id",
    "zipcode_id",
)
# 新建客户的身份字段键(与网页 create 分支 fields 同形)。
_CREATE_ID_KEYS = ("prefix_id", "name", "people_id", "tax_id", "birthday_be", "phone")

# 后台调度 + LINE 出口(_CHANNEL/_thr/_reply/_push 见 _out)· tag 供后台任务日志定位。
_spawn = _out.make_spawn("line_dms.flow")


# ── webhook 入口(thin · spawn 后台) ────────────────────────────────────────
def handle_image(binding: dict, line_user_id: str, message_id: str) -> None:
    """绑定用户发图片(collecting):后台下载 + 身份证 OCR。"""
    if message_id:
        _spawn(process_image(binding, line_user_id, message_id))


async def handle_text(binding: dict, line_user_id: str, reply_token: str, text: str) -> None:
    """绑定用户发文字:เริ่มใหม่ 重置 / 手机号 / 其余按当前态追料。"""
    tenant = binding["tenant_id"]
    if text == _RESET_WORD:  # 全局重置优先于 editing 态
        await _thr(store.clear_session, tenant, line_user_id)
        _reply(reply_token, cards.TXT_RESET)
        return

    sess = await _thr(store.get_session, tenant, line_user_id)
    if (sess or {}).get("state") == "editing":  # 逐字段修正:下一条文本 = 新值
        await edit_flow.handle_text(binding, line_user_id, reply_token, sess, text)
        return

    # 菜单层(波2):เมนู/问候语弹菜单;menu 态下单字 1/2 = 点对应菜单项(先于手机号判定)。
    if await menu_flow.handle_text(binding, line_user_id, reply_token, sess, text):
        return

    # 号码透传:ERP 是权威,它吃什么送什么,不在 Pearnly 写死格式(Zihao 拍板)。
    # 含数字即视为号码(纯路由判据,区分号码与闲聊);格式对错由 DMS 保存时裁决。
    if any(ch.isdigit() for ch in text):
        payload = await _merge_session(
            binding,
            line_user_id,
            {"phone": text},
            keep=("id_card", "endpoint_id", "mode"),
            sess=sess,
        )
        if payload.get("id_card"):
            _spawn(
                _run_dedup(
                    binding,
                    line_user_id,
                    None,
                    payload["id_card"],
                    text,
                    payload.get("endpoint_id"),
                )
            )
        else:
            _reply(reply_token, cards.TXT_ASK_CARD)
        return

    nudge = _nudge(sess)
    if nudge is None:  # 无会话 → 菜单卡引路(取代旧 TXT_INTRO 文本)
        line_client.reply_messages(reply_token, [menu_cards.menu_card()], channel=_CHANNEL)
    else:
        _reply(reply_token, nudge)


async def handle_postback(
    binding: dict, line_user_id: str, reply_token: str, postback: dict
) -> None:
    """确认按钮(postback):核对 nonce → 清 nonce(防双写)→ 分支执行。"""
    tenant = binding["tenant_id"]
    pb = {k: v[0] for k, v in parse_qs(postback.get("data") or "").items()}
    action = pb.get("action")

    # 订车阶段(DL-4a)的预览确认/取消归 booking_flow(客户档写档动作留本文件)。
    if action in booking_flow.BOOKING_ACTIONS:
        await booking_flow.handle_postback(binding, line_user_id, reply_token, action, pb)
        return

    if action == cards.ACT_RESET:
        await _thr(store.clear_session, tenant, line_user_id)
        _reply(reply_token, cards.TXT_RESET)
        return

    sess = await _thr(store.get_session, tenant, line_user_id)
    payload = (sess or {}).get("payload") or {}

    # 菜单层(波2):选菜单项 / 建档后继续订车 / 重拍。无 nonce 消费,须在下方写档守卫之前。
    if action in menu_flow.MENU_ACTIONS:
        await menu_flow.handle_postback(binding, line_user_id, reply_token, action, pb, sess)
        return

    if action in approval_flow.APPROVAL_ACTIONS:  # 波4:nonce/状态守卫都在 approval_flow 内
        await approval_flow.handle_postback(binding, line_user_id, reply_token, action, pb, sess)
        return

    # 逐字段修正(DL-6):开菜单/选字段/取消。nonce 只校验不消费,写档仍由下方 consume_nonce 守卫。
    if action in edit_flow.EDIT_ACTIONS:
        await edit_flow.handle_postback(binding, line_user_id, reply_token, action, pb, sess)
        return

    if action == cards.ACT_KEEP:
        _reply(reply_token, cards.TXT_KEEP)
        # 保留旧数据 = 零写入;customer 模式下问是否继续订车,booking/缺省照旧串联。
        await menu_flow.after_customer_saved(
            binding,
            line_user_id,
            endpoint_id=str(payload.get("endpoint_id") or ""),
            customer_id=str(payload.get("customer_id") or ""),
            draft=payload.get("draft") or {},
            mode=str(payload.get("mode") or ""),
            same_data=True,
        )
        return

    # 写动作:确认守卫(reviewing 态 + nonce 吻合)原子清 nonce 并回 payload;不符/过期 →
    # 过期话术、绝不写。清 nonce 后同一 nonce 的第二次点击此后必然 mismatch(防双击双写)。
    payload = await _thr(store.consume_nonce, tenant, line_user_id, "reviewing", pb.get("nonce"))
    if payload is None:
        _reply(reply_token, cards.TXT_EXPIRED)
        return

    if action == cards.ACT_CREATE:
        _spawn(_write_create(binding, line_user_id, payload))
    elif action == cards.ACT_UPDATE:
        _spawn(_write_update(binding, line_user_id, payload))
    elif action == cards.ACT_PICK:
        cid = pb.get("cid") or ""
        valid = {str(c.get("customer_id")) for c in (payload.get("candidates") or [])}
        if cid not in valid:
            _reply(reply_token, cards.TXT_EXPIRED)
            return
        # 相似认领 = 无 diff 的 overwrite,认领到所选 customer_id;走 _write_update 特例(S9)。
        _spawn(_write_update(binding, line_user_id, {**payload, "customer_id": cid}))
    else:
        _reply(reply_token, cards.TXT_EXPIRED)


# ── collecting:OCR ─────────────────────────────────────────────────────────
async def process_image(binding: dict, line_user_id: str, message_id: str) -> None:
    """下载 + 身份证 OCR(计费走真实用户行)。成功存 id_card;齐料自动查重。"""
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    await _thr(line_client.start_loading, line_user_id, 30, channel=_CHANNEL)

    user = await _thr(db.find_user_by_id, user_id)
    if not user:
        _push(line_user_id, cards.TXT_NO_ENDPOINT)
        return
    content = await _thr(line_client.download_message_content, message_id, channel=_CHANNEL)
    if not content:
        _push(line_user_id, cards.TXT_BLURRY)
        return

    try:
        ep, ocr, _ = await _thr(
            _id_ocr.recognize_id_card, user, content, f"line_{message_id}.jpg", "", None
        )
    except _id_ocr.DmsOcrError as e:
        _push(line_user_id, _ocr_error_text(e))
        return

    if ocr.get("needs_review"):
        # 读不清 / 校验位对不上 → 打回重拍,列缺失项;不查重(C6)。
        _push(line_user_id, _blurry_text(ocr.get("missing_fields") or []))
        return

    id_card = _id_ocr.editable_id_card(ocr["id_card"])
    payload = await _merge_session(
        binding,
        line_user_id,
        {"id_card": id_card, "endpoint_id": str(ep.get("id") or "")},
        keep=("phone", "mode"),
    )
    if payload.get("phone"):
        await _run_dedup(
            binding, line_user_id, ep, id_card, payload["phone"], str(ep.get("id") or "")
        )
    else:
        _push(line_user_id, cards.TXT_ASK_PHONE)


# ── collecting → reviewing:查重四分支 ──────────────────────────────────────
async def _run_dedup(
    binding: dict,
    line_user_id: str,
    ep: Optional[dict],
    id_card: dict,
    phone: str,
    endpoint_id: Optional[str],
) -> None:
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    await _thr(line_client.start_loading, line_user_id, 30, channel=_CHANNEL)
    # 菜单层(波2)的 mode 决定写档后是否自动串联订车;缺省=老直拍行为不变。会话是权威源
    # (采集路径都先写会话再进这里),避免多签名穿参。
    _sess = await _thr(store.get_session, tenant, line_user_id)
    mode = str(((_sess or {}).get("payload") or {}).get("mode") or "")
    if ep is None:
        ep = await _thr(_id_ocr.resolve_dms_endpoint, user_id, endpoint_id)
    if not ep:
        _push(line_user_id, cards.TXT_NO_ENDPOINT)
        return

    # 台账候选:DMS 搜索有「新客隐身期」,刚推过的同尾号客户按号直读核对(intake 侧)。
    tail = str(id_card.get("people_id") or "")[-4:]
    cands = await _thr(_id_ocr.recent_dms_customer_ids_by_tail, tenant, tail)
    res = await _thr(
        _dms_intake.recognize_lookup_mrerp_dms,
        ep,
        people_id=id_card.get("people_id", ""),
        name=id_card.get("name") or "",
        ocr_address=id_card.get("address") or {},
        phone=phone,
        fallback_customer_ids=cands,
    )
    if not res.get("ok"):
        fr = res.get("error_friendly") or {}
        _push(line_user_id, fr.get("th") or cards.TXT_LOOKUP_FAIL)
        return

    scenario = res.get("scenario")
    field_diffs = res.get("field_diffs") or []
    geo = res.get("geo") or {}
    draft_vals = draft.build_draft(id_card, geo, res.get("prefixes") or [], phone)
    summary = draft.build_summary(draft_vals, geo)

    nonce = secrets.token_hex(8)
    base = {
        "draft": draft_vals,
        "summary": summary,
        "endpoint_id": str(ep.get("id") or ""),
        "nonce": nonce,
        "field_diffs": [],  # 默认无差异;exact_diff 分支覆写为真实 diffs。
        # 逐字段修正(DL-6)按此重跑查重:留原始 id_card/phone 作重放源,改值后回灌此路。
        "id_card": id_card,
        "phone": phone,
        "mode": mode,  # 写档后分叉(菜单层波2)靠它;编辑重跑经会话回读得以保留。
    }

    if scenario == "none":
        payload = {**base, "scenario": "none"}
        card = cards.new_customer_card(summary, nonce)
    elif scenario == "exact" and mode != "customer":
        # 订车工作流(泰方拍板:与档案维护是 DMS 两个功能,证件只为认人):认出已有
        # 客户即确认卡直奔选车,不弹差异不问更新;档案维护走菜单1。
        payload = {**base, "scenario": "exact_diff", "customer_id": res["match"]["customer_id"]}
        card = cards.booking_customer_card(summary, nonce)
    elif scenario == "exact":
        has_admin = draft.has_admin_creds(ep)
        display = draft.display_diffs(field_diffs, geo)
        # 审批策略见 approval_flow.APPROVAL_POLICY;无差异 → 同资料预览卡(收到证+电话
        # 一律先确认)。按「保持/继续」后 ACT_KEEP 按 mode 分流。
        args = (tenant, user_id, display, has_admin, nonce, summary)
        card, approval = await _thr(approval_flow.exact_diff_card, *args)
        payload = {
            **base,
            "scenario": "exact_diff",
            "customer_id": res["match"]["customer_id"],
            "field_diffs": field_diffs,
            "has_admin": has_admin,
            "approval": approval,
            "display_diffs": display,
        }
    else:  # similar
        cands = [
            {
                "customer_id": str(c.get("customer_id") or ""),
                "cuscode": c.get("cuscode", ""),
                "name": c.get("name", ""),
                "people_id": c.get("people_id", ""),
            }
            for c in (res.get("candidates") or [])
        ]
        payload = {**base, "scenario": "similar", "candidates": cands}
        card = cards.candidates_card(cands, nonce)

    await _thr(store.set_session, tenant, line_user_id, "reviewing", payload)
    _push_card(line_user_id, card)


# ── reviewing → 执行写档 ────────────────────────────────────────────────────
async def _write_create(binding: dict, line_user_id: str, payload: dict) -> None:
    d = payload.get("draft") or {}
    fields = {k: d.get(k, "") for k in _CREATE_ID_KEYS}
    block = {k: d.get(k, "") for k in _ADDR_BLOCK_KEYS}
    addresses = {"": dict(block), "_ct": dict(block), "_sd": dict(block)}
    await _execute(
        binding,
        line_user_id,
        payload,
        mode="create",
        customer_id=None,
        fields=fields,
        addresses=addresses,
        field_diffs=[],
    )


async def _write_update(binding: dict, line_user_id: str, payload: dict) -> None:
    d = payload.get("draft") or {}
    field_diffs = payload.get("field_diffs") or []
    # 只写变了的字段 + people_id/name 必填项;未变字段不进 fields → 保留 DMS 现值。
    # 相似认领(S9)= 空 field_diffs + payload.customer_id 指向所选候选,天然落回本路径。
    fields = {"people_id": d.get("people_id", ""), "name": d.get("name", "")}
    for diff in field_diffs:
        fields[diff["field"]] = diff.get("new", "")
    await _execute(
        binding,
        line_user_id,
        payload,
        mode="overwrite",
        customer_id=payload.get("customer_id"),
        fields=fields,
        addresses=None,
        field_diffs=field_diffs,
    )


async def _execute(
    binding: dict,
    line_user_id: str,
    payload: dict,
    *,
    mode: str,
    customer_id: Optional[str],
    fields: Dict[str, Any],
    addresses: Optional[Dict[str, Dict[str, Any]]],
    field_diffs: List[dict],
) -> None:
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    name = str(fields.get("name") or "")
    people_id = str(fields.get("people_id") or "")
    await _thr(line_client.start_loading, line_user_id, 30, channel=_CHANNEL)

    ep = await _thr(_id_ocr.resolve_dms_endpoint, user_id, payload.get("endpoint_id"))
    if not ep:
        _push(line_user_id, cards.TXT_NO_ENDPOINT)
        return

    result = await _thr(
        _dms_intake.push_idcard_fields_mrerp_dms,
        ep,
        fields=fields,
        mode=mode,
        customer_id=customer_id,
        addresses=addresses,
    )
    success = bool(result.get("success"))
    # 记录页按 adapter 显示 · LINE 推的也要出现:push_type(trigger 位)保持 'id_card',
    # request_body.trigger='line_dms' 标源、带 field_diffs 快照(与网页 /push 同一台账)。
    request_body = {
        "adapter": "mrerp_dms",
        "trigger": "line_dms",
        "mode": mode,
        "people_id_tail": people_id[-4:],
        "field_diffs": field_diffs,
    }
    await _thr(
        db.insert_push_log,
        user_id,
        str(ep["id"]),
        None,
        result.get("customer_id") or "",
        name,
        None,
        "success" if success else "failed",
        200 if success else 0,
        request_body,
        json.dumps(result.get("response_body") or {}, ensure_ascii=False),
        result.get("error_code"),
        1,
        result.get("elapsed_ms", 0),
        "id_card",
    )

    if success:
        mode = result.get("mode") or mode  # create 被幂等/撞码转更新时回执如实说 อัปเดต
        _push(line_user_id, cards.receipt_text(result.get("customer_id") or "", name, mode))
        await menu_flow.after_customer_saved(
            binding,
            line_user_id,
            endpoint_id=str(payload.get("endpoint_id") or ""),
            customer_id=str(result.get("customer_id") or ""),
            draft=payload.get("draft") or {},
            name=name,
            mode=str(payload.get("mode") or ""),
        )
    elif result.get("error_code") == "ERR_DMS_ADMIN_AUTH":
        _push(line_user_id, cards.TXT_ADMIN_AUTH_FAIL)  # 不谎称已自动通知
    else:
        fr = result.get("error_friendly") or {}
        _push(line_user_id, fr.get("th") or cards.TXT_SAVE_FAIL)


# ── 会话/文案小工具 ─────────────────────────────────────────────────────────
async def _merge_session(
    binding: dict, line_user_id: str, add: dict, keep: tuple, sess: Optional[dict] = None
) -> dict:
    """并入新料到 collecting 会话:只保留 keep 的旧键(丢弃 reviewing 残留 nonce/diffs)。
    调用方已读过会话可经 sess 传入,免二次读。"""
    tenant = binding["tenant_id"]
    if sess is None:
        sess = await _thr(store.get_session, tenant, line_user_id)
    old = (sess or {}).get("payload") or {}
    payload = {k: old.get(k) for k in keep if old.get(k)}
    payload.update(add)
    await _thr(store.set_session, tenant, line_user_id, "collecting", payload)
    return payload


def _nudge(sess: Optional[dict]) -> Optional[str]:
    if not sess:
        return None  # 无会话 → 调用方弹 menu_card 引路(取代旧 TXT_INTRO 文本)
    if sess.get("state") == "reviewing":
        return cards.TXT_PICK_ABOVE
    payload = sess.get("payload") or {}
    if payload.get("id_card") and not payload.get("phone"):
        return cards.TXT_ASK_PHONE
    if payload.get("phone") and not payload.get("id_card"):
        return cards.TXT_ASK_CARD
    return cards.TXT_NEED_BOTH


def _blurry_text(missing: List[str]) -> str:
    labels = [cards.FIELD_LABELS_TH.get(m) for m in missing if cards.FIELD_LABELS_TH.get(m)]
    if not labels:
        return cards.TXT_BLURRY
    return cards.TXT_BLURRY + " (" + ", ".join(labels) + ")"


def _ocr_error_text(e: _id_ocr.DmsOcrError) -> str:
    """按真实原因回话(状态诚实):余额/配置/系统错各说各的,只有真读不清才叫重拍。
    实案:฿0 余额的 402 曾被统一说成「拍不清」,清晰卡也被打回,误导排障。"""
    if e.code == "dms.no_endpoint":
        return cards.TXT_NO_ENDPOINT
    if e.code == "insufficient_balance":
        return cards.TXT_NO_CREDIT
    if e.code in ("ocr.id_card_unreadable", "ocr.empty_file", "ocr.file_too_large"):
        return cards.TXT_BLURRY
    return cards.TXT_SYSTEM_ERROR


# ── LINE 出口(全走 dms channel · _reply/_push 见 _out) ──────────────────────
def _push_card(line_user_id: str, card: dict) -> None:
    line_client.push_messages(line_user_id, [card], channel=_CHANNEL)

# -*- coding: utf-8 -*-
"""DMS 改写审批编排(波4):销售提审 → 选审批人 → 管理员 LINE 批/拒 → 执行 → 双向通知。

角色判据=花名册档案 dms_role(sales 提审;admin 可批);无档案的绑定者(老板/存量)不走
本层——flow 按旧路径直写。执行永远用**批准人自己的 endpoint 凭据**(DMS 审计显示真实
批准人),申请里只存快照(draft/diffs),不依赖销售会话存活。

一次性语义:提审由会话 nonce 消费守卫(防双提);批/拒由 approval_store.claim 的原子
状态迁移守卫(first-wins,双管理员同点只有一人执行)。执行失败回炉 pending 可重试,
绝不谎报「已更新」。
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from core import db
from services.dms_roster import store as roster_store
from services.erp import dms_id_ocr as _id_ocr
from services.erp import erp_dms_intake as _dms_intake
from services.line_binding import line_client
from services.line_dms import _out, approval_cards, approval_store, cards, store
from services.line_dms._out import _CHANNEL, _push, _reply, _thr

logger = logging.getLogger(__name__)

APPROVAL_ACTIONS = frozenset(
    {
        cards.ACT_SUBMIT_APPROVAL,
        cards.ACT_APPROVAL_TARGET,
        cards.ACT_APPROVAL_APPROVE,
        cards.ACT_APPROVAL_REJECT,
        cards.ACT_APPROVAL_RETARGET,
    }
)

_spawn = _out.make_spawn("line_dms.approval")


async def handle_postback(
    binding: dict, line_user_id: str, reply_token: str, action: str, pb: dict, sess: Optional[dict]
) -> None:
    if action == cards.ACT_SUBMIT_APPROVAL:
        await _submit(binding, line_user_id, reply_token, pb)
    elif action == cards.ACT_APPROVAL_TARGET:
        await _target(binding, line_user_id, reply_token, pb)
    elif action == cards.ACT_APPROVAL_RETARGET:
        await _retarget(binding, line_user_id, reply_token, pb)
    else:  # approve / reject
        await _decide(
            binding, line_user_id, reply_token, pb, approve=(action == cards.ACT_APPROVAL_APPROVE)
        )


def exact_diff_card(tenant_id: str, user_id: str, display: list, has_admin: bool, nonce: str):
    """flow 的 exact_diff 分支按花名册角色出卡:sales→提审卡;admin→直写键(自己的 DMS
    凭据本就有改权);无档案(老板/存量)→ 旧 has_admin 逻辑。返回 (card, approval标志)。"""
    prof = roster_store.get_profile(tenant_id, str(user_id))
    role = (prof or {}).get("dms_role") or ""
    if role == "sales":
        return cards.diff_card(display, has_admin, nonce, approval=True), True
    return cards.diff_card(display, has_admin or role == "admin", nonce), False


# ── 审批人名录 ──────────────────────────────────────────────────────────────
def _bound_approvers(tenant_id: str) -> List[Dict[str, str]]:
    """本租户可收审批卡的管理员:dms_role='admin' + 启用 + 已绑 LINE。"""
    out = []
    for p in roster_store.list_profiles(tenant_id):
        if (p.get("dms_role") or "") != "admin" or (p.get("status") or "active") != "active":
            continue
        b = store.get_binding_by_user(str(p["user_id"]))
        if not b:
            continue
        out.append(
            {
                "user_id": str(p["user_id"]),
                "display_name": p.get("display_name") or "",
                "line_user_id": b.get("line_user_id") or "",
            }
        )
    return out


def _approver_eligible(tenant_id: str, user_id: str) -> bool:
    """能批=admin 档案(启用),或无档案的租户 owner(老板本人绑了 LINE 也能批)。"""
    prof = roster_store.get_profile(tenant_id, user_id)
    if prof:
        return (prof.get("dms_role") or "") == "admin" and (
            prof.get("status") or "active"
        ) == "active"
    user = db.find_user_by_id(str(user_id))
    return bool(user and (user.get("role") or "") == "owner")


# ── 销售侧:提审 / 选人 / 改派 ──────────────────────────────────────────────
async def _submit(binding: dict, line_user_id: str, reply_token: str, pb: dict) -> None:
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    payload = await _thr(store.consume_nonce, tenant, line_user_id, "reviewing", pb.get("nonce"))
    if payload is None or payload.get("scenario") != "exact_diff" or not payload.get("approval"):
        _reply(reply_token, cards.TXT_EXPIRED)
        return

    approvers = await _thr(_bound_approvers, tenant)
    if not approvers:
        _reply(reply_token, approval_cards.TXT_NO_APPROVERS)
        return

    d = payload.get("draft") or {}
    req_id = await _thr(
        approval_store.create_request,
        tenant,
        str(user_id),
        endpoint_id=str(payload.get("endpoint_id") or ""),
        customer_id=str(payload.get("customer_id") or ""),
        customer_name=str(d.get("name") or ""),
        field_diffs=payload.get("field_diffs") or [],
        draft={"fields": d, "display_diffs": payload.get("display_diffs") or []},
    )
    if not req_id:
        _reply(reply_token, cards.TXT_SYSTEM_ERROR)
        return
    await _thr(store.clear_session, tenant, line_user_id)
    line_client.reply_messages(
        reply_token, [approval_cards.picker_card(req_id, approvers)], channel=_CHANNEL
    )


async def _own_pending_request(binding: dict, pb: dict) -> Optional[dict]:
    """销售侧动作的共同守卫:req 属本租户、发起人是自己、仍 pending(过期惰性落库)。"""
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    req = await _thr(approval_store.get_request, tenant, str(pb.get("req") or ""))
    if not req or str(req.get("operator_user_id")) != str(user_id):
        return None
    return req


async def _target(binding: dict, line_user_id: str, reply_token: str, pb: dict) -> None:
    req = await _own_pending_request(binding, pb)
    if not req:
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    if req.get("status") != "pending":
        _reply(reply_token, _status_text_for_sales(req))
        return

    tenant = binding["tenant_id"]
    approvers = await _thr(_bound_approvers, tenant)
    aid = str(pb.get("aid") or "all")
    if aid == "all":
        targets, label = approvers, None
    else:
        targets = [a for a in approvers if a["user_id"] == aid]
        label = targets[0]["display_name"] if targets else None
    if not targets:  # 选中的人已停用/解绑,或全员已解绑 → 让销售重选/找老板
        _reply(reply_token, approval_cards.TXT_NO_APPROVERS)
        return

    ok = await _thr(
        approval_store.set_target, tenant, str(req["id"]), None if aid == "all" else aid
    )
    if not ok:
        _reply(reply_token, cards.TXT_EXPIRED)
        return

    operator_name = await _thr(_operator_display_name, tenant, str(req["operator_user_id"]))
    card = approval_cards.request_card(
        str(req["id"]),
        operator_name,
        req.get("customer_name") or "",
        str(req.get("customer_id") or ""),
        _display_diffs(req),
    )
    for t in targets:
        line_client.push_messages(t["line_user_id"], [card], channel=_CHANNEL)
    line_client.reply_messages(
        reply_token, [approval_cards.waiting_card(str(req["id"]), label)], channel=_CHANNEL
    )


async def _retarget(binding: dict, line_user_id: str, reply_token: str, pb: dict) -> None:
    req = await _own_pending_request(binding, pb)
    if not req:
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    if req.get("status") != "pending":
        _reply(reply_token, _status_text_for_sales(req))
        return
    approvers = await _thr(_bound_approvers, binding["tenant_id"])
    if not approvers:
        _reply(reply_token, approval_cards.TXT_NO_APPROVERS)
        return
    line_client.reply_messages(
        reply_token, [approval_cards.picker_card(str(req["id"]), approvers)], channel=_CHANNEL
    )


# ── 管理员侧:批 / 拒 ───────────────────────────────────────────────────────
async def _decide(
    binding: dict, line_user_id: str, reply_token: str, pb: dict, *, approve: bool
) -> None:
    tenant, user_id = binding["tenant_id"], binding["user_id"]
    if not await _thr(_approver_eligible, tenant, str(user_id)):
        _reply(reply_token, approval_cards.TXT_NOT_APPROVER)
        return

    req = await _thr(approval_store.claim, tenant, str(pb.get("req") or ""), str(user_id))
    if not req:
        cur = await _thr(approval_store.get_request, tenant, str(pb.get("req") or ""))
        if cur and cur.get("status") == "expired":
            _reply(reply_token, approval_cards.TXT_REQ_EXPIRED)
        else:
            _reply(reply_token, approval_cards.TXT_REQ_STALE)
        return

    if not approve:
        await _thr(approval_store.finish, tenant, str(req["id"]), "rejected")
        _reply(reply_token, approval_cards.TXT_REQ_REJECTED_ADMIN)
        await _notify_operator(tenant, req, approval_cards.TXT_REQ_REJECTED_SALES)
        return

    _reply(reply_token, approval_cards.TXT_PROCESSING)
    _spawn(_execute_approved(binding, line_user_id, req))


async def _execute_approved(binding: dict, admin_line_user_id: str, req: dict) -> None:
    """以批准人自己的 endpoint 凭据执行 overwrite;成功 approved,失败回炉 pending。"""
    tenant, approver_id = binding["tenant_id"], str(binding["user_id"])
    await _thr(line_client.start_loading, admin_line_user_id, 30, channel=_CHANNEL)

    ep = await _thr(_id_ocr.resolve_dms_endpoint, approver_id, None)
    if not ep:
        await _thr(approval_store.finish, tenant, str(req["id"]), "pending")
        _push(admin_line_user_id, approval_cards.TXT_APPROVER_NO_ENDPOINT)
        return

    draft_wrap = req.get("draft") or {}
    d = draft_wrap.get("fields") or {}
    diffs = req.get("field_diffs") or []
    fields = {"people_id": d.get("people_id", ""), "name": d.get("name", "")}
    for diff in diffs:
        fields[diff.get("field")] = diff.get("new", "")

    result = await _thr(
        _dms_intake.push_idcard_fields_mrerp_dms,
        ep,
        fields=fields,
        mode="overwrite",
        customer_id=str(req.get("customer_id") or ""),
        addresses=None,
    )
    success = bool(result.get("success"))
    request_body = {
        "adapter": "mrerp_dms",
        "trigger": "line_dms_approval",
        "mode": "overwrite",
        "field_diffs": diffs,
        "request_id": str(req["id"]),
        "operator_user_id": str(req.get("operator_user_id") or ""),
    }
    await _thr(
        db.insert_push_log,
        approver_id,
        str(ep["id"]),
        None,
        result.get("customer_id") or str(req.get("customer_id") or ""),
        req.get("customer_name") or "",
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
        await _thr(approval_store.finish, tenant, str(req["id"]), "approved")
        _push(admin_line_user_id, approval_cards.TXT_REQ_APPROVED_ADMIN)
        await _notify_operator(tenant, req, approval_cards.TXT_REQ_APPROVED_SALES)
    else:
        await _thr(approval_store.finish, tenant, str(req["id"]), "pending")
        fr = result.get("error_friendly") or {}
        _push(
            admin_line_user_id,
            (fr.get("th") + "\n" if fr.get("th") else "") + approval_cards.TXT_EXEC_FAIL_ADMIN,
        )


# ── 小工具 ─────────────────────────────────────────────────────────────────
def _status_text_for_sales(req: dict) -> str:
    """销售侧看到的非 pending 申请状态话术(等待卡/选人卡点晚了)。"""
    st = req.get("status")
    if st == "expired":
        return approval_cards.TXT_REQ_EXPIRED
    if st == "approved":
        return approval_cards.TXT_REQ_APPROVED_SALES
    if st == "rejected":
        return approval_cards.TXT_REQ_REJECTED_SALES
    return approval_cards.TXT_REQ_STALE


def _display_diffs(req: dict) -> List[Dict[str, str]]:
    wrap = req.get("draft") or {}
    shown = wrap.get("display_diffs") or []
    if shown:
        return shown
    # 快照缺展示层(异常旧数据)→ 用原始 diffs 兜底,label 走字段中文表。
    return [
        {
            "label": cards.FIELD_LABELS_TH.get(d.get("field"), d.get("field", "")),
            "old": str(d.get("old") or ""),
            "new": str(d.get("new") or ""),
        }
        for d in (req.get("field_diffs") or [])
    ]


def _operator_display_name(tenant_id: str, user_id: str) -> str:
    prof = roster_store.get_profile(tenant_id, user_id)
    return (prof or {}).get("display_name") or "พนักงานขาย"


async def _notify_operator(tenant_id: str, req: dict, text: str) -> None:
    b = await _thr(store.get_binding_by_user, str(req.get("operator_user_id") or ""))
    if b and b.get("line_user_id"):
        _push(b["line_user_id"], text)

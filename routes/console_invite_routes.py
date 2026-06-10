# -*- coding: utf-8 -*-
"""控制台 · 邀请 + 所有权转移 API(批3 · docs/permissions/03)。

POST /api/team/invitations            建邀请(email|line · 角色禁 owner · token 只回一次)
GET  /api/team/invitations            pending 列表
DELETE /api/team/invitations/{id}     撤回
GET  /api/invitations/{token}/preview 公开:接受页渲染数据(租户名/角色/状态)
POST /api/invitations/{token}/accept  公开:新号注册入组(既有号人话拒绝)
POST /api/ownership/transfer          发起转移(目标须 admin · 24h token)
POST /api/ownership/transfer/accept   接收方确认(同事务换角色 · 不可逆)

LINE 通道复用改密链路的发消息能力:目标已绑机器人则推送,未绑则由老板复制链接转发
(invite_url 两种通道都返回,行业标准 copy-link)。
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.route_helpers import _check_password_strength, _log_op
from services.authz.deps import require_perm
from services.authz.registry import ASSIGNABLE_ROLE_KEYS
from services.team import invitations as inv_store
from services.team import ownership as ownership_store

logger = logging.getLogger("mr-pilot")
router = APIRouter()

ROLE_NAMES = {"admin": "Admin", "accountant": "Accountant", "clerk": "Clerk", "viewer": "Viewer"}


class InvitationCreate(BaseModel):
    channel: str = Field(..., pattern="^(email|line)$")
    target: str = Field(..., min_length=1, max_length=200)
    role_key: str = Field(..., min_length=3, max_length=20)
    scope_mode: str = Field("all", pattern="^(all|assigned)$")
    workspace_ids: List[int] = []


class InvitationAccept(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[str] = Field(None, max_length=200)


class TransferCreate(BaseModel):
    target_user_id: str


class TransferAccept(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


def _invite_url(request: Request, token: str) -> str:
    host = request.headers.get("host", "pearnly.com")
    scheme = "http" if "localhost" in host or "127.0.0.1" in host else "https"
    return f"{scheme}://{host}/invite/{token}"


@router.post("/api/team/invitations")
async def create_invitation(req: InvitationCreate, request: Request):
    user = require_perm(request, "team.member.invite")
    if req.role_key not in ASSIGNABLE_ROLE_KEYS:
        raise HTTPException(422, detail="invite.role_not_allowed")
    if req.scope_mode == "assigned" and not req.workspace_ids:
        raise HTTPException(422, detail="team.scope_empty")
    if req.channel == "email" and "@" not in req.target:
        raise HTTPException(422, detail="invite.bad_email")
    created = inv_store.create_invitation(
        tenant_id=str(user["tenant_id"]),
        invited_by=str(user["id"]),
        channel=req.channel,
        target=req.target.strip(),
        role_key=req.role_key,
        scope_mode=req.scope_mode,
        workspace_ids=req.workspace_ids,
    )
    if not created:
        raise HTTPException(422, detail="invite.role_not_allowed")
    url = _invite_url(request, created["token"])
    sent = False
    if req.channel == "email":
        sent = inv_store.send_invite_email(
            req.target.strip(),
            url,
            user.get("company_name") or "Pearnly",
            ROLE_NAMES.get(req.role_key, req.role_key),
        )
    _log_op(
        request,
        user,
        "team.invite",
        "invitation",
        created["id"],
        req.target,
        {"role_key": req.role_key, "channel": req.channel, "scope_mode": req.scope_mode},
    )
    return {
        "ok": True,
        "id": created["id"],
        "invite_url": url,
        "email_sent": sent,
        "expires_at": created["expires_at"],
    }


@router.get("/api/team/invitations")
async def list_invitations(request: Request):
    user = require_perm(request, "team.member.view")
    return {"ok": True, "invitations": inv_store.list_pending(str(user["tenant_id"]))}


@router.delete("/api/team/invitations/{invitation_id}")
async def revoke_invitation(invitation_id: str, request: Request):
    user = require_perm(request, "team.member.invite")
    if not inv_store.revoke(str(user["tenant_id"]), invitation_id):
        raise HTTPException(404, detail="invite.not_found")
    _log_op(request, user, "team.invite_revoke", "invitation", invitation_id, None, {})
    return {"ok": True}


@router.get("/api/invitations/{token}/preview")
async def preview_invitation(token: str):
    """公开:接受页渲染。无效 token 与过期同形(防探测)。"""
    inv = inv_store.find_by_token(token)
    if inv is None:
        return {"ok": True, "status": "invalid"}
    return {
        "ok": True,
        "status": inv["status"],
        "tenant_name": inv.get("tenant_name"),
        "role_key": inv["role_key"],
        "email": inv.get("email"),
    }


@router.post("/api/invitations/{token}/accept")
async def accept_invitation(token: str, req: InvitationAccept, request: Request):
    """公开:新号注册入组。已有账号(1 人 1 租户)→ 人话拒绝换新邮箱注册。"""
    pw_err = _check_password_strength(req.password)
    if pw_err:
        raise HTTPException(400, detail=pw_err)
    result = inv_store.accept(
        token, username=req.username.strip(), password=req.password, email=req.email
    )
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    try:
        from core import db as _db

        _db.insert_operation_log(
            tenant_id=result["tenant_id"],
            actor_user_id=result["user_id"],
            actor_username=req.username,
            actor_is_super=False,
            action="team.member_join",
            target_type="user",
            target_id=result["user_id"],
            target_name=req.username,
            details={"role_key": result["role_key"]},
        )
    except Exception as e:
        logger.warning(f"member_join audit skip: {e}")
    return {"ok": True}


@router.post("/api/ownership/transfer")
async def initiate_transfer(req: TransferCreate, request: Request):
    user = require_perm(request, "ownership.transfer")
    result = ownership_store.initiate(
        tenant_id=str(user["tenant_id"]),
        from_user_id=str(user["id"]),
        to_user_id=req.target_user_id,
    )
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    _log_op(
        request,
        user,
        "ownership.transfer_init",
        "user",
        req.target_user_id,
        result.get("to_username"),
        {"expires_at": result["expires_at"]},
    )
    return {
        "ok": True,
        "token": result["token"],
        "to_username": result.get("to_username"),
        "expires_at": result["expires_at"],
    }


@router.post("/api/ownership/transfer/accept")
async def accept_transfer(req: TransferAccept, request: Request):
    """接收方确认。须以接收方身份登录;成功即不可逆。"""
    from core.auth import get_current_user_from_request

    user = get_current_user_from_request(request)
    result = ownership_store.accept(token=req.token, acting_user_id=str(user["id"]))
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    _log_op(
        request,
        user,
        "ownership.transfer",
        "user",
        str(user["id"]),
        user.get("username"),
        {"from_user_id": result["from_user_id"]},
    )
    return {"ok": True}

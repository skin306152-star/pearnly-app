# -*- coding: utf-8 -*-
"""控制台 · 成员管理 API(批3 · docs/permissions/03 接口契约)。

GET  /api/me/permissions                 前端 can() 协议(角色/码集/作用域)
GET  /api/team/members                   全角色成员列表
PUT  /api/team/members/{uid}/role        改角色(不可设 owner · 不可改自己)
PUT  /api/team/members/{uid}/scope       配作用域(scope_mode + 套账全量替换)
PATCH /api/team/members/{uid}/active     启停(全角色版 · 边界同上)
DELETE /api/team/members/{uid}           移除(级联清理同 legacy)
GET  /api/team/roles                     角色说明卡数据
GET  /api/team/security-events           安全日志(team./role./scope./ownership.)

安全事件全部落 operation_logs 一等 action(Stripe Security history 形态)。
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.route_helpers import _log_op
from services.authz.deps import get_authz, require_perm
from services.authz.registry import ASSIGNABLE_ROLE_KEYS, ROLE_PERMISSIONS, SCOPABLE_ROLE_KEYS
from services.team import console_store

router = APIRouter()

SECURITY_ACTION_PREFIXES = ("team.", "role.", "scope.", "ownership.", "employee.", "member.")


class RoleChangeRequest(BaseModel):
    role_key: str = Field(..., min_length=3, max_length=20)


class ScopeRequest(BaseModel):
    scope_mode: str = Field(..., pattern="^(all|assigned)$")
    workspace_ids: List[int] = []


class ActiveRequest(BaseModel):
    is_active: bool


@router.get("/api/me/permissions")
async def my_permissions(request: Request):
    """前端显隐协议:角色 + 生效码集 + 作用域。超管返 ["*"]。"""
    from core.auth import get_current_user_from_request

    user = get_current_user_from_request(request)
    if user.get("is_super_admin"):
        return {
            "ok": True,
            "data": {
                "role_key": "super_admin",
                "scope_mode": "all",
                "permissions": ["*"],
                "workspace_ids": None,
            },
        }
    authz = get_authz(request, user)
    return {
        "ok": True,
        "data": {
            "role_key": authz.role_key,
            "scope_mode": authz.scope_mode,
            "permissions": sorted(authz.permissions),
            "workspace_ids": (
                sorted(authz.workspace_ids) if authz.workspace_ids is not None else None
            ),
        },
    }


@router.get("/api/team/members")
async def team_members(request: Request):
    user = require_perm(request, "team.member.view")
    members = console_store.list_members(str(user["tenant_id"]))
    me = str(user["id"])
    for m in members:
        m["is_self"] = m["id"] == me
    # 席位计量(PEAK 吸收 · 套餐 seats_max,前端显「当前用户 N/M」+ 满员升级提示)
    from services.auth.signup_core import PLAN_CONFIG

    plan = PLAN_CONFIG.get(str(user.get("plan") or ""), PLAN_CONFIG["credits"])
    return {
        "ok": True,
        "members": members,
        "total": len(members),
        "seats_max": int(plan["seats_max"]),
    }


@router.get("/api/team/roles")
async def team_roles(request: Request):
    """角色说明卡(permission-role review):key + 权限分组摘要 + 在用人数。owner 不可邀。"""
    user = require_perm(request, "team.member.view")
    counts = console_store.role_member_counts(str(user["tenant_id"]))
    roles = []
    for key in ("owner",) + ASSIGNABLE_ROLE_KEYS:
        codes = sorted(ROLE_PERMISSIONS[key])
        roles.append(
            {
                "key": key,
                "assignable": key in ASSIGNABLE_ROLE_KEYS,
                "scopable": key in SCOPABLE_ROLE_KEYS,
                "permission_groups": sorted({c.split(".", 1)[0] for c in codes}),
                "permission_count": len(codes),
                "member_count": counts.get(key, 0),
            }
        )
    return {"ok": True, "roles": roles}


@router.put("/api/team/members/{uid}/role")
async def change_member_role(uid: str, req: RoleChangeRequest, request: Request):
    user = require_perm(request, "team.member.edit_role")
    if req.role_key == "owner":
        raise HTTPException(422, detail="team.owner_only_via_transfer")
    result = console_store.change_role(
        tenant_id=str(user["tenant_id"]),
        actor_id=str(user["id"]),
        target_user_id=uid,
        role_key=req.role_key,
    )
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    _log_op(
        request,
        user,
        "role.change",
        "user",
        uid,
        result.get("username"),
        {"role_from": result.get("role_from"), "role_to": req.role_key},
    )
    return {"ok": True, "role_key": req.role_key}


@router.put("/api/team/members/{uid}/scope")
async def change_member_scope(uid: str, req: ScopeRequest, request: Request):
    user = require_perm(request, "team.member.scope")
    result = console_store.set_scope(
        tenant_id=str(user["tenant_id"]),
        actor_id=str(user["id"]),
        target_user_id=uid,
        scope_mode=req.scope_mode,
        workspace_ids=req.workspace_ids,
    )
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    _log_op(
        request,
        user,
        "scope.change",
        "user",
        uid,
        result.get("username"),
        {
            "scope_mode": req.scope_mode,
            "ws_added": result.get("added"),
            "ws_removed": result.get("removed"),
        },
    )
    return {"ok": True}


@router.patch("/api/team/members/{uid}/active")
async def toggle_member(uid: str, req: ActiveRequest, request: Request):
    user = require_perm(request, "team.member.toggle")
    err = console_store.guard_member_action(str(user["tenant_id"]), str(user["id"]), uid)
    if err:
        raise HTTPException(422, detail=err)
    target = db.find_user_by_id(uid)
    ok = console_store.toggle_employee_active(str(user["tenant_id"]), uid, req.is_active)
    if not ok:
        raise HTTPException(404, detail="team.member_not_found")
    _log_op(
        request,
        user,
        "member.toggle",
        "user",
        uid,
        target.get("username") if target else None,
        {"is_active": req.is_active},
    )
    return {"ok": True}


@router.delete("/api/team/members/{uid}")
async def remove_member(uid: str, request: Request):
    user = require_perm(request, "team.member.remove")
    err = console_store.guard_member_action(str(user["tenant_id"]), str(user["id"]), uid)
    if err:
        raise HTTPException(422, detail=err)
    target = db.find_user_by_id(uid)
    ok = console_store.remove_employee(str(user["tenant_id"]), uid)
    if not ok:
        raise HTTPException(404, detail="team.member_not_found")
    _log_op(
        request,
        user,
        "member.remove",
        "user",
        uid,
        target.get("username") if target else None,
        {},
    )
    return {"ok": True}


@router.get("/api/team/security-events")
async def security_events(
    request: Request, page: int = 1, per_page: int = 50, q: Optional[str] = None
):
    """operation_logs 过滤视图:团队与权限事件(含 legacy employee.* 读侧兼容)。"""
    user = require_perm(request, "audit.log.view")
    # 安全事件占总日志的小头:取近 1000 条按前缀过滤后再分页(防业务日志把事件挤出首页)
    data = db.list_operation_logs_paged(tenant_id=str(user["tenant_id"]), q=q, limit_all=1000)
    matched = [
        r
        for r in data.get("rows", [])
        if str(r.get("action") or "").startswith(SECURITY_ACTION_PREFIXES)
    ]
    page = max(1, page)
    per_page = max(1, min(per_page, 200))
    start = (page - 1) * per_page
    rows = []
    for r in matched[start : start + per_page]:
        action = str(r.get("action") or "")
        rows.append(
            {
                "id": r.get("id"),
                "action": action,
                "actor": r.get("actor_username"),
                "target": r.get("target_name"),
                "details": r.get("details"),
                "ip": r.get("ip"),
                "created_at": (r["created_at"].isoformat() if r.get("created_at") else None),
            }
        )
    return {"ok": True, "events": rows, "page": page, "total": len(matched)}

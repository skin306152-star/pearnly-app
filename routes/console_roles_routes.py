# -*- coding: utf-8 -*-
"""控制台 · 自定义角色 API(G3 · docs/permissions/07 §四)。

GET    /api/team/roles/custom          列本租户自定义角色(+ 在用人数)
POST   /api/team/roles                  建自定义角色(三步向导提交)
PATCH  /api/team/roles/{role_id}        改名/改码集/停用(乐观锁防并发覆盖)
DELETE /api/team/roles/{role_id}        删(在用 → 422 先转移)
PUT    /api/team/members/{uid}/role-assign  分配角色(系统或自定义 · 下一请求即生效)

系统预设角色的只读说明卡仍由 console_team_routes 的 GET /api/team/roles 提供(本文件不重定义,
避开同路径冲突)。写口 require_perm team.member.edit_role(只 owner/admin 持有);role.* 落审计。
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.route_helpers import _log_op
from services.authz import roles_store
from services.authz.deps import require_perm

router = APIRouter()


class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)
    permissions: List[str] = Field(..., min_length=1)


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=40)
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    version: Optional[int] = None


class AssignRoleRequest(BaseModel):
    role_key: str = Field(..., min_length=3, max_length=64)


@router.get("/api/team/roles/custom")
async def list_custom_roles(request: Request):
    user = require_perm(request, "team.member.view")
    return {"ok": True, "roles": roles_store.list_custom_roles(str(user["tenant_id"]))}


@router.post("/api/team/roles")
async def create_custom_role(req: CreateRoleRequest, request: Request):
    user = require_perm(request, "team.member.edit_role")
    result = roles_store.create_custom_role(
        tenant_id=str(user["tenant_id"]),
        actor_id=str(user["id"]),
        display_name=req.name,
        permission_codes=req.permissions,
    )
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    role = result["role"]
    _log_op(
        request,
        user,
        "role.create",
        "role",
        role["id"],
        role["name"],
        {"key": role["key"], "permission_count": role["permission_count"]},
    )
    return {"ok": True, "role": role}


@router.patch("/api/team/roles/{role_id}")
async def update_custom_role(role_id: str, req: UpdateRoleRequest, request: Request):
    user = require_perm(request, "team.member.edit_role")
    result = roles_store.update_custom_role(
        tenant_id=str(user["tenant_id"]),
        role_id=role_id,
        display_name=req.name,
        permission_codes=req.permissions,
        is_active=req.is_active,
        expected_version=req.version,
    )
    if result.get("error"):
        status = 409 if result["error"] == "team.role_version_conflict" else 422
        raise HTTPException(status, detail=result["error"])
    role = result["role"]
    _log_op(
        request,
        user,
        "role.update",
        "role",
        role["id"],
        role["name"],
        {"permission_count": role["permission_count"], "is_active": role["is_active"]},
    )
    return {"ok": True, "role": role}


@router.delete("/api/team/roles/{role_id}")
async def delete_custom_role(role_id: str, request: Request):
    user = require_perm(request, "team.member.edit_role")
    result = roles_store.delete_custom_role(tenant_id=str(user["tenant_id"]), role_id=role_id)
    if result.get("error"):
        if result["error"] == "team.role_in_use":
            raise HTTPException(
                422,
                detail={
                    "code": "team.role_in_use",
                    "member_count": result.get("member_count", 0),
                },
            )
        raise HTTPException(422, detail=result["error"])
    _log_op(request, user, "role.delete", "role", role_id, result.get("name"), {})
    return {"ok": True}


@router.put("/api/team/members/{uid}/role-assign")
async def assign_role(uid: str, req: AssignRoleRequest, request: Request):
    """分配角色(系统预设或 custom:<slug>)。系统预设也走这里以统一前端单入口。"""
    user = require_perm(request, "team.member.edit_role")
    result = roles_store.assign_role(
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

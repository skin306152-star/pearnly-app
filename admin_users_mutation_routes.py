# -*- coding: utf-8 -*-
"""超管用户/员工管理 · 写入/变更路由(REFACTOR-WA · 从 admin_users_routes.py 按读/写域拆出)

纯搬家 · URL/method/权限/返回结构/错误码/业务逻辑 0 改 · 路由 verbatim(@router 装饰器不动)。
覆盖 9 变更路由:创建用户 · 改配额/状态 · 删除(密码确认)· 改密(410)· 员工启停/改密/删(410)·
级联删除老板(双确认)。复用 model 单一来源:AdminUpdateTenantQuota/Status from tenant_routes ·
EmployeeToggleRequest from team_routes。admin_users_routes.py 门面经 include_router 聚合本 router。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import db
from route_helpers import _log_op, _require_super_admin

# 复用已抽出模块的 model(单一来源 · 不重复定义)
from tenant_routes import AdminUpdateTenantQuotaRequest, AdminUpdateTenantStatusRequest
from team_routes import EmployeeToggleRequest

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=6, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=200)
    tenant_type: str = Field("shared_api", pattern="^(shared_api|byo_api)$")
    monthly_quota: int = Field(100, ge=0)
    notes: Optional[str] = None


class AdminVerifyPasswordRequest(BaseModel):
    password: str


class AdminDeleteUserRequest(BaseModel):
    password: str  # 超管自己的密码确认
    confirm_username: str  # 要删除用户的用户名(再次核对)


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100)


class CascadeDeleteRequest(BaseModel):
    confirm_username: str = Field(..., min_length=1, max_length=200)
    confirm_password: str = Field(..., min_length=1, max_length=200)


# 创建用户(超管)· 同时建 tenant + owner
@router.post("/api/admin/users")
async def admin_create_user(req: AdminCreateUserRequest, request: Request):
    admin = _require_super_admin(request)
    result = db.create_owner_user(
        username=req.username,
        password=req.password,
        company_name=req.company_name,
        tenant_type=req.tenant_type,
        monthly_quota=req.monthly_quota,
        notes=req.notes,
    )
    if not result.get("ok"):
        err = result.get("error", "create_failed")
        if err == "username_exists":
            raise HTTPException(409, detail="admin.username_exists")
        raise HTTPException(400, detail="admin.create_failed")
    _log_op(
        request,
        admin,
        "user.create",
        "user",
        result["user_id"],
        req.username,
        {
            "company_name": req.company_name,
            "tenant_type": req.tenant_type,
            "quota": req.monthly_quota,
        },
    )
    return {"ok": True, "user_id": result["user_id"], "tenant_id": result["tenant_id"]}


# 改配额(超管)· tenant_id 路径可从用户详情得到 · 但这里简化 · 按 user_id
@router.patch("/api/admin/users/{user_id}/quota")
async def admin_update_user_quota(
    user_id: str, req: AdminUpdateTenantQuotaRequest, request: Request
):
    admin = _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user or not user.get("tenant_id"):
        raise HTTPException(404, detail="admin.user_not_found")
    ok = db.update_tenant_quota(str(user["tenant_id"]), req.monthly_quota)
    if not ok:
        raise HTTPException(500, detail="admin.update_failed")
    _log_op(
        request,
        admin,
        "user.update_quota",
        "user",
        user_id,
        user.get("username"),
        {"new_quota": req.monthly_quota},
    )
    return {"ok": True}


# 改状态(超管)
@router.patch("/api/admin/users/{user_id}/status")
async def admin_update_user_status(
    user_id: str, req: AdminUpdateTenantStatusRequest, request: Request
):
    admin = _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user or not user.get("tenant_id"):
        raise HTTPException(404, detail="admin.user_not_found")
    ok = db.update_tenant_status(str(user["tenant_id"]), req.status)
    if not ok:
        raise HTTPException(500, detail="admin.update_failed")
    _log_op(
        request,
        admin,
        "user.update_status",
        "user",
        user_id,
        user.get("username"),
        {"new_status": req.status},
    )
    return {"ok": True}


# 删除用户(超管)· 级联删所有数据 · 要求密码确认
@router.post("/api/admin/users/{user_id}/delete")
async def admin_delete_user(user_id: str, req: AdminDeleteUserRequest, request: Request):
    admin = _require_super_admin(request)

    # 1. 验证超管密码
    if not db.verify_user_password(str(admin["id"]), req.password):
        raise HTTPException(403, detail="admin.wrong_password")

    # 2. 确认用户名匹配
    user = db.find_user_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="admin.user_not_found")
    if user.get("username") != req.confirm_username:
        raise HTTPException(400, detail="admin.username_mismatch")
    if user.get("is_super_admin"):
        raise HTTPException(400, detail="admin.cant_delete_super")

    # 3. 级联删
    ok = db.delete_owner_user_cascade(user_id)
    if not ok:
        raise HTTPException(500, detail="admin.delete_failed")
    _log_op(
        request,
        admin,
        "user.delete",
        "user",
        user_id,
        user.get("username"),
        {"company_name": user.get("company_name")},
    )
    return {"ok": True}


# 重置密码(超管)
@router.post("/api/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(user_id: str, request: Request):
    """v118.28.7 · 砍 · 大厂惯例(Xero/QuickBooks/Stripe)超管不碰客户密码
    客户忘密码请走登录页「忘记密码」自助 · 邮箱也丢了走身份验证申诉(人工流程)"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.password_reset_removed")


@router.patch("/api/admin/employees/{employee_id}/active")
async def admin_toggle_employee_active(
    employee_id: str, req: EmployeeToggleRequest, request: Request
):
    """v118.28.6 · 砍 · 行业惯例(Xero/QuickBooks/Stripe)超管不直接管客户员工 · 由所属老板自行操作"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.employee_action_removed")


@router.post("/api/admin/employees/{employee_id}/reset-password")
async def admin_reset_employee_password(employee_id: str, request: Request):
    """v118.28.6 · 砍 · 见上"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.employee_action_removed")


@router.delete("/api/admin/employees/{employee_id}")
async def admin_remove_employee(employee_id: str, request: Request):
    """v118.28.6 · 砍 · 见上"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.employee_action_removed")


@router.post("/api/admin/users/{user_id}/cascade-delete")
async def admin_cascade_delete(user_id: str, req: CascadeDeleteRequest, request: Request):
    """超管级联删除老板 + 整个 tenant + 所有员工 + 所有数据
    需要双重确认:超管自己的主密码 + 输入要删客户的用户名
    """
    admin = _require_super_admin(request)
    # 1) 拿目标 owner
    target = db.find_user_by_id(user_id)
    if not target:
        raise HTTPException(404, detail="admin.user_not_found")
    # v118.16.1 · 兼容老用户 role IS NULL(对齐 admin_list_users 筛选规则)
    target_role = target.get("role")
    if target_role and target_role != "owner":
        raise HTTPException(400, detail="admin.not_an_owner")
    # 2) 防自删
    if str(target["id"]) == str(admin["id"]):
        raise HTTPException(400, detail="admin.cannot_delete_self")
    # 3) 验证用户名(防误删)
    if (target.get("username") or "").strip() != req.confirm_username.strip():
        raise HTTPException(400, detail="admin.username_mismatch")
    # 4) 验证超管自己的密码
    if not db.verify_user_password(str(admin["id"]), req.confirm_password):
        raise HTTPException(403, detail="admin.password_invalid")
    # 5) 取影响范围(写入操作日志)
    preview = db.preview_owner_cascade(user_id) or {}
    target_name = target.get("username")
    # 6) 级联删
    ok = db.delete_owner_user_cascade(user_id)
    if not ok:
        raise HTTPException(500, detail="admin.cascade_delete_failed")
    # 7) 操作日志(deletion 之后写 · 因为 tenant_id 已删)
    _log_op(
        request,
        admin,
        "admin.user.cascade_delete",
        "user",
        user_id,
        target_name,
        {"counts": preview.get("counts", {}), "tenant_id": (preview.get("tenant") or {}).get("id")},
    )
    return {"ok": True, "deleted_username": target_name}

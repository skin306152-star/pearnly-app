# -*- coding: utf-8 -*-
"""
Pearnly · 租户管理路由模块(超管 CRUD + 用户本租户用量)(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / method / response shape / error code。

覆盖 6 个 API:
  GET   /api/admin/tenants                        · 列所有租户(仅超管)
  POST  /api/admin/tenants                        · 创建租户(仅超管)
  PATCH /api/admin/tenants/{tenant_id}/quota      · 改限额(仅超管)
  PATCH /api/admin/tenants/{tenant_id}/status     · 改状态(仅超管)
  GET   /api/admin/tenants/{tenant_id}/summary    · 租户运营概况(仅超管)
  GET   /api/me/tenant-usage                      · 当前用户查自己租户本月用量(所有用户)

依赖:
  - db.*(list_all_tenants / create_tenant / update_tenant_quota / update_tenant_status /
         get_tenant / get_tenant_usage_summary / list_tenant_members)
  - auth.get_current_user_from_request(/api/me/tenant-usage 用)
  - route_helpers._require_super_admin(5 个 admin 路由守门 · 公共)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _require_super_admin

router = APIRouter()


class AdminCreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    tenant_type: str = Field("shared_api", pattern="^(shared_api|byo_api|admin)$")
    monthly_quota: int = 100
    notes: Optional[str] = None


class AdminUpdateTenantQuotaRequest(BaseModel):
    monthly_quota: int = Field(..., ge=0)


class AdminUpdateTenantStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(active|warning|suspended|frozen)$")


@router.get("/api/admin/tenants")
async def admin_list_tenants(request: Request):
    """列出所有租户 · 仅超管"""
    _require_super_admin(request)
    tenants = db.list_all_tenants(limit=500)
    # 序列化
    result = []
    for t in tenants:
        result.append(
            {
                "id": str(t["id"]),
                "name": t.get("name"),
                "display_name": t.get("display_name"),
                "tenant_type": t.get("tenant_type"),
                "status": t.get("status"),
                "monthly_quota": int(t.get("monthly_quota") or 0),
                "used_this_month": int(t.get("used_this_month") or 0),
                "member_count": int(t.get("actual_member_count") or 0),
                "ocr_this_month": int(t.get("ocr_this_month") or 0),
                "last_active_at": (
                    t["last_active_at"].isoformat() if t.get("last_active_at") else None
                ),
                "subscription_expires_at": (
                    t["subscription_expires_at"].isoformat()
                    if t.get("subscription_expires_at")
                    else None
                ),
                "notes": t.get("notes"),
                "created_at": t["created_at"].isoformat() if t.get("created_at") else None,
            }
        )
    return {"tenants": result, "total": len(result)}


@router.post("/api/admin/tenants")
async def admin_create_tenant(req: AdminCreateTenantRequest, request: Request):
    """创建新租户 · 仅超管"""
    _require_super_admin(request)
    tenant_id = db.create_tenant(
        name=req.name,
        tenant_type=req.tenant_type,
        monthly_quota=req.monthly_quota,
        notes=req.notes,
    )
    if not tenant_id:
        raise HTTPException(500, detail="admin.create_tenant_failed")
    return {"ok": True, "tenant_id": tenant_id}


@router.patch("/api/admin/tenants/{tenant_id}/quota")
async def admin_update_tenant_quota(
    tenant_id: str, req: AdminUpdateTenantQuotaRequest, request: Request
):
    """改租户限额 · 仅超管"""
    _require_super_admin(request)
    ok = db.update_tenant_quota(tenant_id, req.monthly_quota)
    if not ok:
        raise HTTPException(404, detail="admin.tenant_not_found")
    return {"ok": True}


@router.patch("/api/admin/tenants/{tenant_id}/status")
async def admin_update_tenant_status(
    tenant_id: str, req: AdminUpdateTenantStatusRequest, request: Request
):
    """改租户状态 · 仅超管"""
    _require_super_admin(request)
    ok = db.update_tenant_status(tenant_id, req.status)
    if not ok:
        raise HTTPException(404, detail="admin.tenant_not_found")
    return {"ok": True}


@router.get("/api/admin/tenants/{tenant_id}/summary")
async def admin_tenant_summary(tenant_id: str, request: Request):
    """租户运营概况 · 仅超管"""
    _require_super_admin(request)
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(404, detail="admin.tenant_not_found")
    summary = db.get_tenant_usage_summary(tenant_id)
    members = db.list_tenant_members(tenant_id)
    return {
        "tenant": {
            "id": str(tenant["id"]),
            "name": tenant.get("name"),
            "tenant_type": tenant.get("tenant_type"),
            "status": tenant.get("status"),
            "monthly_quota": int(tenant.get("monthly_quota") or 0),
            "notes": tenant.get("notes"),
        },
        "summary": summary,
        "members": [
            {
                "id": str(m["id"]),
                "username": m.get("username"),
                "email": m.get("email"),
                "role": m.get("role"),
                "is_active": m.get("is_active"),
                "is_super_admin": m.get("is_super_admin"),
                "last_login_at": m["last_login_at"].isoformat() if m.get("last_login_at") else None,
                "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
            }
            for m in members
        ],
    }


@router.get("/api/me/tenant-usage")
async def get_my_tenant_usage(request: Request):
    """
    当前登录用户查看自己租户的本月用量(给限额仪表盘用)
    所有用户都能调 · 只查自己的租户
    """
    user = get_current_user_from_request(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        # 没挂租户 · 返回空
        return {"has_tenant": False}
    summary = db.get_tenant_usage_summary(str(tenant_id))
    tenant = db.get_tenant(str(tenant_id))
    return {
        "has_tenant": True,
        "tenant_name": tenant.get("name") if tenant else None,
        "tenant_type": tenant.get("tenant_type") if tenant else None,
        "tenant_status": tenant.get("status") if tenant else None,
        "quota": summary["quota"],
        "user_count": summary["user_count"],
        "ocr_this_month": summary["ocr_this_month"],
    }

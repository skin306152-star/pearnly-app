# -*- coding: utf-8 -*-
"""POS 收银员鉴权 + 开通收银路由(POS 项目 · PO-B1 · docs/pos/04 §1/§2)。

薄层:统一 POS 信封(ok / PosError)。SQL/逻辑在 services/pos/{cashier,auth,onboarding}。

匿名前台(开班选人 + PIN 登录):前台启动时还没 token,按 workspace_client_id(全局 bigserial)
反查 tenant,再以该 tenant 为界查收银员。匿名只暴露名字/颜色(低敏);真正登录仍需 PIN。游标用
bypass=True 但每条语句仍 WHERE tenant_id(应用层硬隔离 · RLS 仅兜底)。

onboarding 是管理动作:require_owner(收银员 token 不可调)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, ok, require_owner, require_workspace
from services.pos import auth as pos_auth
from services.pos import cashier as cashier_dal
from services.pos import onboarding as onboarding_svc

router = APIRouter(prefix="/api/pos", tags=["pos-auth"])


class PinLoginRequest(BaseModel):
    workspace_client_id: int
    cashier_id: str = Field(..., min_length=1, max_length=64)
    pin: str = Field(..., min_length=1, max_length=32)


class FirstCashier(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=80)
    pin: str = Field(..., min_length=4, max_length=32)
    color: Optional[str] = Field(None, max_length=20)


class OnboardingRequest(BaseModel):
    workspace_client_id: int
    business_type: str = Field("retail", max_length=40)
    warehouse_name: Optional[str] = Field(None, max_length=120)
    first_cashier: Optional[FirstCashier] = None


def _resolve_tenant(cur, workspace_client_id: int) -> str:
    tid = cashier_dal.resolve_tenant_for_workspace(cur, workspace_client_id=workspace_client_id)
    if not tid:
        raise PosError("pos.forbidden", 403)
    return tid


@router.get("/cashiers")
async def api_list_cashiers(request: Request, workspace_client_id: int = Query(...)):
    """开班选人列表(匿名 · 仅名字/颜色)。"""
    with db.get_cursor_rls(bypass=True) as cur:
        tid = _resolve_tenant(cur, workspace_client_id)
        rows = cashier_dal.list_cashiers(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id
        )
    return ok({"cashiers": [dict(r) | {"id": str(r["id"])} for r in rows]})


@router.post("/auth/pin")
async def api_pin_login(req: PinLoginRequest, request: Request):
    """PIN 登录 → POS token。"""
    with db.get_cursor_rls(bypass=True) as cur:
        tid = _resolve_tenant(cur, req.workspace_client_id)
        data = pos_auth.login(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            cashier_id=req.cashier_id,
            pin=req.pin,
        )
    return ok(data)


class CashierCreate(BaseModel):
    workspace_client_id: int
    display_name: str = Field(..., min_length=1, max_length=80)
    pin: str = Field(..., min_length=4, max_length=32)
    color: Optional[str] = Field(None, max_length=20)


class CashierUpdate(BaseModel):
    workspace_client_id: int
    display_name: Optional[str] = Field(None, min_length=1, max_length=80)
    pin: Optional[str] = Field(None, min_length=4, max_length=32)
    color: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


def _cashier_out(row) -> dict:
    return {
        "id": str(row["id"]),
        "display_name": row["display_name"],
        "color": row.get("color"),
        "is_active": bool(row["is_active"]),
    }


@router.get("/admin/cashiers")
async def api_admin_list_cashiers(request: Request, workspace_client_id: int = Query(...)):
    """收银员后台管理列表(老板/超管 · 含停用项 + 最近开班 + 可否删)。"""
    tid, _uid = require_owner(request)
    with db.get_cursor_rls(tid) as cur:
        require_workspace(cur, tid, workspace_client_id)
        rows = cashier_dal.list_cashiers_admin(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id
        )
    out = []
    for r in rows:
        item = _cashier_out(r)
        lo = r.get("last_opened_at")
        item["last_opened_at"] = lo.isoformat() if lo else None
        item["has_shifts"] = bool(r.get("has_shifts"))
        out.append(item)
    return ok({"cashiers": out})


@router.post("/admin/cashiers")
async def api_admin_create_cashier(req: CashierCreate, request: Request):
    """新增收银员(名字 + PIN + 颜色)。"""
    tid, _uid = require_owner(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, req.workspace_client_id)
        row = cashier_dal.create_cashier(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            display_name=req.display_name.strip(),
            pin_hash=pos_auth.hash_pin(req.pin),
            color=req.color,
        )
    return ok({"cashier": _cashier_out(row)})


@router.put("/admin/cashiers/{cashier_id}")
async def api_admin_update_cashier(cashier_id: str, req: CashierUpdate, request: Request):
    """改名/换色/启停/重设 PIN(只更传入字段)。"""
    tid, _uid = require_owner(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, req.workspace_client_id)
        row = cashier_dal.update_cashier(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            cashier_id=cashier_id,
            display_name=req.display_name.strip() if req.display_name else None,
            color=req.color,
            is_active=req.is_active,
            pin_hash=pos_auth.hash_pin(req.pin) if req.pin else None,
        )
        if not row:
            raise PosError("pos.cashier_not_found", 404)
    return ok({"cashier": _cashier_out(row)})


@router.delete("/admin/cashiers/{cashier_id}")
async def api_admin_delete_cashier(
    cashier_id: str, request: Request, workspace_client_id: int = Query(...)
):
    """删除从未开过班的收银员;开过班的只能停用(保历史)→ pos.cashier_in_use(409)。"""
    tid, _uid = require_owner(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, workspace_client_id)
        res = cashier_dal.delete_cashier_if_unused(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id, cashier_id=cashier_id
        )
        if res is None:
            raise PosError("pos.cashier_not_found", 404)
        if res is False:
            raise PosError("pos.cashier_in_use", 409)
    return ok({"deleted": True})


@router.put("/admin/onboarding")
async def api_onboarding(req: OnboardingRequest, request: Request):
    """开通收银(老板/超管)→ 开模块 + 建仓/终端/首位收银员。"""
    tid, _uid = require_owner(request)
    fc = req.first_cashier.model_dump() if req.first_cashier else None
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, req.workspace_client_id)
        data = onboarding_svc.onboard(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            business_type=req.business_type,
            warehouse_name=req.warehouse_name,
            first_cashier=fc,
        )
    return ok(data)

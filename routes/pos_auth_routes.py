# -*- coding: utf-8 -*-
"""POS 收银员鉴权 + 开通收银路由(POS 项目 · PO-B1 · docs/pos/04 §1/§2)。

薄层:统一 POS 信封(ok / PosError)。SQL/逻辑在 services/pos/{cashier,auth,onboarding}。

匿名前台(开班选人 + PIN 登录):前台启动时还没 token,按 workspace_client_id(全局 bigserial)
反查 tenant,再以该 tenant 为界查收银员。匿名只暴露名字/颜色(低敏);真正登录仍需 PIN。游标用
bypass=True 但每条语句仍 WHERE tenant_id(应用层硬隔离 · RLS 仅兜底)。

onboarding 是管理动作:require_perm_pos_tid(收银员 token 不可调)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import create_pos_store_token, decode_access_token
from core.pos_api import PosError, ok, require_workspace
from services.authz.deps import require_perm_pos_tid
from services.pos import auth as pos_auth
from services.pos import cashier as cashier_dal
from services.pos import onboarding as onboarding_svc
from services.pos import store_binding

router = APIRouter(prefix="/api/pos", tags=["pos-auth"])


class PinLoginRequest(BaseModel):
    workspace_client_id: Optional[int] = None  # 老板「切到收银台」旧路径用;设备绑定走店铺令牌
    cashier_id: str = Field(..., min_length=1, max_length=64)
    pin: str = Field(..., min_length=1, max_length=32)


class BindRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=16)


class WorkspaceBody(BaseModel):
    workspace_client_id: int


def _store_claims(request: Request) -> Optional[dict]:
    """从 Authorization 里取已验签的店铺令牌声明(typ=pos_store);非店铺令牌返 None。"""
    auth = request.headers.get("Authorization") or request.headers.get("authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    payload = decode_access_token(auth[7:].strip())
    if not payload or payload.get("typ") != "pos_store":
        return None
    return payload


def _store_name(cur, tid: str, workspace_client_id: int) -> str:
    """账套显示名(店铺令牌签发/二维码标注用)。无则空串。"""
    cur.execute(
        "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tid),
    )
    row = cur.fetchone()
    return row["name"] if row else ""


def _pos_base_url() -> str:
    """自身 base URL(店铺接入链接/二维码用)· 同 oauth/邮件链接范式 · 多环境不写死。"""
    import os

    return (os.environ.get("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")


def _workspace_from_store_or_legacy(cur, request: Request, legacy_ws: Optional[int]) -> tuple:
    """收银前台定位 (tenant, workspace):优先设备店铺令牌(校 token_version 防重置后旧令牌),
    否则回落老板「切到收银台」旧路径(localStorage 选的账套 → 传 workspace_client_id)。"""
    claims = _store_claims(request)
    if claims:
        tid = str(claims["tenant_id"])
        ws = int(claims["workspace_client_id"])
        ver = store_binding.current_version(cur, tenant_id=tid, workspace_client_id=ws)
        if ver is None or ver != claims.get("ver"):
            raise PosError("pos.store_unbound", 401)  # 店铺码已被重置 → 设备需重绑
        return tid, ws
    if legacy_ws is None:
        raise PosError("pos.store_unbound", 401)  # 既无店铺令牌又无账套 → 设备未绑定
    tid = _resolve_tenant(cur, legacy_ws)
    return tid, int(legacy_ws)


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


@router.post("/bind")
async def api_bind_device(req: BindRequest, request: Request):
    """设备绑定:店铺码 → 解析 (tenant, workspace) → 签发长期店铺令牌(设备存 localStorage)。
    公开端点(店铺码本身即低敏凭证 · 列名+需 PIN 才能卖)。无效码 → pos.store_code_invalid。"""
    code = (req.code or "").strip().upper()
    with db.get_cursor_rls(bypass=True) as cur:
        row = store_binding.resolve(cur, code=code)
        if not row:
            raise PosError("pos.store_code_invalid", 404)
        tid = str(row["tenant_id"])
        ws = int(row["workspace_client_id"])
        ver = int(row["token_version"])
        store_name = _store_name(cur, tid, ws)
    token = create_pos_store_token(tenant_id=tid, workspace_client_id=ws, version=ver)
    return ok(
        {
            "store_token": token,
            "workspace_client_id": ws,
            "store_name": store_name,
        }
    )


@router.get("/cashiers")
async def api_list_cashiers(request: Request, workspace_client_id: Optional[int] = Query(None)):
    """开班选人列表(仅名字/颜色)。账套来自设备店铺令牌(优先)或老板旧路径 workspace_client_id。"""
    with db.get_cursor_rls(bypass=True) as cur:
        tid, ws = _workspace_from_store_or_legacy(cur, request, workspace_client_id)
        rows = cashier_dal.list_cashiers(cur, tenant_id=tid, workspace_client_id=ws)
    return ok({"cashiers": [dict(r) | {"id": str(r["id"])} for r in rows]})


@router.post("/auth/pin")
async def api_pin_login(req: PinLoginRequest, request: Request):
    """PIN 登录 → POS 收银员 token。账套来自设备店铺令牌(优先)或老板旧路径。"""
    with db.get_cursor_rls(bypass=True) as cur:
        tid, ws = _workspace_from_store_or_legacy(cur, request, req.workspace_client_id)
        data = pos_auth.login(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            cashier_id=req.cashier_id,
            pin=req.pin,
        )
    return ok(data)


@router.get("/admin/store-code")
async def api_get_store_code(request: Request, workspace_client_id: int = Query(...)):
    """取该账套店铺码(无则建)· owner。前端拼二维码/链接 pearnly.com/pos?store=<code>。"""
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, workspace_client_id)
        store_name = _store_name(cur, tid, workspace_client_id)
        info = store_binding.get_or_create_code(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            store_name=store_name,
        )
    link = _pos_base_url() + "/pos?store=" + info["code"]
    return ok(
        {
            "code": info["code"],
            "store_name": store_name,
            "workspace_client_id": workspace_client_id,
            "link": link,
            "qr": store_binding.qr_png_base64(link),
        }
    )


@router.post("/admin/store-code/reset")
async def api_reset_store_code(req: WorkspaceBody, request: Request):
    """重置店铺码:换码 + 吊销所有已绑设备(丢机/离职)· owner。"""
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, req.workspace_client_id)
        store_name = _store_name(cur, tid, req.workspace_client_id)
        info = store_binding.reset_code(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            store_name=store_name,
        )
    return ok({"code": info["code"], "store_name": store_name})


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
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
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
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
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
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
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
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
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
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
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

# -*- coding: utf-8 -*-
"""POS 收银员鉴权 + 开通收银路由(POS 项目 · PO-B1 · docs/pos/04 §1/§2)。

薄层:统一 POS 信封(ok / PosError)。SQL/逻辑在 services/pos/{cashier,auth,onboarding}。

开班选人和 PIN 登录只接受已绑定设备令牌,或具备 POS 权限且通过账套范围校验的平台会话。
游标用 bypass=True,每条语句仍以已验证的 tenant_id 和 workspace_client_id 限定范围。

onboarding 是管理动作:require_perm_pos_tid(收银员 token 不可调)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import create_pos_store_token, decode_access_token
from core.pos_api import PosError, ok, require_workspace
from services.authz.deps import check_workspace_scope, require_perm_pos, require_perm_pos_tid
from services.pos import auth as pos_auth
from services.pos import caps as caps_svc
from services.pos import cashier as cashier_dal
from services.pos import entitlements as entitlement_svc
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


def _workspace_from_store_token(cur, request: Request, requested_workspace: Optional[int]) -> tuple:
    """从店铺令牌或已授权平台账号解析收银账套,拒绝匿名账套反查。"""
    claims = _store_claims(request)
    if claims:
        tid = str(claims["tenant_id"])
        ws = int(claims["workspace_client_id"])
        ver = store_binding.current_version(cur, tenant_id=tid, workspace_client_id=ws)
        if ver is None or ver != claims.get("ver"):
            raise PosError("pos.store_unbound", 401)  # 店铺码已被重置 → 设备需重绑
        if requested_workspace is not None and int(requested_workspace) != ws:
            raise PosError("pos.forbidden", 403)
        return tid, ws
    if not request.headers.get("Authorization") and not request.headers.get("authorization"):
        raise PosError("pos.store_unbound", 401)  # 既无店铺令牌又无账套 → 设备未绑定
    if requested_workspace is None:
        raise PosError("pos.store_unbound", 401)
    user = require_perm_pos(request, "pos.sale.operate")
    if user.get("role") == "cashier" or not user.get("tenant_id"):
        raise PosError("pos.forbidden", 403)
    tid = str(user["tenant_id"])
    ws = int(requested_workspace)
    require_workspace(cur, tid, ws)
    check_workspace_scope(request, user, ws, pos=True)
    return tid, ws


class FirstCashier(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=80)
    pin: str = Field(..., min_length=4, max_length=32)
    color: Optional[str] = Field(None, max_length=20)


class OnboardingRequest(BaseModel):
    workspace_client_id: int
    business_type: str = Field("retail", max_length=40)
    warehouse_name: Optional[str] = Field(None, max_length=120)
    first_cashier: Optional[FirstCashier] = None


def _enforce_entitlement_limit(cur, tid: str, workspace_client_id: int, kind: str) -> None:
    """开通版上限执行:只对持有效 pos_entitlement 的租户卡上限(无授权=完整版/存量,零影响)。

    超限 → PosError pos.entitlement_{store|cashier}_limit(前端映射四语「已达开通版上限·想开更多
    联系我们再购一份」)。detail 带 used/limit 供前端可选拼数。
    """
    res = entitlement_svc.check_limit(
        cur, tenant_id=tid, workspace_client_id=workspace_client_id, kind=kind
    )
    if res["entitled"] and not res["allowed"]:
        raise PosError(f"pos.entitlement_{kind}_limit", 403, detail=f"{res['used']}/{res['limit']}")


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
    """开班选人列表(仅名字/颜色)。账套来自店铺令牌或已授权平台账号。"""
    with db.get_cursor_rls(bypass=True) as cur:
        tid, ws = _workspace_from_store_token(cur, request, workspace_client_id)
        rows = cashier_dal.list_cashiers(cur, tenant_id=tid, workspace_client_id=ws)
    return ok({"cashiers": [dict(r) | {"id": str(r["id"])} for r in rows]})


@router.post("/auth/pin")
async def api_pin_login(req: PinLoginRequest, request: Request):
    """PIN 登录 → POS 收银员 token。账套来自店铺令牌或已授权平台账号。"""
    with db.get_cursor_rls(bypass=True) as cur:
        tid, ws = _workspace_from_store_token(cur, request, req.workspace_client_id)
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
    """取该账套店铺码(无则建)· owner。前端拼二维码/链接 pearnly.com/cashier?store=<code>(PS-5 迁址)。"""
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, workspace_client_id)
        # 开通版店铺上限:新账套要码时卡(本账套已有码=幂等放行,不算新开店)。
        _enforce_entitlement_limit(cur, tid, workspace_client_id, "store")
        store_name = _store_name(cur, tid, workspace_client_id)
        info = store_binding.get_or_create_code(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            store_name=store_name,
        )
    link = _pos_base_url() + "/cashier?store=" + info["code"]
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
    # 绑一个持 pos.refund.approve 的主账号 → 该收银员成为退货/作废授权人(PS-1)。
    approver_user_id: Optional[str] = Field(None, max_length=64)


class CashierUpdate(BaseModel):
    workspace_client_id: int
    display_name: Optional[str] = Field(None, min_length=1, max_length=80)
    pin: Optional[str] = Field(None, min_length=4, max_length=32)
    color: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    # ""/null = 解绑授权人;省略 = 不动绑定。
    approver_user_id: Optional[str] = Field(None, max_length=64)
    # 纯收银员按人权限(折扣上限/退作废/改价/成本可见);省略 = 不动。白名单校验见 caps.sanitize_caps。
    caps: Optional[dict] = None


def _validate_approver(cur, tid: str, approver_user_id: Optional[str]) -> None:
    """绑定授权人前置:必须是本租户在职成员(防绑跨租户/离职账号越权授权)。"""
    if approver_user_id and not cashier_dal.is_active_member(
        cur, tenant_id=tid, user_id=approver_user_id
    ):
        raise PosError("pos.forbidden", 403, detail="approver_not_member")


def _cashier_out(row) -> dict:
    return {
        "id": str(row["id"]),
        "display_name": row["display_name"],
        "color": row.get("color"),
        "is_active": bool(row["is_active"]),
        "caps": caps_svc.merge_defaults(row.get("caps") if hasattr(row, "get") else None),
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
        # 绑主账号者权限随其 RBAC(resolve_caps 忽略 caps 列)→ 前端据此显只读提示、不给编辑。
        item["has_approver"] = bool(r.get("user_id"))
        out.append(item)
    return ok({"cashiers": out})


@router.post("/admin/cashiers")
async def api_admin_create_cashier(req: CashierCreate, request: Request):
    """新增收银员(名字 + PIN + 颜色)。"""
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, req.workspace_client_id)
        # 开通版收银员上限:达上限拦新增(启停/改名不受影响)。
        _enforce_entitlement_limit(cur, tid, req.workspace_client_id, "cashier")
        _validate_approver(cur, tid, req.approver_user_id)
        row = cashier_dal.create_cashier(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            display_name=req.display_name.strip(),
            pin_hash=pos_auth.hash_pin(req.pin),
            color=req.color,
            user_id=req.approver_user_id or None,
        )
    return ok({"cashier": _cashier_out(row)})


@router.put("/admin/cashiers/{cashier_id}")
async def api_admin_update_cashier(cashier_id: str, req: CashierUpdate, request: Request):
    """改名/换色/启停/重设 PIN(只更传入字段)。"""
    tid, _uid = require_perm_pos_tid(request, "pos.admin.manage")
    # 省略字段 = 不动绑定;传空串/null = 解绑;传 user_id = 绑定(校验在职成员)。
    fields_set = req.model_dump(exclude_unset=True) if hasattr(req, "model_dump") else {}
    user_id_arg = cashier_dal._UNSET
    if "approver_user_id" in fields_set:
        user_id_arg = req.approver_user_id or None
    caps_arg = cashier_dal._UNSET
    if "caps" in fields_set:
        try:
            caps_arg = caps_svc.sanitize_caps(req.caps or {})
        except ValueError as e:
            raise PosError("pos.caps_invalid", 422, detail=str(e))
    with db.get_cursor_rls(tid, commit=True) as cur:
        require_workspace(cur, tid, req.workspace_client_id)
        _validate_approver(cur, tid, req.approver_user_id)
        row = cashier_dal.update_cashier(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            cashier_id=cashier_id,
            display_name=req.display_name.strip() if req.display_name else None,
            color=req.color,
            is_active=req.is_active,
            pin_hash=pos_auth.hash_pin(req.pin) if req.pin else None,
            user_id=user_id_arg,
            caps=caps_arg,
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

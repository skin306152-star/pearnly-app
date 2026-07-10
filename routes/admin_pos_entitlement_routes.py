# -*- coding: utf-8 -*-
"""Earn 超管 · POS 买断开通(ค่าติดตั้งและเปิดใช้งาน)入口(PS-3 S 档)。

超管手工:输租户标识 → 看现状 → 开通(默认已付 ฿1000 · 生成授权码)/ 吊销 / 转移。
全部经 _require_super_admin 守门 + _log_op 审计。业务逻辑在 services/pos/entitlements;
本层只做:解析租户、组装现状、翻译 ValueError(状态机拒绝)成干净 409/404。

用 db.get_cursor(owner · BYPASSRLS)跨租户操作(超管/迁移通道);读现状走只读游标。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from core import db
from core.route_helpers import _log_op, _require_super_admin
from services.modules import store as modules_store
from services.pos import entitlements as ent
from services.pos import provision as pos_provision

router = APIRouter()

_DEFAULT_AMOUNT_THB = 1000


def _resolve_tenant(cur, q: str) -> Optional[dict]:
    """按标识解析租户:tenant_id(uuid)优先,其次成员邮箱/用户名精确,再次租户名模糊。

    用户名精确匹配放在租户名模糊之前:发放纯用户名账号后前端会用该用户名回查现状,
    模糊命名会误命中他人租户,故先走成员用户名精确定位。返回 {id,name,created_at}。
    """
    q = (q or "").strip()
    if not q:
        return None
    cur.execute("SELECT id::text AS id, name, created_at FROM tenants WHERE id::text = %s", (q,))
    row = cur.fetchone()
    if row:
        return dict(row)
    if "@" in q:
        cur.execute(
            "SELECT t.id::text AS id, t.name, t.created_at FROM tenants t "
            "JOIN users u ON u.tenant_id = t.id WHERE lower(u.email) = lower(%s) LIMIT 1",
            (q,),
        )
        row = cur.fetchone()
        if row:
            return dict(row)
    else:
        cur.execute(
            "SELECT t.id::text AS id, t.name, t.created_at FROM tenants t "
            "JOIN users u ON u.tenant_id = t.id WHERE lower(u.username) = lower(%s) LIMIT 1",
            (q,),
        )
        row = cur.fetchone()
        if row:
            return dict(row)
    cur.execute(
        "SELECT id::text AS id, name, created_at FROM tenants WHERE name ILIKE %s "
        "ORDER BY created_at DESC LIMIT 1",
        (f"%{q}%",),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _entitlement_out(row) -> Optional[dict]:
    if not row:
        return None
    return {
        "grant_code": row["grant_code"],
        "amount_paid_thb": float(row["amount_paid_thb"] or 0),
        "store_limit": int(row["store_limit"]),
        "cashier_limit": int(row["cashier_limit"]),
        "status": row["status"],
        "purchased_at": row["purchased_at"].isoformat() if row["purchased_at"] else None,
    }


def _status_for(cur, tenant: dict) -> dict:
    """租户现状快照:授权行 + 已用店/收银员数 + 业态 + 订阅有无(给超管开通前核对)。"""
    tid = tenant["id"]
    active = ent.get_for_tenant(cur, tenant_id=tid, active_only=True)
    cur.execute("SELECT count(*) AS n FROM pos_store_codes WHERE tenant_id = %s::uuid", (tid,))
    stores = int((cur.fetchone() or {}).get("n") or 0)
    cur.execute(
        "SELECT count(*) AS n FROM pos_cashiers WHERE tenant_id = %s::uuid AND is_active = TRUE",
        (tid,),
    )
    cashiers = int((cur.fetchone() or {}).get("n") or 0)
    return {
        "tenant": {
            "id": tid,
            "name": tenant.get("name") or "(无名)",
            "created_at": tenant["created_at"].isoformat() if tenant.get("created_at") else None,
        },
        "entitlement": _entitlement_out(active),
        "stores_used": stores,
        "cashiers_used": cashiers,
        "business_type": modules_store.get_business_type(cur, tenant_id=tid),
        "has_subscription": db.get_active_subscription(tid) is not None,
    }


class GrantBody(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=64)
    amount_paid_thb: Optional[float] = Field(None, ge=0)


class TenantBody(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=64)


class TransferBody(BaseModel):
    from_tenant_id: str = Field(..., min_length=1, max_length=64)
    to_tenant_id: str = Field(..., min_length=1, max_length=64)


class ProvisionBody(BaseModel):
    # 账号标识:任意用户名或邮箱(格式校验在服务层 resolve_account_identifier · 单一事实源)。
    account: str = Field(..., min_length=1, max_length=200)
    tenant_name: Optional[str] = Field(None, max_length=100)
    amount_paid_thb: Optional[float] = Field(None, ge=0)
    # 可选自定义初始密码(留空自动生成强随机)· 策略校验在服务层(与重置流同源)
    password: Optional[str] = Field(None, max_length=128)


class ResetPasswordBody(BaseModel):
    # 账号标识:用户名或邮箱(与发放同口径)。
    account: str = Field(..., min_length=1, max_length=200)
    # 可选自定义新密码(留空自动生成强随机)
    password: Optional[str] = Field(None, max_length=128)


@router.get("/api/admin/pos-entitlement")
async def get_pos_entitlement(request: Request, q: str = Query(..., min_length=1)):
    """按标识查租户现状(授权 + 已用店/收银员 + 业态)。查不到 404。"""
    _require_super_admin(request)
    with db.get_cursor() as cur:
        tenant = _resolve_tenant(cur, q)
        if not tenant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="admin.tenant_not_found")
        return _status_for(cur, tenant)


@router.post("/api/admin/pos-entitlement/grant")
async def grant_pos_entitlement(request: Request, body: GrantBody):
    """开通买断授权(默认已付 ฿1000)→ 联动 pos_only 业态 + 记 credit_transactions 审计。"""
    user = _require_super_admin(request)
    amount = _DEFAULT_AMOUNT_THB if body.amount_paid_thb is None else body.amount_paid_thb
    with db.get_cursor(commit=True) as cur:
        tenant = _resolve_tenant(cur, body.tenant_id)
        if not tenant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="admin.tenant_not_found")
        try:
            row = ent.grant(
                cur, tenant_id=tenant["id"], amount_paid_thb=amount, granted_by=str(user["id"])
            )
        except ValueError as e:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"pos.entitlement_{e}") from e
    _log_op(
        request,
        user,
        action="pos_entitlement.grant",
        target_type="tenant",
        target_id=tenant["id"],
        target_name=tenant.get("name"),
        details=f"amount={amount} code={row['grant_code']}",
    )
    return {"ok": True, "grant_code": row["grant_code"], "entitlement": _entitlement_out(row)}


@router.post("/api/admin/pos-entitlement/provision")
async def provision_pos_account(request: Request, body: ProvisionBody):
    """发放账号一条龙:输客户账号(用户名或邮箱)→ 无账号则建号(回显一次性初始密码)+ 建租户 + grant。

    账号已存在 → 走既有租户开通路(不建号、不回显密码)。审计只记账号/租户/授权码,
    绝不落初始密码(铁律 #26:密码不进日志)。业务逻辑在 services/pos/provision。
    """
    user = _require_super_admin(request)
    amount = _DEFAULT_AMOUNT_THB if body.amount_paid_thb is None else body.amount_paid_thb
    with db.get_cursor(commit=True) as cur:
        try:
            res = pos_provision.provision_pos_account(
                cur,
                account=body.account,
                tenant_name=(body.tenant_name or None),
                granted_by=str(user["id"]),
                amount_paid_thb=amount,
                password=body.password,
            )
        except ValueError as e:
            code = str(e)
            if code in ("password_too_short", "password_too_weak"):
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                detail = f"account.{code}"
            elif code in (
                "email_invalid",
                "username_invalid",
                "account_missing",
                "tenant_provision_failed",
            ):
                status_code = status.HTTP_400_BAD_REQUEST
                detail = f"pos.provision_{code}"
            else:
                status_code = status.HTTP_409_CONFLICT
                detail = f"pos.provision_{code}"
            raise HTTPException(status_code, detail=detail) from e
    # 审计:带 existed/账号/租户/授权码 —— 刻意不带 initial_password(不落日志)。
    _log_op(
        request,
        user,
        action="pos_entitlement.provision",
        target_type="tenant",
        target_id=res["tenant_id"],
        target_name=body.account,
        details=f"existed={res['existed']} code={res['grant_code']}",
    )
    return {
        "ok": True,
        "existed": res["existed"],
        "tenant_id": res["tenant_id"],
        "grant_code": res["grant_code"],
        # 一次性回显:仅新建账号有值,超管当场转交客户后不再可得。
        "initial_password": res["initial_password"],
    }


@router.post("/api/admin/pos-entitlement/reset-password")
async def reset_pos_account_password(request: Request, body: ResetPasswordBody):
    """发放制账号重置密码(严格限定域 · 不是通用改密)。

    范围=账号所属租户持 pos_entitlement(任意 status)且账号是该租户成员;范围外(主站自由
    注册用户/超管/不存在邮箱)一律 404 不区分缘由(防枚举)。通用超管改密端点历史上因账户
    接管风险被砍 410(勘察修复台账 #1),不许复活——范围判定在 services/pos/provision。
    密码可选自定义(策略不合格 422);回显一次,审计与日志绝不含密码本体。
    """
    user = _require_super_admin(request)
    with db.get_cursor(commit=True) as cur:
        try:
            res = pos_provision.reset_pos_account_password(
                cur, account=body.account, password=body.password
            )
        except ValueError as e:
            code = str(e)
            if code in ("password_too_short", "password_too_weak"):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"account.{code}"
                ) from e
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="pos.reset_not_available") from e
    # 审计:谁给谁重置了密码(操作人 + 目标账号)—— 刻意不带密码本体。
    _log_op(
        request,
        user,
        action="pos_entitlement.reset_password",
        target_type="user",
        target_id=res["user_id"],
        target_name=body.account,
    )
    return {"ok": True, "account": res["account"], "new_password": res["new_password"]}


@router.post("/api/admin/pos-entitlement/revoke")
async def revoke_pos_entitlement(request: Request, body: TenantBody):
    """吊销授权(active→revoked)。非法状态跳转 → 409。"""
    user = _require_super_admin(request)
    with db.get_cursor(commit=True) as cur:
        tenant = _resolve_tenant(cur, body.tenant_id)
        if not tenant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="admin.tenant_not_found")
        try:
            ent.revoke(cur, tenant_id=tenant["id"], revoked_by=str(user["id"]))
        except ValueError as e:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"pos.entitlement_{e}") from e
    _log_op(
        request,
        user,
        action="pos_entitlement.revoke",
        target_type="tenant",
        target_id=tenant["id"],
        target_name=tenant.get("name"),
    )
    return {"ok": True}


@router.post("/api/admin/pos-entitlement/transfer")
async def transfer_pos_entitlement(request: Request, body: TransferBody):
    """转移授权:源租户 active→transferred + 目标租户落地 active。非法状态 → 409。"""
    user = _require_super_admin(request)
    with db.get_cursor(commit=True) as cur:
        src = _resolve_tenant(cur, body.from_tenant_id)
        dst = _resolve_tenant(cur, body.to_tenant_id)
        if not src or not dst:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="admin.tenant_not_found")
        try:
            row = ent.transfer(
                cur,
                from_tenant_id=src["id"],
                to_tenant_id=dst["id"],
                transferred_by=str(user["id"]),
            )
        except ValueError as e:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"pos.entitlement_{e}") from e
    _log_op(
        request,
        user,
        action="pos_entitlement.transfer",
        target_type="tenant",
        target_id=dst["id"],
        target_name=dst.get("name"),
        details=f"from={src['id']}",
    )
    return {"ok": True, "grant_code": row["grant_code"], "entitlement": _entitlement_out(row)}

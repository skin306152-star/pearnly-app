# -*- coding: utf-8 -*-
"""Earn 超管 · ERP 入口邀请管理(erp_portal 闸的发放侧)。

core/feature_flags.erp_portal_enabled_for 按账套主体归属判定灰度:有 tenant_id 走
tenant(团队共享同一开关状态),个人套账(无 tenant)退回 user_id。本路由是这条
tenant-first 判据的写入口 —— 加错 id(把 user_id 当 tenant_id 写进名单,或反过来)
闸对该主体永远判不中,现象是「明明加了名单还是没生效」却查不出根因(contract test
钉死这条)。

超管两种发放方式:
  ① 已有账号 → 按判据把其 tenant_id(有租户)或 user_id(无租户)加进 allowlist。
  ② 账号不存在 → 任意用户名直接建号(自由邀请制,不强制邮箱;是邮箱则顺手落
    users.email)。密码可超管自定义或留空随机,只在本次响应回显,建完自动进名单。

名单存取全部经 services/platform_settings/store 现有 API;platform_setting_allowlist
表的 created_at(store 不暴露)直接只读查一次,不碰 store.py 内部实现。与 /ai、/dms
邀请同构,仅闸键、授权入口发 erp 门、审计 action/notes 口径(erp_portal)不同。
"""

from __future__ import annotations

import logging
import secrets
import string

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.feature_flags import ERP_PORTAL_KEY
from core.route_helpers import _check_password_strength, _log_op, _require_super_admin
from services.accounting_engagement import flags as engagement_flags
from services.accounting_engagement import invitations as engagement_invitations
from services.accounting_engagement.errors import (
    FIRM_INACTIVE,
    NOT_ACTIVE,
    PRIMARY_EXISTS,
    EngagementError,
)
from services.auth.account_provision import resolve_account_identifier
from services.auth.entrance import ERP
from services.auth.entrance_store import grant_entrance_safe, revoke_entrance
from services.firm import store as firm_store
from services.platform_settings import store as platform_settings_store
from services.tenant.owner_users import create_owner_user

logger = logging.getLogger("mr-pilot")

router = APIRouter()

_DEFAULT_QUOTA = 100
_PASSWORD_LEN = 14
_PASSWORD_GEN_ATTEMPTS = 50


class InviteBody(BaseModel):
    username_or_email: str = Field(..., min_length=1, max_length=200)
    # 留空 = 系统随机生成;传了原样用(超管口不设强度闸)。
    password: str | None = Field(None, min_length=1, max_length=200)
    # 新闭环灰度参数；现有 Earn UI 尚未传入时继续走原邀请，不改变线上行为。
    firm_tenant_id: str | None = Field(None, min_length=1, max_length=64)


class RevokeBody(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=64)


def _subject_id(user: dict) -> str:
    """tenant-first 判据,与 erp_portal_enabled_for 完全对齐:有 tenant_id 用 tenant,
    个人套账(无 tenant)退回 user_id。唯一判据来源,不许在别处另写一份。"""
    tenant_id = user.get("tenant_id")
    return str(tenant_id) if tenant_id else str(user["id"])


def _generate_temp_password() -> str:
    """随机一次性密码,拒绝采样直到过 _check_password_strength(与站内建号同一把尺子)。"""
    alphabet = string.ascii_letters + string.digits
    for _ in range(_PASSWORD_GEN_ATTEMPTS):
        pwd = "".join(secrets.choice(alphabet) for _ in range(_PASSWORD_LEN))
        if _check_password_strength(pwd) is None:
            return pwd
    raise HTTPException(500, detail="admin.erp_password_gen_failed")


def _resolve_password(custom: str | None) -> str:
    """建号的密码来源:超管给了就原样用(超管口不设强度闸),没给才落回随机一次性密码。"""
    return custom if custom else _generate_temp_password()


def _enrich_subjects(subject_ids: list[str]) -> dict[str, dict]:
    """把 allowlist 的 subject_id(tenant_id 或 user_id)配上人类可读信息。

    先按 tenant 匹配(团队账套 · 显示 owner 的用户名/邮箱/公司名),落空再按 user 匹配
    (个人套账,无 tenant)。删号/删租户后不报错,标记 unknown 让运营看得出名单已失联。
    """
    if not subject_ids:
        return {}
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT t.id::text AS subject_id, t.name AS company_name,
                   u.username AS username, u.email AS email
            FROM tenants t
            LEFT JOIN users u ON u.id = t.owner_user_id
            WHERE t.id::text = ANY(%s)
            """,
            (list(subject_ids),),
        )
        by_tenant = {r["subject_id"]: dict(r) for r in cur.fetchall()}
        cur.execute(
            "SELECT id::text AS subject_id, username, email, company_name "
            "FROM users WHERE id::text = ANY(%s)",
            (list(subject_ids),),
        )
        by_user = {r["subject_id"]: dict(r) for r in cur.fetchall()}
    out = {}
    for sid in subject_ids:
        t = by_tenant.get(sid)
        if t:
            out[sid] = {
                "subject_type": "tenant",
                "username": t.get("username") or "",
                "email": t.get("email") or "",
                "company_name": t.get("company_name") or "",
            }
            continue
        u = by_user.get(sid)
        out[sid] = {
            "subject_type": "user" if u else "unknown",
            "username": (u or {}).get("username") or "",
            "email": (u or {}).get("email") or "",
            "company_name": (u or {}).get("company_name") or "",
        }
    return out


def _engagement_http_error(error: EngagementError) -> HTTPException:
    status_by_code = {
        FIRM_INACTIVE: 422,
        NOT_ACTIVE: 422,
        PRIMARY_EXISTS: 409,
    }
    return HTTPException(status_by_code.get(error.code, 400), detail=error.code)


@router.get("/api/admin/erp/firms")
async def erp_active_firms(request: Request):
    """Earn 可选事务所元数据；不返回客户、单据、金额或库存。"""
    _require_super_admin(request)
    with db.get_cursor_rls(bypass=True) as cur:
        rows = firm_store.list_active_profiles_for_admin(cur)
    return {
        "firms": [
            {
                "tenant_id": row["tenant_id"],
                "firm_code": row["firm_code"],
                "display_name": row["display_name"],
                "tax_id": row.get("tax_id"),
            }
            for row in rows
        ]
    }


@router.get("/api/admin/erp/overview")
async def erp_overview(request: Request):
    """闸状态(enabled/rollout)+ 邀请名单(每项配人类可读的用户/租户信息 + invited 状态)。"""
    _require_super_admin(request)
    flag = platform_settings_store.get_setting(ERP_PORTAL_KEY)
    value = (flag or {}).get("value") or {}
    rollout = value.get("rollout") if isinstance(value, dict) else None

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT user_id::text AS subject_id, created_at FROM platform_setting_allowlist "
            "WHERE setting_key = %s ORDER BY created_at",
            (ERP_PORTAL_KEY,),
        )
        rows = [dict(r) for r in cur.fetchall()]

    info_by_id = _enrich_subjects([r["subject_id"] for r in rows])
    allowlist = [
        {
            "subject_id": r["subject_id"],
            "joined_at": r["created_at"].isoformat() if r.get("created_at") else None,
            "invited": True,
            **info_by_id.get(
                r["subject_id"],
                {"subject_type": "unknown", "username": "", "email": "", "company_name": ""},
            ),
        }
        for r in rows
    ]
    return {
        "flag": {
            "enabled": bool(flag and flag.get("enabled")),
            "rollout": rollout or "allowlist",
            "updated_at": (
                flag["updated_at"].isoformat() if flag and flag.get("updated_at") else None
            ),
        },
        "allowlist": allowlist,
    }


@router.post("/api/admin/erp/invite")
async def erp_invite(request: Request, body: InviteBody):
    """已有账号 → 按 tenant-first 判据直接加名单;不存在 → 任意用户名建号后加名单。"""
    admin = _require_super_admin(request)
    try:
        identity = resolve_account_identifier(body.username_or_email)
    except ValueError as e:
        code = e.args[0] if e.args else "invalid"
        if code == "account_missing":
            raise HTTPException(400, detail="admin.erp_missing_identity") from e
        raise HTTPException(422, detail=f"admin.erp_{code}") from e

    if body.firm_tenant_id:
        if not engagement_flags.enabled_for(body.firm_tenant_id):
            raise HTTPException(404, detail="not_found")
        try:
            with db.get_cursor_rls(bypass=True, commit=True) as cur:
                invited = engagement_invitations.invite_merchant(
                    cur,
                    identity=identity,
                    firm_tenant_id=body.firm_tenant_id,
                    admin_user_id=str(admin["id"]),
                    password=body.password,
                )
        except EngagementError as error:
            raise _engagement_http_error(error) from error

        engagement = invited["engagement"]
        _log_op(
            request,
            admin,
            action="erp.engagement_invite",
            target_type="tenant",
            target_id=invited["merchant_tenant_id"],
            target_name=invited.get("username"),
            details={
                "engagement_id": engagement["id"],
                "firm_tenant_id": engagement["firm_tenant_id"],
                "status": engagement["status"],
            },
        )
        response = {
            "ok": True,
            "created_account": invited["created_account"],
            "subject_id": invited["merchant_tenant_id"],
            "username": invited.get("username"),
            "engagement": {
                "id": engagement["id"],
                "firm_tenant_id": engagement["firm_tenant_id"],
                "merchant_tenant_id": engagement["merchant_tenant_id"],
                "status": engagement["status"],
            },
        }
        if invited.get("initial_password") is not None:
            response["initial_password"] = invited["initial_password"]
        return response

    existing = db.find_user_by_username(identity["lookup_key"])
    if existing:
        subject_id = _subject_id(existing)
        platform_settings_store.add_to_allowlist(ERP_PORTAL_KEY, subject_id)
        grant_entrance_safe(
            ERP, existing.get("tenant_id"), str(admin.get("id")) if admin else None, context="erp"
        )
        _log_op(
            request,
            admin,
            action="erp.invite",
            target_type="tenant" if existing.get("tenant_id") else "user",
            target_id=subject_id,
            target_name=existing.get("username"),
        )
        return {
            "ok": True,
            "created_account": False,
            "subject_id": subject_id,
            "username": existing.get("username"),
        }

    temp_password = _resolve_password(body.password)
    username = identity["username"]
    local_part = username.split("@", 1)[0].strip() or "erp-portal"
    result = create_owner_user(
        username=username,
        password=temp_password,
        company_name=local_part,
        tenant_type="shared_api",
        monthly_quota=_DEFAULT_QUOTA,
        notes="erp_portal invite",
    )
    if not result.get("ok"):
        err = result.get("error", "create_failed")
        if err == "username_exists":
            raise HTTPException(409, detail="admin.username_exists")
        raise HTTPException(400, detail="admin.erp_create_failed")

    user_id = result["user_id"]
    tenant_id = result["tenant_id"]
    if identity["is_email"]:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET email = %s WHERE id = %s", (identity["email"], user_id))

    # 新号开箱余额 0(不随邀请发额度):老板进 ERP 门户「套餐与余额」页自助充值或订阅。
    platform_settings_store.add_to_allowlist(ERP_PORTAL_KEY, tenant_id)
    grant_entrance_safe(ERP, tenant_id, str(admin.get("id")) if admin else None, context="erp")
    _log_op(
        request,
        admin,
        action="erp.create",
        target_type="tenant",
        target_id=tenant_id,
        target_name=username,
    )
    return {
        "ok": True,
        "created_account": True,
        "subject_id": tenant_id,
        "username": username,
        "initial_password": temp_password,
    }


@router.post("/api/admin/erp/revoke")
async def erp_revoke(request: Request, body: RevokeBody):
    """从名单移除(不删账号)· 并同步摘掉 tenant_entrances 表行。

    名单(platform_setting_allowlist)是 Phase1 推导判据;tenant_entrances 显式表建成后
    是 authorized_entrances 的表侧优先源,只摘名单不摘表行,登录准入仍从表放行。两处一起
    摘才是真收回。表未建(prod 过渡期)/基建抖动 → fail-open 只 log,不阻断收回主流程。
    """
    admin = _require_super_admin(request)
    subject_id = body.subject_id.strip()
    if not subject_id:
        raise HTTPException(400, detail="admin.erp_missing_subject")

    info = _enrich_subjects([subject_id]).get(subject_id, {})
    platform_settings_store.remove_from_allowlist(ERP_PORTAL_KEY, subject_id)
    try:
        with db.get_cursor(commit=True) as cur:
            revoke_entrance(cur, subject_id, ERP)
    except Exception as e:  # noqa: BLE001 · 表未建/基建抖动不阻断收回主流程
        logger.warning("[erp] revoke_entrance skip · subject=%s: %s", subject_id, e)
    _log_op(
        request,
        admin,
        action="erp.revoke",
        target_type=info.get("subject_type", "unknown"),
        target_id=subject_id,
        target_name=info.get("username") or info.get("company_name"),
    )
    return {"ok": True}

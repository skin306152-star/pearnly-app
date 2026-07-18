# -*- coding: utf-8 -*-
"""Earn 超管 · DMS 订车入口邀请管理(dms_portal 闸的发放侧)。

MR.ERP DMS 订车入口(身份证→客户库)是邀请制:闸 dms_portal(allowlist 模式),发号/收回/
改密全在 Earn 后台。判据与发放范式照 admin_pearnly_ai_routes 一比一(相似度 >85%,复制改名
优于抽共用):core/feature_flags.dms_portal_enabled_for 同样按账套主体归属灰度——有 tenant_id
走 tenant(团队共享同一开关状态),个人套账退回 user_id。本路由是这条 tenant-first 判据的写
入口,加错 id(把 user_id 当 tenant_id 写进名单或反过来)闸对该用户永远判不中,现象是"明明
加了名单还是没生效"却查不出根因(contract test 钉死这条)。

与 /ai 邀请仅四处刻意不同:① 闸键 dms_portal;② 授权入口发 DMS 门;③ 文案口径「DMS 邀请」;
④ revoke 比 /ai 多摘一步 tenant_entrances 表行(见 dms_revoke)。其余(建号口径、一次性密码只
回显一次、reset 严格限名单内)逐字节照抄。

超管两种发放方式:① 已有账号 → 按判据把 tenant_id/user_id 加进 allowlist;② 账号不存在 →
任意用户名建号(不强制邮箱;是邮箱则顺手落 users.email),密码可超管自定义或留空随机,只在本次
响应回显(库里只存 bcrypt,不落日志/审计 details),建完自动进名单。
"""

from __future__ import annotations

import logging
import secrets
import string

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.feature_flags import DMS_PORTAL_KEY
from core.route_helpers import _check_password_strength, _log_op, _require_super_admin
from services.auth.account_provision import resolve_account_identifier
from services.auth.entrance_store import DMS, grant_entrance_safe, revoke_entrance
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


class RevokeBody(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=64)


class ResetPasswordBody(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=64)
    password: str | None = Field(None, min_length=1, max_length=200)


def _subject_id(user: dict) -> str:
    """tenant-first 判据,与 dms_portal_enabled_for 完全对齐:有 tenant_id 用 tenant,
    个人套账(无 tenant)退回 user_id。这是唯一判据来源,不许在别处另写一份。"""
    tenant_id = user.get("tenant_id")
    return str(tenant_id) if tenant_id else str(user["id"])


def _generate_temp_password() -> str:
    """随机一次性密码,拒绝采样直到过 _check_password_strength(与站内建号同一把尺子)。"""
    alphabet = string.ascii_letters + string.digits
    for _ in range(_PASSWORD_GEN_ATTEMPTS):
        pwd = "".join(secrets.choice(alphabet) for _ in range(_PASSWORD_LEN))
        if _check_password_strength(pwd) is None:
            return pwd
    raise HTTPException(500, detail="admin.dms_password_gen_failed")


def _resolve_password(custom: str | None) -> str:
    """建号/重置的密码来源:超管给了就原样用(超管口不设强度闸),没给才落回随机一次性密码。"""
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


@router.get("/api/admin/dms/overview")
async def dms_overview(request: Request):
    """闸状态(enabled/rollout)+ 邀请名单(每项配人类可读的用户/租户信息)。"""
    _require_super_admin(request)
    flag = platform_settings_store.get_setting(DMS_PORTAL_KEY)
    value = (flag or {}).get("value") or {}
    rollout = value.get("rollout") if isinstance(value, dict) else None

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT user_id::text AS subject_id, created_at FROM platform_setting_allowlist "
            "WHERE setting_key = %s ORDER BY created_at",
            (DMS_PORTAL_KEY,),
        )
        rows = [dict(r) for r in cur.fetchall()]

    info_by_id = _enrich_subjects([r["subject_id"] for r in rows])
    allowlist = [
        {
            "subject_id": r["subject_id"],
            "joined_at": r["created_at"].isoformat() if r.get("created_at") else None,
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


@router.post("/api/admin/dms/invite")
async def dms_invite(request: Request, body: InviteBody):
    """已有账号 → 按 tenant-first 判据直接加名单;不存在 → 任意用户名建号后加名单。

    标识判定/归一复用 services.auth.account_provision.resolve_account_identifier(与
    /pos 开通、/ai 邀请共口径,防多条建号路一硬一软)。
    """
    admin = _require_super_admin(request)
    try:
        identity = resolve_account_identifier(body.username_or_email)
    except ValueError as e:
        code = e.args[0] if e.args else "invalid"
        if code == "account_missing":
            raise HTTPException(400, detail="admin.dms_missing_identity") from e
        raise HTTPException(422, detail=f"admin.dms_{code}") from e

    existing = db.find_user_by_username(identity["lookup_key"])
    if existing:
        subject_id = _subject_id(existing)
        platform_settings_store.add_to_allowlist(DMS_PORTAL_KEY, subject_id)
        grant_entrance_safe(
            DMS, existing.get("tenant_id"), str(admin.get("id")) if admin else None, context="dms"
        )
        _log_op(
            request,
            admin,
            action="dms.invite",
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

    # 自由邀请制:用户名任意(不强制邮箱)。是邮箱就顺手落 users.email(supabase 侧可读),
    # 不是就只当登录名——邀请账号无自助通道,邮箱非必需。
    temp_password = _resolve_password(body.password)
    username = identity["username"]
    local_part = username.split("@", 1)[0].strip() or "dms-portal"
    result = create_owner_user(
        username=username,
        password=temp_password,
        company_name=local_part,
        tenant_type="shared_api",
        monthly_quota=_DEFAULT_QUOTA,
        notes="dms_portal invite",
    )
    if not result.get("ok"):
        err = result.get("error", "create_failed")
        if err == "username_exists":
            raise HTTPException(409, detail="admin.username_exists")
        raise HTTPException(400, detail="admin.create_failed")

    user_id = result["user_id"]
    tenant_id = result["tenant_id"]
    if identity["is_email"]:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET email = %s WHERE id = %s", (identity["email"], user_id))

    # 新号开箱余额 0(不再随邀请发额度)：老板进 /dms 门户「套餐与余额」页自助充值或订阅套餐
    # 后余额闸(get_billing_status_combined)才放行识别。发号只开门、不送钱。
    platform_settings_store.add_to_allowlist(DMS_PORTAL_KEY, tenant_id)
    grant_entrance_safe(DMS, tenant_id, str(admin.get("id")) if admin else None, context="dms")
    _log_op(
        request,
        admin,
        action="dms.create",
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


@router.post("/api/admin/dms/revoke")
async def dms_revoke(request: Request, body: RevokeBody):
    """从名单移除(不删账号)· 并同步摘掉 tenant_entrances 表行。

    比 /ai 邀请多摘一步:名单(platform_setting_allowlist)只是 Phase1 推导判据,
    tenant_entrances 显式表建成后是 authorized_entrances 的表侧优先源——只摘名单不摘
    表行,登录准入仍从表放行,名单外的账号照样能登 /dms 门。两处一起摘才是真收回。
    表未建(prod 过渡期)/基建抖动 → fail-open 只 log,不阻断收回主流程。
    """
    admin = _require_super_admin(request)
    subject_id = body.subject_id.strip()
    if not subject_id:
        raise HTTPException(400, detail="admin.dms_missing_subject")

    info = _enrich_subjects([subject_id]).get(subject_id, {})
    platform_settings_store.remove_from_allowlist(DMS_PORTAL_KEY, subject_id)
    try:
        with db.get_cursor(commit=True) as cur:
            revoke_entrance(cur, subject_id, DMS)
    except Exception as e:  # noqa: BLE001 · 表未建/基建抖动不阻断收回主流程
        logger.warning("[dms] revoke_entrance skip · subject=%s: %s", subject_id, e)
    _log_op(
        request,
        admin,
        action="dms.revoke",
        target_type=info.get("subject_type", "unknown"),
        target_id=subject_id,
        target_name=info.get("username") or info.get("company_name"),
    )
    return {"ok": True}


def _resolve_target_user(subject_id: str) -> dict | None:
    """反解 subject_id(tenant-first 判据的产物)回目标 user 行。

    subject_id 先当 tenant_id 查 tenants.owner_user_id(团队账套口径);查不到落空,
    再当 user_id 直接查(个人套账口径)。跟 _subject_id() 是同一条判据的正反两个方向,
    任何一边改了口径都要同步改这里,否则重置会打到错的账号。
    """
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT owner_user_id::text AS owner_user_id FROM tenants WHERE id::text = %s",
            (subject_id,),
        )
        row = cur.fetchone()
    owner_user_id = row.get("owner_user_id") if row else None
    if owner_user_id:
        return db.find_user_by_id(owner_user_id)
    return db.find_user_by_id(subject_id)


@router.post("/api/admin/dms/reset-password")
async def dms_reset_password(request: Request, body: ResetPasswordBody):
    """重置 DMS 邀请账号密码 —— 仅限邀请名单内主体,不复活通用超管改密能力。

    通用 /api/admin/users/{id}/reset-password 早被故意砍成 410("超管不碰客户密码":
    主站账号忘密走登录页自助流程)。DMS 是邀请制账号,登录卡不放"忘记密码",没有自助
    通道可走,所以单独开这个重置口子——但严格闸在 allowlist 名单内,一旦 subject 不在
    名单直接 404,不是把砍掉的通用能力开回来。
    """
    admin = _require_super_admin(request)
    subject_id = body.subject_id.strip()
    if not subject_id:
        raise HTTPException(400, detail="admin.dms_missing_subject")
    if not platform_settings_store.is_allowlisted(DMS_PORTAL_KEY, subject_id):
        raise HTTPException(404, detail="admin.dms_not_invited")

    new_password = _resolve_password(body.password)

    target = _resolve_target_user(subject_id)
    if not target:
        raise HTTPException(404, detail="admin.dms_subject_unknown")

    # reset_user_password 同步刷 password_changed_at → 已签发旧 JWT 全失效(铁律 v118.28.9),
    # 不许在这里手写 bcrypt+UPDATE 绕过这层。
    if not db.reset_user_password(target["id"], new_password):
        raise HTTPException(500, detail="admin.dms_reset_failed")

    _log_op(
        request,
        admin,
        action="dms.reset_password",
        target_type="tenant" if target.get("tenant_id") else "user",
        target_id=subject_id,
        target_name=target.get("username"),
    )
    return {"ok": True, "username": target.get("username"), "initial_password": new_password}

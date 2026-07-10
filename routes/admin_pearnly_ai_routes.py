# -*- coding: utf-8 -*-
"""Earn 超管 · Pearnly AI 邀请管理(Z1-b · pearnly_ai_m1 闸的发放侧)。

core/feature_flags.pearnly_ai_m1_enabled_for 按账套主体归属判定灰度:有 tenant_id 走
tenant(团队共享同一开关状态,跟 workspace_clients 其余隔离口径一致),个人套账(无
tenant)退回 user_id。本路由是这条 tenant-first 判据的唯一写入口 —— 加错 id(把
user_id 当 tenant_id 写进名单,或反过来)闸对该用户永远判不中,现象是"明明加了名单
还是没生效"却查不出根因(contract test 钉死这条)。

超管两种发放方式:
  ① 已有账号 → 按判据把其 tenant_id(有租户)或 user_id(无租户)加进 allowlist。
  ② 账号不存在(必须给邮箱)→ 复用 services/tenant/owner_users.create_owner_user 建号,
    生成一次性初始密码只在本次响应回显(库里只存 bcrypt,不落日志/审计 details),
    建完自动进名单。

名单存取全部经 services/platform_settings/store 现有 API;platform_setting_allowlist
表的 created_at(store 不暴露)直接只读查一次,不碰 store.py 内部实现。
"""

from __future__ import annotations

import logging
import secrets
import string

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.feature_flags import PEARNLY_AI_M1_KEY
from core.route_helpers import _check_password_strength, _log_op, _require_super_admin
from services.platform_settings import store as platform_settings_store
from services.tenant.owner_users import create_owner_user

logger = logging.getLogger("mr-pilot")

router = APIRouter()

_DEFAULT_QUOTA = 100
_PASSWORD_LEN = 14
_PASSWORD_GEN_ATTEMPTS = 50


class InviteBody(BaseModel):
    username_or_email: str = Field(..., min_length=1, max_length=200)


class RevokeBody(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=64)


def _subject_id(user: dict) -> str:
    """tenant-first 判据,与 pearnly_ai_m1_enabled_for 完全对齐:有 tenant_id 用 tenant,
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
    raise HTTPException(500, detail="admin.pearnly_ai_password_gen_failed")


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


@router.get("/api/admin/pearnly-ai/overview")
async def pearnly_ai_overview(request: Request):
    """闸状态(enabled/rollout)+ 邀请名单(每项配人类可读的用户/租户信息)。"""
    _require_super_admin(request)
    flag = platform_settings_store.get_setting(PEARNLY_AI_M1_KEY)
    value = (flag or {}).get("value") or {}
    rollout = value.get("rollout") if isinstance(value, dict) else None

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT user_id::text AS subject_id, created_at FROM platform_setting_allowlist "
            "WHERE setting_key = %s ORDER BY created_at",
            (PEARNLY_AI_M1_KEY,),
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


@router.post("/api/admin/pearnly-ai/invite")
async def pearnly_ai_invite(request: Request, body: InviteBody):
    """已有账号 → 按 tenant-first 判据直接加名单;不存在(须给邮箱)→ 建号后加名单。"""
    admin = _require_super_admin(request)
    raw = body.username_or_email.strip()
    if not raw:
        raise HTTPException(400, detail="admin.pearnly_ai_missing_identity")

    existing = db.find_user_by_username(raw)
    if existing:
        subject_id = _subject_id(existing)
        platform_settings_store.add_to_allowlist(PEARNLY_AI_M1_KEY, subject_id)
        _log_op(
            request,
            admin,
            action="pearnly_ai.invite",
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

    if "@" not in raw:
        raise HTTPException(422, detail="admin.pearnly_ai_needs_email_to_create")

    temp_password = _generate_temp_password()
    local_part = raw.split("@", 1)[0].strip() or "pearnly-ai"
    result = create_owner_user(
        username=raw,
        password=temp_password,
        company_name=local_part,
        tenant_type="shared_api",
        monthly_quota=_DEFAULT_QUOTA,
        notes="pearnly_ai_m1 invite",
    )
    if not result.get("ok"):
        err = result.get("error", "create_failed")
        if err == "username_exists":
            raise HTTPException(409, detail="admin.username_exists")
        raise HTTPException(400, detail="admin.create_failed")

    user_id = result["user_id"]
    tenant_id = result["tenant_id"]
    with db.get_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET email = %s WHERE id = %s", (raw, user_id))

    platform_settings_store.add_to_allowlist(PEARNLY_AI_M1_KEY, tenant_id)
    _log_op(
        request,
        admin,
        action="pearnly_ai.create",
        target_type="tenant",
        target_id=tenant_id,
        target_name=raw,
    )
    return {
        "ok": True,
        "created_account": True,
        "subject_id": tenant_id,
        "username": raw,
        "initial_password": temp_password,
    }


@router.post("/api/admin/pearnly-ai/revoke")
async def pearnly_ai_revoke(request: Request, body: RevokeBody):
    """从名单移除(不删账号)。"""
    admin = _require_super_admin(request)
    subject_id = body.subject_id.strip()
    if not subject_id:
        raise HTTPException(400, detail="admin.pearnly_ai_missing_subject")

    info = _enrich_subjects([subject_id]).get(subject_id, {})
    platform_settings_store.remove_from_allowlist(PEARNLY_AI_M1_KEY, subject_id)
    _log_op(
        request,
        admin,
        action="pearnly_ai.revoke",
        target_type=info.get("subject_type", "unknown"),
        target_id=subject_id,
        target_name=info.get("username") or info.get("company_name"),
    )
    return {"ok": True}

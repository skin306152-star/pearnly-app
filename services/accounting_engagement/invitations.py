"""Earn 发放 ERP 商户账号并建立事务所关系的原子事务。"""

from __future__ import annotations

from typing import Callable, Optional

from core.auth import hash_password
from services.accounting_engagement import flags, lifecycle
from services.accounting_engagement.errors import NOT_ACTIVE, EngagementError
from services.auth.account_provision import (
    create_owner_login_user,
    find_login_user,
    resolve_password,
)
from services.auth.entrance import ERP
from services.auth.entrance_store import grant_entrance
from services.auth.signup_core import _ensure_tenant_for_new_user

ERP_PORTAL_KEY = "erp_portal"


def invite_merchant(
    cur,
    *,
    identity: dict,
    firm_tenant_id: str,
    admin_user_id: str,
    password: Optional[str] = None,
    password_resolver: Callable[[Optional[str]], str] = resolve_password,
) -> dict:
    """复用账号、发 ERP 门并创建 pending_merchant；任一步失败由调用方整笔回滚。"""
    existing = find_login_user(cur, identity["lookup_key"])
    created_account = existing is None
    initial_password = None

    if existing:
        user_id = str(existing["id"])
        merchant_tenant_id = str(existing["tenant_id"]) if existing.get("tenant_id") else None
    else:
        initial_password = password_resolver(password)
        user_id = create_owner_login_user(
            cur,
            username=identity["username"],
            email=identity.get("email"),
            email_norm=identity.get("email_norm"),
            password_hash=hash_password(initial_password),
        )
        merchant_tenant_id = None

    if not merchant_tenant_id:
        company_name = identity["username"].split("@", 1)[0].strip() or "erp-portal"
        merchant_tenant_id = _ensure_tenant_for_new_user(
            cur,
            user_id,
            "credits",
            company_name=company_name,
            username=identity["username"],
            entry="erp",
        )
    if not merchant_tenant_id:
        raise EngagementError(NOT_ACTIVE)

    _require_active_merchant(cur, merchant_tenant_id)
    engagement = lifecycle.invite(
        cur,
        firm_tenant_id=str(firm_tenant_id),
        merchant_tenant_id=str(merchant_tenant_id),
        admin_user_id=str(admin_user_id),
    )
    _grant_erp_access(
        cur,
        merchant_tenant_id=str(merchant_tenant_id),
        admin_user_id=str(admin_user_id),
    )

    result = {
        "created_account": created_account,
        "user_id": user_id,
        "merchant_tenant_id": str(merchant_tenant_id),
        "username": identity["username"] if created_account else existing.get("username"),
        "engagement": engagement,
    }
    if initial_password is not None:
        result["initial_password"] = initial_password
    return result


def _require_active_merchant(cur, merchant_tenant_id: str) -> None:
    cur.execute(
        "SELECT 1 FROM tenants WHERE id = %s::uuid AND status = 'active' "
        "AND tenant_type_v2 IS DISTINCT FROM 'f_firm'",
        (str(merchant_tenant_id),),
    )
    if not cur.fetchone():
        raise EngagementError(NOT_ACTIVE)


def _grant_erp_access(cur, *, merchant_tenant_id: str, admin_user_id: str) -> None:
    cur.execute(
        "INSERT INTO platform_setting_allowlist (setting_key, user_id) "
        "VALUES (%s, %s::uuid) ON CONFLICT DO NOTHING",
        (ERP_PORTAL_KEY, str(merchant_tenant_id)),
    )
    cur.execute(
        "INSERT INTO platform_setting_allowlist (setting_key, user_id) "
        "VALUES (%s, %s::uuid) ON CONFLICT DO NOTHING",
        (flags.ERP_COWORK_ENGAGEMENTS_KEY, str(merchant_tenant_id)),
    )
    grant_entrance(cur, str(merchant_tenant_id), ERP, str(admin_user_id))

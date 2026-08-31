"""ERP team member provisioning and membership updates."""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional

import bcrypt

from core import db
from services.auth.account_provision import find_login_user, resolve_account_identifier
from services.authz.resolver import create_membership, set_membership_role
from services.erp.push_store import create_erp_endpoint_with_cursor
from services.erp.team_access import _ensure_role, normalize_modules


def _select_member_endpoint(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    owner_id: str,
    endpoint_id: str,
    erp_system: str,
) -> Optional[str]:
    cur.execute(
        """
        SELECT ep.id
        FROM erp_endpoints ep
        WHERE ep.id = %s AND ep.adapter = %s AND ep.enabled = TRUE
          AND (
                (ep.user_id = %s AND ep.binding_generation = 0)
             OR (%s = 'express' AND ep.tenant_id = %s AND ep.workspace_client_id = %s
                 AND ep.binding_generation > 0 AND ep.shared_scope = TRUE
                 AND ep.revoked_at IS NULL)
          )
        LIMIT 1
        """,
        (
            endpoint_id,
            erp_system,
            owner_id,
            erp_system,
            tenant_id,
            int(workspace_client_id),
        ),
    )
    row = cur.fetchone()
    return str(row["id"]) if row else None


def create_member(
    *,
    tenant_id: str,
    workspace_client_id: int,
    invited_by: str,
    account: str,
    password: str,
    modules: Iterable[str],
    erp_system: Optional[str] = None,
    erp_config: Optional[dict[str, Any]] = None,
    erp_endpoint_id: Optional[str] = None,
) -> dict[str, Any]:
    normalized = normalize_modules(modules)
    if not normalized:
        return {"error": "erp_team.modules_required"}
    try:
        identity = resolve_account_identifier(account)
    except ValueError:
        return {"error": "erp_team.account_invalid"}
    if erp_system not in (None, "mrerp", "express"):
        return {"error": "erp_team.erp_system_invalid"}
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s AND is_active = TRUE",
            (int(workspace_client_id), tenant_id),
        )
        if cur.fetchone() is None:
            return {"error": "workspace.invalid"}
        if find_login_user(cur, identity["lookup_key"]):
            return {"error": "team.username_exists"}
        endpoint_id = None
        if erp_endpoint_id and erp_system:
            endpoint_id = _select_member_endpoint(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                owner_id=invited_by,
                endpoint_id=erp_endpoint_id,
                erp_system=erp_system,
            )
            if endpoint_id is None:
                return {"error": "erp_team.endpoint_not_available"}
        elif erp_system == "mrerp" and erp_config:
            endpoint_id = create_erp_endpoint_with_cursor(
                cur,
                user_id=invited_by,
                name="MR.ERP",
                adapter="mrerp",
                config=erp_config,
                auto_push=False,
            )
        elif erp_system:
            return {"error": f"erp_team.{erp_system}_not_configured"}
        cur.execute("SELECT name FROM tenants WHERE id = %s", (tenant_id,))
        tenant = cur.fetchone() or {}
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute(
            """
            INSERT INTO users (username, email, email_normalized, password_hash, plan, is_active,
                               is_super_admin, tenant_id, role, invited_by, company_name)
            VALUES (%s, %s, %s, %s, 'credits', TRUE, FALSE, %s, 'member', %s, %s)
            RETURNING id
            """,
            (
                identity["username"],
                identity["email"],
                identity["email_norm"],
                password_hash,
                tenant_id,
                invited_by,
                tenant.get("name"),
            ),
        )
        user_id = str(cur.fetchone()["id"])
        role_key = _ensure_role(cur, tenant_id=tenant_id, actor_id=invited_by, modules=normalized)
        if not create_membership(
            cur,
            user_id=user_id,
            tenant_id=tenant_id,
            role_key=role_key,
            granted_by=invited_by,
            scope_mode="assigned",
            allow_custom=True,
            allow_owner=False,
        ):
            raise RuntimeError("ERP team membership could not be created")
        cur.execute(
            "SELECT id FROM memberships WHERE user_id = %s AND tenant_id = %s",
            (user_id, tenant_id),
        )
        membership_id = str(cur.fetchone()["id"])
        cur.execute(
            """
            INSERT INTO member_scopes (tenant_id, membership_id, workspace_client_id, assigned_by)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (membership_id, workspace_client_id) DO NOTHING
            """,
            (tenant_id, membership_id, int(workspace_client_id), invited_by),
        )
        cur.execute(
            """
            INSERT INTO erp_team_members
                (tenant_id, workspace_client_id, user_id, modules, erp_system,
                 erp_endpoint_id, invited_by)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s)
            """,
            (
                tenant_id,
                int(workspace_client_id),
                user_id,
                json.dumps(normalized),
                erp_system,
                endpoint_id,
                invited_by,
            ),
        )
    return {"ok": True, "user_id": user_id, "username": identity["username"]}


def update_member(
    *, tenant_id: str, actor_id: str, user_id: str, modules: Iterable[str], is_active: bool
) -> dict[str, Any]:
    normalized = normalize_modules(modules)
    if not normalized:
        return {"error": "erp_team.modules_required"}
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT 1 FROM erp_team_members WHERE tenant_id = %s AND user_id = %s FOR UPDATE",
            (tenant_id, user_id),
        )
        if cur.fetchone() is None:
            return {"error": "team.member_not_found"}
        role_key = _ensure_role(cur, tenant_id=tenant_id, actor_id=actor_id, modules=normalized)
        if not set_membership_role(
            cur,
            user_id=user_id,
            tenant_id=tenant_id,
            role_key=role_key,
            granted_by=actor_id,
        ):
            return {"error": "team.member_not_found"}
        cur.execute(
            "UPDATE erp_team_members SET modules = %s::jsonb, is_active = %s, "
            "updated_at = NOW() WHERE tenant_id = %s AND user_id = %s",
            (json.dumps(normalized), bool(is_active), tenant_id, user_id),
        )
        cur.execute(
            "UPDATE users SET is_active = %s WHERE tenant_id = %s AND id = %s",
            (bool(is_active), tenant_id, user_id),
        )
    return {"ok": True, "modules": list(normalized), "is_active": bool(is_active)}


def member_exists(tenant_id: str, workspace_client_id: int, user_id: str) -> bool:
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM erp_team_members WHERE tenant_id = %s AND workspace_client_id = %s "
            "AND user_id = %s",
            (tenant_id, int(workspace_client_id), user_id),
        )
        return cur.fetchone() is not None

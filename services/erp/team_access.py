"""ERP owner-to-member access, provisioning and record visibility."""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional

from fastapi import HTTPException, Request

from core import db
from services.authz.registry import ERP_CODES, PURCHASE_CODES, SALES_CODES, STOCKCARD_CODES
from services.erp.endpoint_config import strip_endpoint_for_response
from services.erp.legacy_generation import lock_endpoint_binding

PRODUCT = "product"
PURCHASE = "purchase"
SALES = "sales"
MODULES = (PRODUCT, PURCHASE, SALES)

_PURCHASE_MEMBER_CODES = frozenset(PURCHASE_CODES) - {
    "purchase.settings.manage",
    "purchase.supplier.manage",
}
_SALES_MEMBER_CODES = frozenset(SALES_CODES) - {
    "sales.product.manage",
    "sales.settings.manage",
}
_ERP_MEMBER_CODES = frozenset(ERP_CODES) - {"erp.endpoint.manage"}


def normalize_modules(raw: Iterable[str] | None) -> tuple[str, ...]:
    selected = {str(value).strip().lower() for value in (raw or ())}
    return tuple(module for module in MODULES if module in selected)


def permission_codes(modules: Iterable[str]) -> list[str]:
    selected = set(normalize_modules(modules))
    codes: set[str] = set()
    if PRODUCT in selected:
        codes.update(STOCKCARD_CODES[:1])
    if PURCHASE in selected:
        codes.update(_PURCHASE_MEMBER_CODES)
        codes.add("intake.upload")
    if SALES in selected:
        codes.update(_SALES_MEMBER_CODES)
        codes.add("intake.upload")
    if selected & {PURCHASE, SALES}:
        codes.update(_ERP_MEMBER_CODES)
    return sorted(codes)


def _role_key(modules: Iterable[str]) -> str:
    selected = set(normalize_modules(modules))
    mask = "".join(
        code
        for module, code in ((PRODUCT, "g"), (PURCHASE, "p"), (SALES, "s"))
        if module in selected
    )
    return f"custom:erp-team-{mask}"


def _ensure_role(cur, *, tenant_id: str, actor_id: str, modules: Iterable[str]) -> str:
    normalized = normalize_modules(modules)
    key = _role_key(normalized)
    label = "ERP · " + " + ".join(
        {PRODUCT: "Goods", PURCHASE: "Purchase", SALES: "Sales"}[module] for module in normalized
    )
    cur.execute(
        """
        INSERT INTO roles (name, key, display_name, permissions, is_system, is_active,
                           version, tenant_id, created_by)
        VALUES (%s, %s, %s, %s::jsonb, FALSE, TRUE, 0, %s, %s)
        ON CONFLICT (tenant_id, key) WHERE tenant_id IS NOT NULL DO UPDATE
        SET display_name = EXCLUDED.display_name,
            permissions = EXCLUDED.permissions,
            is_active = TRUE,
            version = roles.version + 1
        RETURNING key
        """,
        (
            f"custom:{tenant_id}:erp-team-{key.rsplit('-', 1)[-1]}",
            key,
            label,
            json.dumps(permission_codes(normalized)),
            tenant_id,
            actor_id,
        ),
    )
    return str(cur.fetchone()["key"])


def _role_and_profile(cur, tenant_id: str, user_id: str) -> Optional[dict[str, Any]]:
    cur.execute(
        """
        SELECT r.key AS role_key, m.status AS membership_status,
               etm.workspace_client_id, etm.modules, etm.erp_system,
               etm.is_active AS team_active
        FROM memberships m
        JOIN roles r ON r.id = m.role_id
        LEFT JOIN erp_team_members etm
          ON etm.user_id = m.user_id AND etm.tenant_id = m.tenant_id
        WHERE m.tenant_id = %s AND m.user_id = %s
        LIMIT 1
        """,
        (tenant_id, user_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def access_for_user(tenant_id: str, user_id: str) -> Optional[dict[str, Any]]:
    with db.get_cursor() as cur:
        row = _role_and_profile(cur, str(tenant_id), str(user_id))
    if not row or row.get("membership_status") != "active":
        return None
    if row.get("role_key") == "owner":
        return {
            "is_owner": True,
            "is_active": True,
            "modules": list(MODULES),
            "workspace_client_id": None,
            "erp_system": None,
        }
    if not str(row.get("role_key") or "").startswith("custom:erp-team-"):
        return None
    if not row.get("team_active"):
        return None
    return {
        "is_owner": False,
        "is_active": True,
        "modules": list(normalize_modules(row.get("modules") or [])),
        "workspace_client_id": row.get("workspace_client_id"),
        "erp_system": row.get("erp_system"),
    }


def login_allowed(user: dict) -> bool:
    if user.get("is_super_admin"):
        return True
    if str(user.get("role") or "").lower() == "owner":
        return bool(user.get("is_active", True))
    tenant_id = user.get("tenant_id")
    user_id = user.get("id")
    if not tenant_id or not user_id or not user.get("is_active", True):
        return False
    return access_for_user(str(tenant_id), str(user_id)) is not None


def require_active_erp_user(user: dict) -> dict:
    if user.get("entry") == "erp" and not login_allowed(user):
        raise HTTPException(403, detail="erp_team.access_revoked")
    return user


def require_endpoint_manager(user: dict) -> None:
    if (
        user.get("entry") != "erp"
        or user.get("is_super_admin")
        or str(user.get("role") or "").lower() == "owner"
    ):
        return
    access = access_for_user(str(user.get("tenant_id") or ""), str(user.get("id") or ""))
    if access and not access.get("is_owner"):
        raise HTTPException(403, detail="erp_team.owner_required")


def _request_access(request: Request, user: dict) -> Optional[dict[str, Any]]:
    state = getattr(request, "state", None)
    cached = getattr(state, "_erp_team_access", None) if state is not None else None
    if cached and cached[0] == str(user.get("id")):
        return cached[1]
    access = access_for_user(str(user.get("tenant_id") or ""), str(user.get("id") or ""))
    if state is not None:
        setattr(state, "_erp_team_access", (str(user.get("id")), access))
    return access


def record_creator_scope(request: Request, user: Optional[dict] = None) -> Optional[str]:
    """Return the creator filter for ERP members; owners and other portals see tenant data."""
    if request is None:
        return None
    if user is None:
        from core.auth import get_current_user_from_request

        user = get_current_user_from_request(request)
    if user.get("is_super_admin") or user.get("entry") != "erp":
        return None
    if str(user.get("role") or "").lower() == "owner":
        return None
    access = _request_access(request, user)
    if not access:
        raise HTTPException(403, detail="erp_team.access_revoked")
    return None if access["is_owner"] else str(user["id"])


def tenant_record_scope(request: Request, user: dict) -> Optional[str]:
    """Keep owner reads tenant-wide while forcing ERP members onto user-owned rows."""
    return None if record_creator_scope(request, user) else str(user.get("tenant_id") or "")


def assert_owned_histories(request: Request, user: dict, history_ids: Iterable[str]) -> None:
    creator = record_creator_scope(request, user)
    ids = list(dict.fromkeys(str(value) for value in history_ids if value))
    if not creator or not ids:
        return
    try:
        with db.get_cursor_rls(tenant_id=str(user.get("tenant_id") or ""), user_id=creator) as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM ocr_history "
                "WHERE id = ANY(%s::uuid[]) AND user_id = %s::uuid",
                (ids, creator),
            )
            found = int(cur.fetchone()["n"])
    except Exception:
        raise HTTPException(404, detail="history.not_found") from None
    if found != len(ids):
        raise HTTPException(404, detail="history.not_found")


def mode_allowed(tenant_id: str, user_id: str, mode: str) -> bool:
    access = access_for_user(str(tenant_id), str(user_id))
    if not access:
        return False
    required = PURCHASE if mode == "purchase" else SALES if mode == "sales" else None
    return required is not None and required in access["modules"]


def line_modes(tenant_id: str, user_id: str) -> tuple[str, ...]:
    access = access_for_user(str(tenant_id), str(user_id))
    if not access:
        return ()
    return tuple(mode for mode in (PURCHASE, SALES) if mode in access["modules"])


def binding_line_modes(binding: dict) -> tuple[str, ...]:
    return line_modes(str(binding["tenant_id"]), str(binding["user_id"]))


def list_members(tenant_id: str, workspace_client_id: int) -> list[dict[str, Any]]:
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.username, u.is_active, u.last_login_at, u.created_at,
                   etm.modules, etm.erp_system, etm.is_active AS team_active,
                   ep.id AS endpoint_id, ep.name AS endpoint_name,
                   (ep.config->>'username_enc' IS NOT NULL) AS erp_credentials_set,
                   lb.display_name AS line_display_name, lb.bound_at AS line_bound_at
            FROM erp_team_members etm
            JOIN users u ON u.id = etm.user_id
            LEFT JOIN erp_endpoints ep ON ep.id = etm.erp_endpoint_id
            LEFT JOIN line_erp_bindings lb ON lb.user_id = etm.user_id
            WHERE etm.tenant_id = %s AND etm.workspace_client_id = %s
            ORDER BY etm.created_at DESC
            """,
            (tenant_id, int(workspace_client_id)),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [
        {
            "id": str(row["id"]),
            "username": row.get("username") or "",
            "modules": list(normalize_modules(row.get("modules") or [])),
            "erp_system": row.get("erp_system"),
            "erp_endpoint_id": str(row["endpoint_id"]) if row.get("endpoint_id") else None,
            "erp_endpoint_name": row.get("endpoint_name"),
            "erp_connected": bool(row.get("endpoint_id") or row.get("erp_system") == "express"),
            "is_active": bool(row.get("is_active") and row.get("team_active")),
            "last_login_at": row["last_login_at"].isoformat() if row.get("last_login_at") else None,
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "line": {
                "bound": bool(row.get("line_bound_at")),
                "display_name": row.get("line_display_name"),
                "bound_at": row["line_bound_at"].isoformat() if row.get("line_bound_at") else None,
            },
        }
        for row in rows
    ]


def owner_endpoint_options(
    tenant_id: str, workspace_client_id: int, owner_id: str
) -> list[dict[str, Any]]:
    """Return configured owner/workspace push targets without credentials."""
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT ep.id, ep.name, ep.adapter, ep.enabled, ep.is_default,
                   ep.binding_generation,
                   CASE WHEN ep.binding_generation > 0 THEN 'workspace' ELSE 'owner' END AS scope
            FROM erp_endpoints ep
            WHERE ep.enabled = TRUE
              AND (
                    (ep.user_id = %s AND ep.binding_generation = 0
                     AND ep.adapter IN ('mrerp', 'express'))
                 OR (ep.tenant_id = %s AND ep.workspace_client_id = %s
                     AND ep.binding_generation > 0 AND ep.shared_scope = TRUE
                     AND ep.adapter = 'express' AND ep.revoked_at IS NULL)
              )
            ORDER BY ep.adapter, ep.is_default DESC, ep.created_at, ep.id
            """,
            (owner_id, tenant_id, int(workspace_client_id)),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [
        {
            "id": str(row["id"]),
            "name": row.get("name") or row.get("adapter") or "ERP",
            "adapter": row.get("adapter"),
            "is_default": bool(row.get("is_default")),
            "scope": row.get("scope"),
        }
        for row in rows
    ]


def _assigned_endpoint_row(
    cur, *, tenant_id: str, user_id: str, endpoint_id: Optional[str] = None
) -> Optional[dict[str, Any]]:
    endpoint_filter = "AND ep.id = %s" if endpoint_id else ""
    params: list[Any] = [tenant_id, user_id]
    if endpoint_id:
        params.append(endpoint_id)
    cur.execute(
        """
        SELECT ep.id, ep.name, ep.adapter, ep.config, ep.is_default, ep.auto_push,
               ep.enabled, ep.last_used_at, ep.last_status, ep.success_count,
               ep.failure_count, ep.created_at, ep.updated_at, ep.user_id,
               ep.tenant_id, ep.workspace_client_id, ep.shared_scope,
               ep.binding_generation, ep.bound_account_set, ep.bound_profile_key,
               ep.live_account_set, ep.live_profile_key, ep.agent_last_seen_at,
               ep.agent_version, ep.revoked_at,
               etm.workspace_client_id AS assigned_workspace_client_id,
               clock_timestamp() AS server_now
        FROM erp_team_members etm
        JOIN erp_endpoints ep ON ep.id = etm.erp_endpoint_id
        JOIN users owner_user ON owner_user.id = etm.invited_by
        WHERE etm.tenant_id = %s AND etm.user_id = %s AND etm.is_active = TRUE
          AND owner_user.tenant_id = etm.tenant_id AND owner_user.is_active = TRUE
          AND ep.adapter = etm.erp_system
          AND (
                (ep.binding_generation = 0 AND ep.user_id = etm.invited_by)
             OR (ep.binding_generation > 0 AND ep.adapter = 'express'
                 AND ep.tenant_id = etm.tenant_id
                 AND ep.workspace_client_id = etm.workspace_client_id
                 AND ep.shared_scope = TRUE AND ep.revoked_at IS NULL)
          )
        """ + endpoint_filter + " ORDER BY ep.is_default DESC, ep.created_at LIMIT 1",
        tuple(params),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def assigned_endpoint_items(tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    with db.get_cursor() as cur:
        row = _assigned_endpoint_row(cur, tenant_id=tenant_id, user_id=user_id)
    if not row:
        return []
    item = strip_endpoint_for_response(row)
    for key in ("bound_profile_key", "live_profile_key"):
        item.pop(key, None)
    if str(row.get("adapter") or "").lower() == "express":
        from services.erp.shared_express_store import safe_endpoint_dto

        safe = safe_endpoint_dto(row, row.get("server_now"))
        item.update(safe)
        item.pop("config", None)
    item["is_default"] = True
    item["read_only"] = True
    return [item]


def assigned_push_endpoint(
    user: dict, endpoint_id: Optional[str] = None
) -> Optional[dict[str, Any]]:
    if user.get("entry") != "erp" or str(user.get("role") or "").lower() == "owner":
        return None
    access = access_for_user(str(user.get("tenant_id") or ""), str(user.get("id") or ""))
    if not access or access.get("is_owner"):
        return None
    with db.get_cursor() as cur:
        return _assigned_endpoint_row(
            cur,
            tenant_id=str(user["tenant_id"]),
            user_id=str(user["id"]),
            endpoint_id=endpoint_id,
        )


def assigned_endpoint_for_request(
    user: dict, requested_endpoint_id: Optional[str]
) -> Optional[dict[str, Any]]:
    """Resolve an ERP member's immutable owner-assigned push target."""
    if user.get("entry") != "erp" or str(user.get("role") or "").lower() == "owner":
        return None
    access = access_for_user(str(user.get("tenant_id") or ""), str(user.get("id") or ""))
    if not access or access.get("is_owner"):
        raise HTTPException(403, detail="erp_team.access_revoked")
    endpoint = assigned_push_endpoint(user)
    if endpoint is None:
        raise HTTPException(400, detail="erp.no_default_endpoint")
    assigned_id = str(endpoint["id"])
    if requested_endpoint_id and str(requested_endpoint_id) != assigned_id:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    return endpoint


def assigned_endpoint_owner(user: dict, endpoint_id: str) -> Optional[str]:
    endpoint = assigned_push_endpoint(user, endpoint_id)
    return str(endpoint["user_id"]) if endpoint else None


def insert_assigned_push_log(
    *,
    user: dict,
    endpoint_id: str,
    history_id: str,
    invoice_no: Optional[str],
    seller_name: Optional[str],
    total_amount: Optional[float],
    status: str,
    http_status: Optional[int],
    request_body: Optional[dict],
    response_body: Optional[str],
    error_msg: Optional[str],
    attempt: int,
    elapsed_ms: int,
    trigger: str = "manual",
) -> Optional[str]:
    """Write a member-owned log after rechecking the owner endpoint assignment."""
    with db.get_cursor(commit=True) as cur:
        lock_endpoint_binding(cur, endpoint_id)
        endpoint = _assigned_endpoint_row(
            cur,
            tenant_id=str(user.get("tenant_id") or ""),
            user_id=str(user.get("id") or ""),
            endpoint_id=endpoint_id,
        )
        if endpoint is None:
            return None
        cur.execute(
            """
            INSERT INTO erp_push_logs (
                user_id, endpoint_id, history_id, invoice_no, seller_name,
                total_amount, status, http_status, request_body, response_body,
                error_msg, attempt, elapsed_ms, trigger
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                str(user["id"]),
                endpoint_id,
                history_id,
                invoice_no,
                seller_name,
                total_amount,
                status,
                http_status,
                json.dumps(request_body) if request_body else None,
                response_body,
                error_msg,
                int(attempt),
                int(elapsed_ms or 0),
                trigger,
            ),
        )
        row = cur.fetchone()
        return str(row["id"]) if row else None

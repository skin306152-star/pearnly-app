"""Validation shared by workspace creation and legacy endpoint binding."""

from __future__ import annotations

from typing import Optional

from core import db
from services.erp.legacy_generation import lock_endpoint_binding


def lock_bindable_erp_endpoint(
    cur,
    endpoint_id: Optional[str],
    user_id: str,
    tenant_id: Optional[str],
    *,
    exclude_workspace_client_id: Optional[int] = None,
) -> bool:
    """Lock an actor-owned legacy endpoint and reject an active competing binding."""
    if not endpoint_id:
        return True
    cur.execute(
        """
        SELECT id, user_id, tenant_id, adapter, binding_generation
        FROM erp_endpoints
        WHERE id = %s
        FOR UPDATE
        """,
        (str(endpoint_id).strip(),),
    )
    endpoint = cur.fetchone()
    if not endpoint:
        return False
    if int(endpoint.get("binding_generation") or 0) != 0:
        return False
    if str(endpoint.get("user_id") or "") != str(user_id):
        return False
    endpoint_tenant = endpoint.get("tenant_id")
    if tenant_id:
        if endpoint_tenant is not None and str(endpoint_tenant) != str(tenant_id):
            return False
    elif endpoint_tenant is not None:
        return False
    params: list = [str(endpoint_id).strip()]
    occupancy_sql = (
        "SELECT id FROM workspace_clients WHERE erp_endpoint_id = %s " "AND is_active = TRUE"
    )
    if exclude_workspace_client_id is not None:
        occupancy_sql += " AND id <> %s"
        params.append(int(exclude_workspace_client_id))
    occupancy_sql += " ORDER BY id LIMIT 1 FOR UPDATE"
    cur.execute(occupancy_sql, tuple(params))
    return cur.fetchone() is None


def lock_workspace_client(
    cur, workspace_client_id: int, user_id: str, tenant_id: Optional[str]
) -> bool:
    """Lock an active workspace before the endpoint lock."""
    if tenant_id:
        cur.execute(
            "SELECT id FROM workspace_clients WHERE id = %s AND tenant_id = %s "
            "AND is_active = TRUE FOR UPDATE",
            (int(workspace_client_id), tenant_id),
        )
    else:
        cur.execute(
            "SELECT id FROM workspace_clients WHERE id = %s AND user_id = %s "
            "AND tenant_id IS NULL AND is_active = TRUE FOR UPDATE",
            (int(workspace_client_id), str(user_id)),
        )
    return cur.fetchone() is not None


def bind_workspace_endpoint(
    workspace_client_id: int,
    erp_endpoint_id: Optional[str],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """Bind an existing legacy endpoint after locking workspace then endpoint."""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            lock_endpoint_binding(cur, erp_endpoint_id)
            if not lock_workspace_client(cur, workspace_client_id, str(user_id), tenant_id):
                return False
            if not lock_bindable_erp_endpoint(
                cur,
                erp_endpoint_id,
                str(user_id),
                tenant_id,
                exclude_workspace_client_id=workspace_client_id,
            ):
                return False
            value = str(erp_endpoint_id).strip() if erp_endpoint_id else None
            if tenant_id:
                cur.execute(
                    "UPDATE workspace_clients SET erp_endpoint_id = %s, updated_at = NOW() "
                    "WHERE id = %s AND tenant_id = %s",
                    (value, int(workspace_client_id), tenant_id),
                )
            else:
                cur.execute(
                    "UPDATE workspace_clients SET erp_endpoint_id = %s, updated_at = NOW() "
                    "WHERE id = %s AND user_id = %s AND tenant_id IS NULL",
                    (value, int(workspace_client_id), str(user_id)),
                )
            return cur.rowcount > 0
    except Exception:
        return False

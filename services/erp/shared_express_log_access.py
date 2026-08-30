"""Managed-only reader scope for shared Express push logs."""

from __future__ import annotations

from typing import Optional


def enable_managed_log_reader(
    cur,
    *,
    user_id: str,
    tenant_id: Optional[str],
    workspace_client_id: Optional[int],
) -> bool:
    if not tenant_id or workspace_client_id is None:
        return False

    from services.authz.resolver import resolve
    from services.erp.shared_express_schema import enable_shared_express_select

    cur.execute("SET LOCAL app.current_user_id = %s", (str(user_id),))
    cur.execute("SET LOCAL app.current_workspace_id = %s", (str(workspace_client_id),))
    authz = resolve({"id": user_id, "tenant_id": tenant_id}, cur=cur)
    if (
        authz.membership_id is None
        or not authz.has("erp.log.view")
        or not authz.allows_workspace(workspace_client_id)
    ):
        return False
    return enable_shared_express_select(cur, str(tenant_id), workspace_client_id)


def log_reader_predicate(
    alias: str,
    *,
    user_id: str,
    tenant_id: Optional[str],
    workspace_client_id: Optional[int],
    shared: bool,
) -> tuple[str, tuple]:
    own = f"{alias}.user_id = %s"
    if not shared or not tenant_id or workspace_client_id is None:
        return own, (user_id,)
    managed = (
        f"{alias}.tenant_id = %s AND {alias}.workspace_client_id = %s "
        "AND EXISTS (SELECT 1 FROM erp_endpoints managed_endpoint "
        f"WHERE managed_endpoint.id = {alias}.endpoint_id "
        "AND managed_endpoint.tenant_id = %s "
        "AND managed_endpoint.workspace_client_id = %s "
        "AND managed_endpoint.adapter = 'express' "
        "AND managed_endpoint.shared_scope = TRUE "
        "AND managed_endpoint.binding_generation > 0)"
    )
    return f"({own} OR ({managed}))", (
        user_id,
        str(tenant_id),
        int(workspace_client_id),
        str(tenant_id),
        int(workspace_client_id),
    )


__all__ = ["enable_managed_log_reader", "log_reader_predicate"]

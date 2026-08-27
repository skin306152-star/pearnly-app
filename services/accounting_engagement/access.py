"""关系参与方与 workspace 归属校验。"""

from __future__ import annotations

from services.accounting_engagement.errors import FORBIDDEN, WORKSPACE_MISMATCH, EngagementError


def require_participant(row: dict, tenant_id: str) -> str:
    tenant = str(tenant_id)
    if str(row.get("firm_tenant_id")) == tenant:
        return "firm"
    if str(row.get("merchant_tenant_id")) == tenant:
        return "merchant"
    raise EngagementError(FORBIDDEN)


def require_workspace_owner(cur, *, tenant_id: str, workspace_client_id: int) -> None:
    cur.execute(
        "SELECT 1 FROM workspace_clients " "WHERE id = %s AND tenant_id = %s::uuid AND is_active",
        (int(workspace_client_id), str(tenant_id)),
    )
    if not cur.fetchone():
        raise EngagementError(WORKSPACE_MISMATCH)


def require_active_firm(cur, *, tenant_id: str) -> None:
    cur.execute(
        "SELECT 1 FROM accounting_firm_profiles p "
        "JOIN tenants t ON t.id = p.tenant_id "
        "WHERE p.tenant_id = %s::uuid AND p.status = 'active' AND t.status = 'active'",
        (str(tenant_id),),
    )
    if not cur.fetchone():
        from services.accounting_engagement.errors import FIRM_INACTIVE

        raise EngagementError(FIRM_INACTIVE)

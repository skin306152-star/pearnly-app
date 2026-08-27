"""accounting_engagements 事务级 DAL。"""

from __future__ import annotations

from typing import Optional

_COLUMNS = """
    id::text, firm_tenant_id::text, firm_workspace_client_id,
    merchant_tenant_id::text, merchant_workspace_client_id,
    status, is_primary, merchant_accepted_at, firm_accepted_at,
    active_from, ended_at, created_by_admin_user_id::text, created_at, updated_at
"""


def create_pending(
    cur,
    *,
    firm_tenant_id: str,
    merchant_tenant_id: str,
    created_by_admin_user_id: Optional[str],
) -> dict:
    cur.execute(
        f"""
        INSERT INTO accounting_engagements (
            firm_tenant_id, merchant_tenant_id, created_by_admin_user_id
        )
        SELECT p.tenant_id, m.id, %s::uuid
        FROM accounting_firm_profiles p
        JOIN tenants f ON f.id = p.tenant_id
        JOIN tenants m ON m.id = %s::uuid
        WHERE p.tenant_id = %s::uuid
          AND p.status = 'active' AND f.status = 'active' AND m.status = 'active'
          AND m.tenant_type_v2 IS DISTINCT FROM 'f_firm'
        ON CONFLICT (merchant_tenant_id)
            WHERE is_primary AND status <> 'ended'
        DO NOTHING
        RETURNING {_COLUMNS}
        """,
        (created_by_admin_user_id, str(merchant_tenant_id), str(firm_tenant_id)),
    )
    row = cur.fetchone()
    return dict(row) if row else {}


def get_by_id(cur, *, engagement_id: str) -> Optional[dict]:
    cur.execute(
        f"SELECT {_COLUMNS} FROM accounting_engagements WHERE id = %s::uuid",
        (str(engagement_id),),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def get_open_for_merchant(cur, *, merchant_tenant_id: str) -> Optional[dict]:
    cur.execute(
        f"""
        SELECT {_COLUMNS} FROM accounting_engagements
        WHERE merchant_tenant_id = %s::uuid AND is_primary AND status <> 'ended'
        """,
        (str(merchant_tenant_id),),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_for_tenant(cur, *, tenant_id: str) -> list[dict]:
    cur.execute(
        f"""
        SELECT {_COLUMNS} FROM accounting_engagements
        WHERE firm_tenant_id = %s::uuid OR merchant_tenant_id = %s::uuid
        ORDER BY created_at DESC
        """,
        (str(tenant_id), str(tenant_id)),
    )
    return [dict(row) for row in cur.fetchall()]


def update_fields(cur, *, engagement_id: str, fields: dict) -> Optional[dict]:
    allowed = {
        "firm_workspace_client_id",
        "merchant_workspace_client_id",
        "status",
        "merchant_accepted_at",
        "firm_accepted_at",
        "active_from",
        "ended_at",
    }
    selected = [(key, value) for key, value in fields.items() if key in allowed]
    if not selected:
        return get_by_id(cur, engagement_id=engagement_id)
    assignments = ", ".join(f"{key} = %s" for key, _ in selected)
    params = [value for _, value in selected]
    params.append(str(engagement_id))
    cur.execute(
        f"""
        UPDATE accounting_engagements
        SET {assignments}, updated_at = now()
        WHERE id = %s::uuid
        RETURNING {_COLUMNS}
        """,
        params,
    )
    row = cur.fetchone()
    return dict(row) if row else None

"""关系创建与状态迁移。"""

from __future__ import annotations

from services.accounting_engagement import access, store
from services.accounting_engagement.errors import (
    FIRM_INACTIVE,
    NOT_ACTIVE,
    PRIMARY_EXISTS,
    EngagementError,
)


def invite(
    cur,
    *,
    firm_tenant_id: str,
    merchant_tenant_id: str,
    admin_user_id: str,
) -> dict:
    access.require_active_firm(cur, tenant_id=firm_tenant_id)
    existing = store.get_open_for_merchant(cur, merchant_tenant_id=merchant_tenant_id)
    if existing:
        if str(existing["firm_tenant_id"]) == str(firm_tenant_id):
            return existing
        raise EngagementError(PRIMARY_EXISTS)
    row = store.create_pending(
        cur,
        firm_tenant_id=firm_tenant_id,
        merchant_tenant_id=merchant_tenant_id,
        created_by_admin_user_id=admin_user_id,
    )
    if not row:
        existing = store.get_open_for_merchant(cur, merchant_tenant_id=merchant_tenant_id)
        if existing:
            if str(existing["firm_tenant_id"]) == str(firm_tenant_id):
                return existing
            raise EngagementError(PRIMARY_EXISTS)
        raise EngagementError(FIRM_INACTIVE)
    return row


def accept_merchant(
    cur,
    *,
    engagement_id: str,
    merchant_tenant_id: str,
    workspace_client_id: int,
) -> dict:
    row = _participant_row(cur, engagement_id, merchant_tenant_id, "merchant")
    if row.get("merchant_accepted_at") and int(row.get("merchant_workspace_client_id") or 0) == int(
        workspace_client_id
    ):
        return row
    if row["status"] not in {"pending_merchant", "pending_firm"}:
        raise EngagementError(NOT_ACTIVE)
    access.require_workspace_owner(
        cur,
        tenant_id=merchant_tenant_id,
        workspace_client_id=workspace_client_id,
    )
    return store.update_fields(
        cur,
        engagement_id=engagement_id,
        fields={
            "merchant_workspace_client_id": int(workspace_client_id),
            "merchant_accepted_at": _now_sql(cur),
            "status": "pending_firm",
        },
    )


def accept_firm(
    cur,
    *,
    engagement_id: str,
    firm_tenant_id: str,
    workspace_client_id: int,
) -> dict:
    row = _participant_row(cur, engagement_id, firm_tenant_id, "firm")
    if row["status"] == "active" and int(row.get("firm_workspace_client_id") or 0) == int(
        workspace_client_id
    ):
        return row
    if row["status"] != "pending_firm" or not row.get("merchant_accepted_at"):
        raise EngagementError(NOT_ACTIVE)
    access.require_active_firm(cur, tenant_id=firm_tenant_id)
    access.require_workspace_owner(
        cur,
        tenant_id=firm_tenant_id,
        workspace_client_id=workspace_client_id,
    )
    now = _now_sql(cur)
    result = store.update_fields(
        cur,
        engagement_id=engagement_id,
        fields={
            "firm_workspace_client_id": int(workspace_client_id),
            "firm_accepted_at": now,
            "active_from": now,
            "status": "active",
        },
    )
    if not result:
        raise EngagementError(NOT_ACTIVE)
    return result


def suspend(cur, *, engagement_id: str, tenant_id: str) -> dict:
    row = _participant_row(cur, engagement_id, tenant_id)
    if row["status"] != "active":
        raise EngagementError(NOT_ACTIVE)
    return store.update_fields(cur, engagement_id=engagement_id, fields={"status": "suspended"})


def resume(cur, *, engagement_id: str, tenant_id: str) -> dict:
    row = _participant_row(cur, engagement_id, tenant_id)
    if row["status"] != "suspended" or not _ready(row):
        raise EngagementError(NOT_ACTIVE)
    access.require_active_firm(cur, tenant_id=str(row["firm_tenant_id"]))
    return store.update_fields(cur, engagement_id=engagement_id, fields={"status": "active"})


def end(cur, *, engagement_id: str, tenant_id: str) -> dict:
    row = _participant_row(cur, engagement_id, tenant_id)
    if row["status"] == "ended":
        return row
    return store.update_fields(
        cur,
        engagement_id=engagement_id,
        fields={"status": "ended", "ended_at": _now_sql(cur)},
    )


def _participant_row(cur, engagement_id: str, tenant_id: str, expected: str | None = None) -> dict:
    row = store.get_by_id(cur, engagement_id=engagement_id)
    if not row:
        raise EngagementError(NOT_ACTIVE)
    side = access.require_participant(row, tenant_id)
    if expected and side != expected:
        raise EngagementError(NOT_ACTIVE)
    return row


def _ready(row: dict) -> bool:
    return all(
        row.get(key)
        for key in (
            "firm_workspace_client_id",
            "merchant_workspace_client_id",
            "merchant_accepted_at",
            "firm_accepted_at",
            "active_from",
        )
    )


def _now_sql(cur):
    cur.execute("SELECT now() AS value")
    row = cur.fetchone()
    return row["value"] if isinstance(row, dict) else row[0]

"""Recovery of ambiguous Cowork MR.ERP reservations without external replay."""

from __future__ import annotations

from typing import Any

from core import db
from services.erp.legacy_generation import lock_endpoint_binding

LEGACY_RESERVATION_LEASE = "cowork:mrerp"
_UNKNOWN_RESULT = "COWORK_MRERP_RESULT_UNKNOWN"


def _identity(identity: dict[str, Any]) -> tuple[str, str]:
    tenant_id = str(identity.get("tenant_id") or "").strip()
    actor_id = str(identity.get("user_id") or "").strip()
    if not tenant_id or not actor_id:
        raise ValueError("cowork identity scope is required")
    return tenant_id, actor_id


def settle_stale_legacy(cur, tenant_id: str, actor_id: str) -> int:
    cur.execute(
        "UPDATE erp_push_logs SET status = 'manual',http_status = NULL,error_msg = %s,"
        "next_retry_at = NULL,lease_owner = NULL,lease_expires_at = NULL "
        "WHERE tenant_id = %s AND user_id = %s AND status = 'retrying' "
        "AND lease_owner = %s AND lease_expires_at <= clock_timestamp() "
        "RETURNING history_id::text AS history_id",
        (_UNKNOWN_RESULT, tenant_id, actor_id, LEGACY_RESERVATION_LEASE),
    )
    history_ids = [
        str(row["history_id"])
        for row in (cur.fetchall() or [])
        if row.get("history_id") is not None
    ]
    if history_ids:
        cur.execute(
            "UPDATE ocr_history SET last_push_status = 'manual',"
            "last_pushed_at = clock_timestamp() WHERE id = ANY(%s::uuid[]) "
            "AND tenant_id = %s AND user_id = %s AND staged = FALSE",
            (history_ids, tenant_id, actor_id),
        )
    return len(history_ids)


def reconcile_stale_legacy_reservations(identity: dict[str, Any]) -> int:
    """Make expired MR.ERP outcome ambiguity honest without replaying external I/O."""
    tenant_id, actor_id = _identity(identity)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        return settle_stale_legacy(cur, tenant_id, actor_id)


def mark_legacy_intent_unknown(
    identity: dict[str, Any], endpoint: dict[str, Any], intent: dict[str, Any]
) -> bool:
    """Best-effort fallback when MR.ERP returned but its reserved log could not finalize."""
    tenant_id, actor_id = _identity(identity)
    endpoint_id = str(endpoint.get("id") or "")
    workspace_id = int(intent["history"].get("workspace_client_id") or 0)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
            lock_endpoint_binding(cur, endpoint_id)
            cur.execute(
                "UPDATE erp_push_logs SET status = 'manual',http_status = NULL,error_msg = %s,"
                "next_retry_at = NULL,lease_owner = NULL,lease_expires_at = NULL "
                "WHERE id = %s AND tenant_id = %s AND user_id = %s AND endpoint_id = %s "
                "AND history_id = %s AND workspace_client_id = %s AND status = 'retrying' "
                "AND lease_owner = %s RETURNING history_id::text AS history_id",
                (
                    _UNKNOWN_RESULT,
                    intent["log_id"],
                    tenant_id,
                    actor_id,
                    endpoint_id,
                    intent["history_id"],
                    workspace_id,
                    LEGACY_RESERVATION_LEASE,
                ),
            )
            row = cur.fetchone()
            if not row:
                return False
            cur.execute(
                "UPDATE ocr_history SET last_push_status = 'manual',"
                "last_pushed_at = clock_timestamp() WHERE id = %s AND tenant_id = %s "
                "AND user_id = %s AND workspace_client_id = %s AND staged = FALSE",
                (intent["history_id"], tenant_id, actor_id, workspace_id),
            )
            return cur.rowcount == 1
    except Exception:
        return False


__all__ = [
    "LEGACY_RESERVATION_LEASE",
    "mark_legacy_intent_unknown",
    "reconcile_stale_legacy_reservations",
    "settle_stale_legacy",
]

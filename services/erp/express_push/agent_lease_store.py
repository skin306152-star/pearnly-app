"""Atomic lease query for the local Express agent queue."""

from __future__ import annotations

from typing import Any, Iterable


def _allowed_accounts(account_sets: Iterable[object] | None) -> list[str] | None:
    if account_sets is None:
        return None
    return sorted(
        {str(value or "").strip().casefold() for value in account_sets if str(value or "").strip()}
    )


def lease_pending_rows(
    cur,
    *,
    endpoint_id: str,
    owner: str,
    max_n: int,
    account_sets: Iterable[object] | None,
    confirmed_predicate: str,
    lease_seconds: int,
) -> list[Any]:
    allowed = _allowed_accounts(account_sets)
    if allowed == []:
        return []
    account_filter = (
        "AND lower(btrim(COALESCE(request_body->>'account_set', "
        "request_body->'meta'->>'account_set', ''))) = ANY(%s)"
        if allowed is not None
        else ""
    )
    params: list[Any] = [endpoint_id]
    if allowed is not None:
        params.append(allowed)
    params.extend((max_n, owner, lease_seconds))
    cur.execute(
        f"""
        WITH due AS (
            SELECT id FROM erp_push_logs
            WHERE endpoint_id = %s AND status = 'pending'
              {account_filter}
              AND (lease_owner IS NULL
                   OR (NOT ({confirmed_predicate})
                       AND (lease_expires_at IS NULL OR lease_expires_at < NOW())))
            ORDER BY created_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        )
        UPDATE erp_push_logs l
        SET lease_owner = %s,
            lease_expires_at = NOW() + (%s * INTERVAL '1 second')
        FROM due
        WHERE l.id = due.id
        RETURNING l.id, l.history_id, l.invoice_no, l.request_body,
                  l.lease_expires_at
        """,
        tuple(params),
    )
    return list(cur.fetchall() or [])

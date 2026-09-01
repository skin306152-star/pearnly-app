"""Deduplication query used inside Cowork's push reservation transaction."""

from __future__ import annotations

from typing import Any


def prior_success(
    cur,
    endpoint_id: str,
    actor_id: str,
    history: dict[str, Any],
    account_set: str | None = None,
):
    account_sql = " AND COALESCE(request_body->>'account_set', '') = %s" if account_set else ""
    cur.execute(
        "SELECT id::text AS id,response_body FROM erp_push_logs "
        "WHERE endpoint_id = %s AND user_id = %s AND status = 'success' "
        "AND (history_id = %s OR (invoice_no = %s AND COALESCE(seller_name,'') = COALESCE(%s,''))) "
        + account_sql
        + " ORDER BY created_at DESC,id DESC LIMIT 1",
        (
            endpoint_id,
            actor_id,
            history["id"],
            history.get("invoice_no"),
            history.get("seller_name"),
            *((str(account_set),) if account_set else ()),
        ),
    )
    return cur.fetchone()


__all__ = ["prior_success"]

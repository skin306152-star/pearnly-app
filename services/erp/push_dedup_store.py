"""Account-aware ERP push deduplication queries."""

from __future__ import annotations

import logging
from typing import Any, Optional

from core import db

logger = logging.getLogger(__name__)


def has_recent_successful_push(
    history_id: str,
    endpoint_id: str,
    user_id: str,
    invoice_no: Optional[str] = None,
    seller_name: Optional[str] = None,
    account_set: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Return an earlier success for the same endpoint, account, and document."""
    if not endpoint_id:
        return None
    try:
        with db.get_cursor_rls(user_id=str(user_id)) as cur:
            account_sql = (
                " AND COALESCE(request_body->>'account_set', '') = %s" if account_set else ""
            )
            account_params = (str(account_set),) if account_set else ()
            if history_id:
                cur.execute(
                    f"""
                    SELECT id, response_body, created_at, invoice_no
                    FROM erp_push_logs
                    WHERE history_id = %s AND endpoint_id = %s
                      AND user_id = %s AND status = 'success'
                      {account_sql}
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (history_id, endpoint_id, str(user_id), *account_params),
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
            if invoice_no:
                cur.execute(
                    f"""
                    SELECT id, response_body, created_at, invoice_no
                    FROM erp_push_logs
                    WHERE endpoint_id = %s AND user_id = %s AND status = 'success'
                      AND invoice_no = %s
                      AND COALESCE(seller_name, '') = COALESCE(%s, '')
                      {account_sql}
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (endpoint_id, str(user_id), invoice_no, seller_name, *account_params),
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
            return None
    except Exception as exc:
        logger.error("has_recent_successful_push failed: %s", exc)
        return None


__all__ = ["has_recent_successful_push"]

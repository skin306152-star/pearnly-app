# -*- coding: utf-8 -*-
"""Durable accounting posting failure queue.

Business flows must not fail just because voucher generation failed, but the
failure must be visible and retryable. This module records one open failure per
source and lets the background loop retry it later.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger("mr-pilot")

_OPEN = ("pending", "retrying")
_DELAYS = (60, 300, 1800)


def _as_json(value: Optional[dict]) -> str:
    return json.dumps(value or {}, ensure_ascii=False, default=str)


def _as_dict(row) -> dict:
    return dict(row) if row else {}


def _delay_for(attempts: int) -> Optional[int]:
    idx = max(0, int(attempts or 1) - 1)
    if idx >= len(_DELAYS):
        return None
    return _DELAYS[idx]


def record_failure(
    cur,
    *,
    tenant_id: str,
    workspace_client_id,
    source_type: str,
    source_id,
    error: str,
    created_by=None,
    context: Optional[dict] = None,
    operation: str = "enqueue",
) -> None:
    """Record or refresh the open failure row inside the caller transaction."""
    if not tenant_id or not workspace_client_id or not source_type or source_id is None:
        return
    cur.execute(
        """
        INSERT INTO accounting_posting_failures
            (tenant_id, workspace_client_id, operation, source_type, source_id,
             status, attempts, last_error, context, created_by, next_retry_at)
        VALUES (%s, %s, %s, %s, %s, 'pending', 0, %s, %s::jsonb, %s,
                now() + make_interval(secs => %s))
        ON CONFLICT (tenant_id, workspace_client_id, operation, source_type, source_id)
            WHERE status IN ('pending', 'retrying')
        DO UPDATE SET
            status = 'pending',
            last_error = EXCLUDED.last_error,
            context = EXCLUDED.context,
            created_by = COALESCE(EXCLUDED.created_by, accounting_posting_failures.created_by),
            last_failed_at = now(),
            updated_at = now(),
            next_retry_at = now() + make_interval(secs => %s)
        """,
        (
            tenant_id,
            int(workspace_client_id),
            operation,
            source_type,
            str(source_id),
            str(error or "")[:2000],
            _as_json(context),
            str(created_by or ""),
            _DELAYS[0],
            _DELAYS[0],
        ),
    )


def mark_resolved(
    cur,
    *,
    tenant_id: str,
    workspace_client_id,
    source_type: str,
    source_id,
    operation: str = "enqueue",
) -> None:
    """Close any open failure for a source after posting succeeds or becomes no-op."""
    if not tenant_id or not workspace_client_id or not source_type or source_id is None:
        return
    cur.execute(
        """
        UPDATE accounting_posting_failures
           SET status = 'resolved',
               resolved_at = now(),
               next_retry_at = NULL,
               updated_at = now()
         WHERE tenant_id = %s
           AND workspace_client_id = %s
           AND operation = %s
           AND source_type = %s
           AND source_id = %s
           AND status IN ('pending', 'retrying')
        """,
        (tenant_id, int(workspace_client_id), operation, source_type, str(source_id)),
    )


def claim_due(limit: int = 20) -> list[dict]:
    """Claim due rows (multi-worker safe). Cross-tenant, so bypass=True (RLS would hide them); retry_one re-sets per-row tenant context."""
    from core import db

    with db.get_cursor_rls(bypass=True, commit=True) as cur:
        cur.execute(
            """
            UPDATE accounting_posting_failures f
               SET status = 'retrying',
                   attempts = attempts + 1,
                   updated_at = now()
             WHERE f.id IN (
                   SELECT id
                     FROM accounting_posting_failures
                    WHERE status IN ('pending', 'retrying')
                      AND tenant_id IS NOT NULL
                      AND (next_retry_at IS NULL OR next_retry_at <= now())
                    ORDER BY COALESCE(next_retry_at, first_failed_at), first_failed_at
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
             )
            RETURNING *
            """,
            (int(limit),),
        )
        return [_as_dict(r) for r in (cur.fetchall() or [])]


def _reschedule(cur, row: dict, error: str) -> None:
    delay = _delay_for(int(row.get("attempts") or 1))
    if delay is None:
        cur.execute(
            """
            UPDATE accounting_posting_failures
               SET status = 'failed',
                   last_error = %s,
                   next_retry_at = NULL,
                   last_failed_at = now(),
                   updated_at = now()
             WHERE id = %s
               AND tenant_id = %s
               AND workspace_client_id = %s
            """,
            (str(error or "")[:2000], row["id"], row["tenant_id"], int(row["workspace_client_id"])),
        )
        return
    cur.execute(
        """
        UPDATE accounting_posting_failures
           SET status = 'retrying',
               last_error = %s,
               next_retry_at = now() + make_interval(secs => %s),
               last_failed_at = now(),
               updated_at = now()
         WHERE id = %s
           AND tenant_id = %s
           AND workspace_client_id = %s
        """,
        (
            str(error or "")[:2000],
            delay,
            row["id"],
            row["tenant_id"],
            int(row["workspace_client_id"]),
        ),
    )


def retry_one(row: dict) -> bool:
    """Retry one claimed failure row in its own transaction."""
    from core import db
    from services.accounting import posting
    from services.modules import store as modules_store

    tenant_id = str(row["tenant_id"])
    ws = int(row["workspace_client_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, workspace_client_id=ws, commit=True) as cur:
        try:
            cur.execute("SAVEPOINT acct_failure_retry")
            if not modules_store.is_enabled(cur, tenant_id=tenant_id, module_key="accounting"):
                cur.execute(
                    "UPDATE accounting_posting_failures "
                    "SET status = 'resolved', resolved_at = now(), updated_at = now() "
                    "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
                    (row["id"], tenant_id, ws),
                )
                cur.execute("RELEASE SAVEPOINT acct_failure_retry")
                return True
            context: Any = row.get("context") or {}
            if isinstance(context, str):
                context = json.loads(context or "{}")
            posting.generate_for_source(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=ws,
                source_type=row["source_type"],
                source_id=row["source_id"],
                created_by=row.get("created_by") or "system",
                context=context,
            )
            cur.execute(
                "UPDATE accounting_posting_failures "
                "SET status = 'resolved', resolved_at = now(), next_retry_at = NULL, "
                "updated_at = now() WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
                (row["id"], tenant_id, ws),
            )
            cur.execute("RELEASE SAVEPOINT acct_failure_retry")
            return True
        except Exception as e:
            logger.warning(
                "accounting failure retry failed source=%s:%s: %s",
                row.get("source_type"),
                row.get("source_id"),
                e,
            )
            try:
                cur.execute("ROLLBACK TO SAVEPOINT acct_failure_retry")
            except Exception:
                pass
            _reschedule(cur, row, str(e))
            return False


def retry_due(limit: int = 20) -> dict:
    rows = claim_due(limit=limit)
    done = 0
    failed = 0
    for row in rows:
        if retry_one(row):
            done += 1
        else:
            failed += 1
    return {"claimed": len(rows), "resolved": done, "failed": failed}

# -*- coding: utf-8 -*-
"""Durable refresh requests that keep ERP collection off interactive reads."""

from __future__ import annotations

import logging
import socket
import uuid
from datetime import datetime, timezone
from typing import Any

from core import db
from services.erp.express_target_projection import normalize_express_account_key

logger = logging.getLogger(__name__)

_LEASE_SECONDS = 180
_EXPRESS_LEASE_SECONDS = 900
ENDPOINT_SCOPE_KEY = "@endpoint"


def _account_key(adapter: str, value: Any) -> str:
    raw = str(value or "").strip()
    return normalize_express_account_key(raw) if adapter == "express" else raw[:500]


def request_refresh(
    *,
    tenant_id: str,
    user_id: str,
    endpoint_id: str,
    account_set_key: str,
    adapter: str,
    reason: str = "line_new_document",
) -> dict[str, Any]:
    """Coalesce one active refresh per target without waiting for the collector."""
    tenant_id = str(tenant_id or "").strip()
    user_id = str(user_id or "").strip()
    endpoint_id = str(endpoint_id or "").strip()
    adapter = str(adapter or "").strip().lower()
    account_set_key = _account_key(adapter, account_set_key)
    if adapter not in {"mrerp", "express"} or not account_set_key:
        raise ValueError("erp.target_refresh_invalid")

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            SELECT ep.id, ep.tenant_id, ep.binding_generation,
                   owner_user.tenant_id AS owner_tenant_id
            FROM erp_endpoints ep
            LEFT JOIN users owner_user ON owner_user.id = ep.user_id
            WHERE ep.id = %s AND ep.adapter = %s AND ep.enabled = TRUE
              AND (ep.tenant_id = %s OR (ep.tenant_id IS NULL AND owner_user.tenant_id = %s))
              AND EXISTS (
                  SELECT 1 FROM users actor
                  WHERE actor.id = %s AND actor.tenant_id = %s AND actor.is_active = TRUE
              )
            FOR UPDATE OF ep
            """,
            (endpoint_id, adapter, tenant_id, tenant_id, user_id, tenant_id),
        )
        endpoint = cur.fetchone()
        if not endpoint:
            raise ValueError("erp.endpoint_not_found")
        if endpoint.get("tenant_id") is None:
            if int(endpoint.get("binding_generation") or 0) != 0:
                raise ValueError("erp.endpoint_not_found")
            cur.execute(
                "UPDATE erp_endpoints SET tenant_id = %s WHERE id = %s AND tenant_id IS NULL",
                (tenant_id, endpoint_id),
            )
        cur.execute(
            """
            UPDATE erp_target_refresh_requests
            SET status = CASE
                    WHEN requested_at > started_at THEN 'requested'
                    ELSE 'failed'
                END,
                started_at = CASE WHEN requested_at > started_at THEN NULL ELSE started_at END,
                completed_at = CASE
                    WHEN requested_at > started_at THEN NULL
                    ELSE clock_timestamp()
                END,
                error_code = CASE
                    WHEN requested_at > started_at THEN NULL
                    ELSE 'ERR_REFRESH_LEASE_EXPIRED'
                END,
                lease_owner = NULL,
                lease_expires_at = NULL, updated_at = clock_timestamp()
            WHERE tenant_id = %s AND endpoint_id = %s AND account_set_key = %s
              AND status = 'leased'
              AND (lease_expires_at IS NULL OR lease_expires_at <= clock_timestamp())
            """,
            (tenant_id, endpoint_id, account_set_key),
        )
        cur.execute(
            """
            SELECT id, status, lease_expires_at
            FROM erp_target_refresh_requests
            WHERE tenant_id = %s AND endpoint_id = %s AND account_set_key = %s
              AND status IN ('requested', 'leased')
            FOR UPDATE
            """,
            (tenant_id, endpoint_id, account_set_key),
        )
        active = cur.fetchone()
        if active and str(active.get("status") or "") == "requested":
            cur.execute(
                """
                UPDATE erp_target_refresh_requests
                SET requested_at = clock_timestamp(), reason = %s,
                    updated_at = clock_timestamp()
                WHERE id = %s
                RETURNING id, status, requested_at
                """,
                (str(reason or "line_new_document")[:80], str(active["id"])),
            )
        else:
            if active:
                cur.execute(
                    """
                    UPDATE erp_target_refresh_requests
                    SET status = 'failed', completed_at = clock_timestamp(),
                        error_code = 'ERR_REFRESH_SUPERSEDED', result_revision = NULL,
                        lease_owner = NULL, lease_expires_at = NULL,
                        updated_at = clock_timestamp()
                    WHERE id = %s AND status = 'leased'
                    """,
                    (str(active["id"]),),
                )
                if cur.rowcount != 1:
                    raise ValueError("erp.target_refresh_changed")
            cur.execute(
                """
                INSERT INTO erp_target_refresh_requests (
                    tenant_id, endpoint_id, account_set_key, adapter,
                    requested_by_user_id, reason
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, status, requested_at
                """,
                (
                    tenant_id,
                    endpoint_id,
                    account_set_key,
                    adapter,
                    user_id,
                    str(reason or "line_new_document")[:80],
                ),
            )
        row = cur.fetchone()
    return {
        "request_id": str(row["id"]),
        "status": str(row["status"]),
        "account_set_key": account_set_key,
    }


def _worker_name() -> str:
    return f"{socket.gethostname()}:{uuid.uuid4().hex[:12]}"


def _claim_mrerp(request_id: str | None = None) -> dict[str, Any] | None:
    if request_id:
        try:
            request_id = str(uuid.UUID(str(request_id)))
        except (TypeError, ValueError, AttributeError):
            return None
    owner = _worker_name()
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE erp_target_refresh_requests
            SET status = CASE
                    WHEN requested_at > started_at THEN 'requested'
                    ELSE 'failed'
                END,
                started_at = CASE WHEN requested_at > started_at THEN NULL ELSE started_at END,
                completed_at = CASE
                    WHEN requested_at > started_at THEN NULL
                    ELSE clock_timestamp()
                END,
                error_code = CASE
                    WHEN requested_at > started_at THEN NULL
                    ELSE 'ERR_REFRESH_LEASE_EXPIRED'
                END,
                lease_owner = NULL,
                lease_expires_at = NULL, updated_at = clock_timestamp()
            WHERE adapter = 'mrerp' AND status = 'leased'
              AND (lease_expires_at IS NULL OR lease_expires_at <= clock_timestamp())
              AND (%s::uuid IS NULL OR id = %s::uuid)
            """,
            (request_id, request_id),
        )
        cur.execute(
            """
            SELECT r.id, r.tenant_id, r.endpoint_id, r.account_set_key,
                   ep.user_id, ep.name, ep.adapter, ep.config, ep.enabled
            FROM erp_target_refresh_requests r
            JOIN erp_endpoints ep ON ep.id = r.endpoint_id
            WHERE r.adapter = 'mrerp' AND ep.enabled = TRUE
              AND r.status = 'requested'
              AND (%s::uuid IS NULL OR r.id = %s::uuid)
            ORDER BY r.requested_at
            LIMIT 1
            FOR UPDATE OF r SKIP LOCKED
            """,
            (request_id, request_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute(
            """
            UPDATE erp_target_refresh_requests
            SET status = 'leased', started_at = clock_timestamp(),
                lease_owner = %s,
                lease_expires_at = clock_timestamp() + (%s * interval '1 second'),
                updated_at = clock_timestamp()
            WHERE id = %s
            """,
            (owner, _LEASE_SECONDS, str(row["id"])),
        )
    return {**dict(row), "lease_owner": owner}


def process_mrerp_request(request_id: str | None = None) -> bool:
    """Claim and run one cloud collector request; callers never hold the LINE response."""
    from services.erp import mrerp_refresh_worker

    processed = False
    for _ in range(3):
        request = _claim_mrerp(request_id)
        if not request:
            return processed
        processed = True
        try:
            result = mrerp_refresh_worker.collect(request, endpoint_scope_key=ENDPOINT_SCOPE_KEY)
        except Exception:
            logger.exception("MR.ERP target refresh failed: %s", str(request["id"])[:8])
            result = {
                "ok": False,
                "error_code": "ERR_UNEXPECTED",
                "failure_scope": (
                    None
                    if str(request["account_set_key"]) == ENDPOINT_SCOPE_KEY
                    else str(request["account_set_key"])
                ),
                "observed_at": datetime.now(timezone.utc),
                "observations": [],
            }
        try:
            completed = mrerp_refresh_worker.commit(request, result)
        except ValueError as exc:
            if str(exc) != "erp.target_refresh_stale_completion":
                raise
            logger.info("Discarded stale MR.ERP target refresh: %s", str(request["id"])[:8])
            return True
        if completed is not False:
            return True
    return processed


def process_due_mrerp_requests(limit: int = 2) -> int:
    processed = 0
    for _ in range(max(1, min(int(limit or 1), 10))):
        if not process_mrerp_request():
            break
        processed += 1
    return processed


def lease_express_refresh_with_cursor(
    cur, endpoint_id: str, account_set_key: str | None = None
) -> dict[str, Any] | None:
    endpoint_id = str(endpoint_id or "").strip()
    account_set_key = normalize_express_account_key(account_set_key)
    if not endpoint_id:
        return None
    cur.execute(
        """
        SELECT id
        FROM erp_endpoints
        WHERE id = %s AND adapter = 'express' AND enabled = TRUE
        FOR UPDATE
        """,
        (endpoint_id,),
    )
    if not cur.fetchone():
        return None
    cur.execute(
        """
        UPDATE erp_target_refresh_requests
        SET status = CASE
                WHEN requested_at > started_at THEN 'requested'
                ELSE 'failed'
            END,
            started_at = CASE WHEN requested_at > started_at THEN NULL ELSE started_at END,
            completed_at = CASE
                WHEN requested_at > started_at THEN NULL
                ELSE clock_timestamp()
            END,
            error_code = CASE
                WHEN requested_at > started_at THEN NULL
                ELSE 'ERR_REFRESH_LEASE_EXPIRED'
            END,
            lease_owner = NULL,
            lease_expires_at = NULL, updated_at = clock_timestamp()
        WHERE endpoint_id = %s AND adapter = 'express' AND status = 'leased'
          AND (lease_expires_at IS NULL OR lease_expires_at <= clock_timestamp())
        """,
        (endpoint_id,),
    )
    cur.execute(
        """
        SELECT id
        FROM erp_target_refresh_requests
        WHERE endpoint_id = %s AND adapter = 'express' AND status = 'leased'
          AND lease_expires_at > clock_timestamp()
        LIMIT 1
        FOR UPDATE
        """,
        (endpoint_id,),
    )
    if cur.fetchone():
        return None
    cur.execute(
        """
        SELECT r.id, r.account_set_key, r.requested_at, r.status, r.lease_expires_at
        FROM erp_target_refresh_requests r
        JOIN erp_endpoints ep ON ep.id = r.endpoint_id
        WHERE r.endpoint_id = %s AND r.adapter = 'express' AND ep.enabled = TRUE
          AND (%s = '' OR r.account_set_key IN (%s, %s))
          AND r.status = 'requested'
        ORDER BY CASE
            WHEN r.account_set_key = %s THEN 0
            WHEN r.account_set_key = %s THEN 1
            ELSE 2 END,
            r.requested_at
        LIMIT 1
        FOR UPDATE OF r
        """,
        (
            endpoint_id,
            account_set_key,
            account_set_key,
            ENDPOINT_SCOPE_KEY,
            ENDPOINT_SCOPE_KEY,
            account_set_key,
        ),
    )
    row = cur.fetchone()
    if not row:
        return None
    cur.execute(
        """
        UPDATE erp_target_refresh_requests
        SET status = 'leased', started_at = clock_timestamp(),
            lease_owner = %s,
            lease_expires_at = clock_timestamp() + (%s * interval '1 second'),
            updated_at = clock_timestamp()
        WHERE id = %s AND status = 'requested'
        """,
        (endpoint_id, _EXPRESS_LEASE_SECONDS, str(row["id"])),
    )
    if cur.rowcount != 1:
        return None
    return {
        "request_id": str(row["id"]),
        "account_set_key": str(row["account_set_key"]),
        "scope_kind": (
            "endpoint" if str(row["account_set_key"]) == ENDPOINT_SCOPE_KEY else "account_set"
        ),
    }


def lease_express_refresh(
    endpoint_id: str, account_set_key: str | None = None
) -> dict[str, Any] | None:
    with db.get_cursor(commit=True) as cur:
        return lease_express_refresh_with_cursor(cur, endpoint_id, account_set_key)


def complete_express_refresh_with_cursor(
    cur,
    *,
    request_id: Any,
    endpoint_id: str,
    account_set_key: str,
    scope_kind: str,
    revision: int | None = None,
    error_code: str | None = None,
) -> bool:
    try:
        request_id = str(uuid.UUID(str(request_id)))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("erp.target_refresh_stale_completion") from None
    expected_key = (
        ENDPOINT_SCOPE_KEY
        if str(scope_kind or "").strip() == "endpoint"
        else normalize_express_account_key(account_set_key)
    )
    cur.execute(
        """
        UPDATE erp_target_refresh_requests
        SET status = CASE WHEN requested_at > started_at THEN 'requested' ELSE %s END,
            started_at = CASE WHEN requested_at > started_at THEN NULL ELSE started_at END,
            completed_at = CASE WHEN requested_at > started_at THEN NULL ELSE clock_timestamp() END,
            error_code = CASE WHEN requested_at > started_at THEN NULL ELSE %s END,
            result_revision = CASE WHEN requested_at > started_at THEN NULL ELSE %s END,
            lease_owner = NULL, lease_expires_at = NULL,
            updated_at = clock_timestamp()
        WHERE id = %s AND endpoint_id = %s AND adapter = 'express'
          AND account_set_key = %s AND status = 'leased'
          AND lease_owner = %s AND lease_expires_at > clock_timestamp()
        """,
        (
            "failed" if error_code else "succeeded",
            str(error_code)[:200] if error_code else None,
            int(revision) if revision is not None else None,
            request_id,
            str(endpoint_id),
            expected_key,
            str(endpoint_id),
        ),
    )
    if cur.rowcount != 1:
        raise ValueError("erp.target_refresh_stale_completion")
    return True


def refresh_status(request_id: Any, *, tenant_id: str, endpoint_id: str) -> dict[str, Any] | None:
    try:
        request_id = str(uuid.UUID(str(request_id)))
    except (TypeError, ValueError, AttributeError):
        return None
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT status, account_set_key, requested_at, completed_at, error_code,
                   result_revision
            FROM erp_target_refresh_requests
            WHERE id = %s AND tenant_id = %s AND endpoint_id = %s
            """,
            (request_id, str(tenant_id), str(endpoint_id)),
        )
        row = cur.fetchone()
    return dict(row) if row else None


__all__ = [
    "ENDPOINT_SCOPE_KEY",
    "complete_express_refresh_with_cursor",
    "lease_express_refresh",
    "lease_express_refresh_with_cursor",
    "process_due_mrerp_requests",
    "process_mrerp_request",
    "refresh_status",
    "request_refresh",
]

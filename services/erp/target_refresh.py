# -*- coding: utf-8 -*-
"""Durable refresh requests that keep ERP collection off interactive reads."""

from __future__ import annotations

import logging
import socket
import uuid
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
            SELECT id, status, lease_expires_at
            FROM erp_target_refresh_requests
            WHERE tenant_id = %s AND endpoint_id = %s AND account_set_key = %s
              AND status IN ('requested', 'leased')
            FOR UPDATE
            """,
            (tenant_id, endpoint_id, account_set_key),
        )
        active = cur.fetchone()
        if active:
            cur.execute(
                """
                UPDATE erp_target_refresh_requests
                SET requested_at = clock_timestamp(), reason = %s,
                    status = CASE
                        WHEN status = 'leased' AND lease_expires_at > clock_timestamp()
                        THEN 'leased' ELSE 'requested' END,
                    lease_owner = CASE
                        WHEN status = 'leased' AND lease_expires_at > clock_timestamp()
                        THEN lease_owner ELSE NULL END,
                    lease_expires_at = CASE
                        WHEN status = 'leased' AND lease_expires_at > clock_timestamp()
                        THEN lease_expires_at ELSE NULL END,
                    updated_at = clock_timestamp()
                WHERE id = %s
                RETURNING id, status, requested_at
                """,
                (str(reason or "line_new_document")[:80], str(active["id"])),
            )
        else:
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
            SELECT r.id, r.tenant_id, r.endpoint_id, r.account_set_key,
                   ep.user_id, ep.name, ep.adapter, ep.config, ep.enabled
            FROM erp_target_refresh_requests r
            JOIN erp_endpoints ep ON ep.id = r.endpoint_id
            WHERE r.adapter = 'mrerp' AND ep.enabled = TRUE
              AND (r.status = 'requested'
                   OR (r.status = 'leased' AND r.lease_expires_at <= clock_timestamp()))
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
            SET status = 'leased', started_at = COALESCE(started_at, clock_timestamp()),
                lease_owner = %s,
                lease_expires_at = clock_timestamp() + (%s * interval '1 second'),
                updated_at = clock_timestamp()
            WHERE id = %s
            """,
            (owner, _LEASE_SECONDS, str(row["id"])),
        )
    return {**dict(row), "lease_owner": owner}


def _finish_mrerp(
    request_id: str,
    owner: str,
    *,
    success: bool,
    error_code: str | None = None,
    revision: int | None = None,
) -> None:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE erp_target_refresh_requests
            SET status = %s, completed_at = clock_timestamp(), error_code = %s,
                result_revision = %s, lease_owner = NULL, lease_expires_at = NULL,
                updated_at = clock_timestamp()
            WHERE id = %s AND status = 'leased' AND lease_owner = %s
            """,
            (
                "succeeded" if success else "failed",
                None if success else str(error_code or "ERR_UNEXPECTED")[:200],
                revision,
                request_id,
                owner,
            ),
        )


def process_mrerp_request(request_id: str | None = None) -> bool:
    """Claim and run one cloud collector request; callers never hold the LINE response."""
    request = _claim_mrerp(request_id)
    if not request:
        return False
    request_id = str(request["id"])
    owner = str(request["lease_owner"])
    try:
        from services.erp.mrerp_target_projection import (
            refresh_mrerp_account_catalog,
            refresh_mrerp_projection,
        )

        refresh = (
            refresh_mrerp_account_catalog
            if str(request["account_set_key"]) == ENDPOINT_SCOPE_KEY
            else refresh_mrerp_projection
        )
        kwargs = {
            "tenant_id": str(request["tenant_id"]),
            "user_id": str(request["user_id"]),
            "endpoint": {
                "id": str(request["endpoint_id"]),
                "name": request.get("name"),
                "adapter": "mrerp",
                "config": request.get("config") or {},
            },
        }
        if refresh is refresh_mrerp_projection:
            kwargs["account_set_key"] = str(request["account_set_key"])
        result = refresh(**kwargs)
        success = bool(result.get("ok"))
        publication = result.get("projection") or result.get("catalog")
        projection = publication if isinstance(publication, dict) else {}
        _finish_mrerp(
            request_id,
            owner,
            success=success,
            error_code=result.get("error_code"),
            revision=int(projection.get("revision") or 0) or None,
        )
    except Exception:
        logger.exception("MR.ERP target refresh failed: %s", request_id[:8])
        _finish_mrerp(request_id, owner, success=False, error_code="ERR_UNEXPECTED")
    return True


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
        SELECT r.id, r.account_set_key, r.requested_at, r.status, r.lease_expires_at
        FROM erp_target_refresh_requests r
        JOIN erp_endpoints ep ON ep.id = r.endpoint_id
        WHERE r.endpoint_id = %s AND r.adapter = 'express' AND ep.enabled = TRUE
          AND (%s = '' OR r.account_set_key IN (%s, %s))
          AND r.status IN ('requested', 'leased')
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
    if str(row["status"]) == "requested" or row.get("lease_expires_at") is None:
        cur.execute(
            """
            UPDATE erp_target_refresh_requests
            SET status = 'leased', started_at = COALESCE(started_at, clock_timestamp()),
                lease_owner = %s,
                lease_expires_at = clock_timestamp() + (%s * interval '1 second'),
                updated_at = clock_timestamp()
            WHERE id = %s
            """,
            (endpoint_id, _EXPRESS_LEASE_SECONDS, str(row["id"])),
        )
    elif row.get("lease_expires_at") is not None:
        cur.execute(
            """
            UPDATE erp_target_refresh_requests
            SET lease_expires_at = clock_timestamp() + (%s * interval '1 second'),
                updated_at = clock_timestamp()
            WHERE id = %s
            """,
            (_EXPRESS_LEASE_SECONDS, str(row["id"])),
        )
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
        return False
    expected_key = (
        ENDPOINT_SCOPE_KEY
        if str(scope_kind or "").strip() == "endpoint"
        else normalize_express_account_key(account_set_key)
    )
    cur.execute(
        """
        UPDATE erp_target_refresh_requests
        SET status = %s, completed_at = clock_timestamp(), error_code = %s,
            result_revision = %s, lease_owner = NULL, lease_expires_at = NULL,
            updated_at = clock_timestamp()
        WHERE id = %s AND endpoint_id = %s AND adapter = 'express'
          AND account_set_key = %s AND status IN ('requested', 'leased')
        """,
        (
            "failed" if error_code else "succeeded",
            str(error_code)[:200] if error_code else None,
            int(revision) if revision is not None else None,
            request_id,
            str(endpoint_id),
            expected_key,
        ),
    )
    return cur.rowcount == 1


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

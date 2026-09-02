"""Collect MR.ERP state and publish it only for the current refresh lease."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from core import db
from services.erp import mrerp_target_projection as projection
from services.erp.target_projection_contract import normalize_projection
from services.erp.target_projection_store import (
    publish_with_cursor,
    record_refresh_state_with_cursor,
)

_STALE_COMPLETION = "erp.target_refresh_stale_completion"


def _config_fingerprint(value: Any) -> str:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            pass
    encoded = json.dumps(value or {}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def collect(request: dict[str, Any], *, endpoint_scope_key: str) -> dict[str, Any]:
    """Read third-party state without publishing any projection."""
    observed_at = datetime.now(timezone.utc)
    config = deepcopy(request.get("config") or {})
    observations: list[dict[str, Any]] = []
    requested_key = str(request["account_set_key"])
    failure_scope = None if requested_key == endpoint_scope_key else requested_key

    def failed(error_code: Any, scope: str | None = None) -> dict[str, Any]:
        return {
            "ok": False,
            "error_code": str(error_code or "ERR_UNEXPECTED"),
            "failure_scope": scope,
            "observed_at": observed_at,
            "observations": observations,
        }

    account_result = projection._run_live(projection.test_mrerp_endpoint, config)
    if not account_result.get("ok"):
        return failed(account_result.get("error_code"), failure_scope)
    account_sets = projection._account_sets(account_result.get("companies"))
    if not account_sets:
        return failed("ERR_ACCOUNT_SET_EMPTY", failure_scope)
    if requested_key == endpoint_scope_key:
        observations.append(
            projection._observation(observed_at=observed_at, account_sets=account_sets)
        )
        return {"ok": True, "observed_at": observed_at, "observations": observations}

    selected = projection._selected_account_set(account_sets, config, requested_key)
    if selected is None:
        return failed("ERR_ACCOUNT_SET_UNAVAILABLE", requested_key)
    selected_key = str(selected["source_id"])
    config.update(selected["attributes"])
    masters = {}
    for kind, loader in (
        ("products", projection.list_mrerp_products),
        ("customers", projection.list_mrerp_customers),
    ):
        result = projection._run_live(loader, config)
        if not result.get("ok"):
            return failed(result.get("error_code"), selected_key)
        masters[kind] = projection._master_rows(result.get(kind), kind=kind)
    observations.append(
        projection._observation(
            observed_at=observed_at,
            account_sets=account_sets,
            account_set_key=selected_key,
            masters=masters,
        )
    )
    return {"ok": True, "observed_at": observed_at, "observations": observations}


def _lock_current_request(cur, request: dict[str, Any]) -> dict[str, Any]:
    cur.execute(
        """
        SELECT r.id, r.requested_at, r.started_at
        FROM erp_target_refresh_requests r
        WHERE r.id = %s AND r.tenant_id = %s AND r.endpoint_id = %s
          AND r.account_set_key = %s AND r.adapter = 'mrerp'
          AND r.status = 'leased' AND r.lease_owner = %s
          AND r.lease_expires_at > clock_timestamp()
          AND NOT EXISTS (
              SELECT 1 FROM erp_target_refresh_requests newer
              WHERE newer.tenant_id = r.tenant_id AND newer.endpoint_id = r.endpoint_id
                AND newer.account_set_key = r.account_set_key AND newer.id <> r.id
                AND (newer.requested_at, newer.created_at, newer.id) >
                    (r.requested_at, r.created_at, r.id)
          )
        FOR UPDATE OF r
        """,
        (
            str(request["id"]),
            str(request["tenant_id"]),
            str(request["endpoint_id"]),
            str(request["account_set_key"]),
            str(request["lease_owner"]),
        ),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(_STALE_COMPLETION)
    return dict(row)


def _requeue_current_request(cur, request: dict[str, Any]) -> None:
    cur.execute(
        """
        UPDATE erp_target_refresh_requests
        SET status = 'requested', started_at = NULL, completed_at = NULL,
            error_code = NULL, result_revision = NULL, lease_owner = NULL,
            lease_expires_at = NULL, updated_at = clock_timestamp()
        WHERE id = %s AND status = 'leased' AND lease_owner = %s
        """,
        (str(request["id"]), str(request["lease_owner"])),
    )
    if cur.rowcount != 1:
        raise ValueError(_STALE_COMPLETION)


def commit(request: dict[str, Any], result: dict[str, Any]) -> bool:
    """Atomically fence the lease, publish observations, and finish the request."""
    request_id = str(request["id"])
    tenant_id = str(request["tenant_id"])
    endpoint_id = str(request["endpoint_id"])
    owner = str(request["lease_owner"])
    with db.get_cursor(commit=True) as cur:
        endpoint = projection.claim_endpoint_tenant_with_cursor(
            cur, tenant_id=tenant_id, endpoint_id=endpoint_id
        )
        current = _lock_current_request(cur, request)
        requested_at = current.get("requested_at")
        started_at = current.get("started_at")
        rerun_requested = bool(
            requested_at is not None and started_at is not None and requested_at > started_at
        )
        config_changed = _config_fingerprint((endpoint or {}).get("config")) != _config_fingerprint(
            request.get("config")
        )
        if rerun_requested or config_changed:
            _requeue_current_request(cur, request)
            return False
        revision = None
        for observation in result.get("observations") or []:
            publication = publish_with_cursor(
                cur,
                tenant_id=tenant_id,
                endpoint_id=endpoint_id,
                projection=normalize_projection(observation),
            )
            revision = int(publication.get("revision") or 0) or revision
        if not result.get("ok"):
            error_code = str(result.get("error_code") or "ERR_UNEXPECTED")
            record_refresh_state_with_cursor(
                cur,
                tenant_id=tenant_id,
                endpoint_id=endpoint_id,
                account_set_key=result.get("failure_scope"),
                status=projection._status_for(error_code),
                observed_at=result["observed_at"],
                collector=projection._COLLECTOR,
                error_code=error_code,
            )
            revision = None
        cur.execute(
            """
            UPDATE erp_target_refresh_requests
            SET status = %s, completed_at = clock_timestamp(), error_code = %s,
                result_revision = %s, lease_owner = NULL, lease_expires_at = NULL,
                updated_at = clock_timestamp()
            WHERE id = %s AND status = 'leased' AND lease_owner = %s
              AND lease_expires_at > clock_timestamp()
            """,
            (
                "succeeded" if result.get("ok") else "failed",
                (
                    None
                    if result.get("ok")
                    else str(result.get("error_code") or "ERR_UNEXPECTED")[:200]
                ),
                revision,
                request_id,
                owner,
            ),
        )
        if cur.rowcount != 1:
            raise ValueError(_STALE_COMPLETION)
    return True


__all__ = ["collect", "commit"]

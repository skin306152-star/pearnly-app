"""Validate that a non-default ERP target came from one exact catalog refresh."""

from __future__ import annotations

import json
import ntpath
import uuid
from typing import Any, Mapping

from core import db
from services.erp.express_target_projection import normalize_express_account_key
from services.erp.target_refresh import ENDPOINT_SCOPE_KEY

CATALOG_REFRESH_REQUIRED = "catalog_refresh_required"
CATALOG_REFRESH_INVALID = "catalog_refresh_invalid"


def _adapter(value: Any) -> str:
    return str(value or "").strip().lower()


def _account_identity(adapter: str, value: Any) -> str:
    raw = str(value or "").strip()
    return normalize_express_account_key(raw) if adapter == "express" else raw[:500]


def _root_identity(value: Any) -> str:
    return normalize_express_account_key(value)


def _account_root(account_set_key: str) -> str:
    return _root_identity(ntpath.dirname(account_set_key.rstrip("\\/")))


def _revision(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _request_id(value: Any) -> str | None:
    try:
        return str(uuid.UUID(str(value)))
    except (AttributeError, TypeError, ValueError):
        return None


def _result(
    *,
    ok: bool,
    proof_required: bool,
    reason: str,
    account_set_key: str,
    root_key: str | None,
    request_id: str | None = None,
    revision: int | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "proof_required": proof_required,
        "error_code": (
            None
            if ok
            else CATALOG_REFRESH_REQUIRED if reason == "proof_missing" else CATALOG_REFRESH_INVALID
        ),
        "reason": reason,
        "account_set_key": account_set_key,
        "root_key": root_key,
        "request_id": request_id,
        "revision": revision,
    }


def _account_sets(value: Any) -> list[Mapping[str, Any]] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return None
    if not isinstance(value, list):
        return None
    return [row for row in value if isinstance(row, Mapping)]


def _selected_account(
    rows: list[Mapping[str, Any]], adapter: str, selected_key: str
) -> Mapping[str, Any] | None:
    for row in rows:
        if _account_identity(adapter, row.get("source_id")) == selected_key:
            return row
    return None


def _validate_proof_with_cursor(
    cur,
    *,
    tenant_id: str,
    endpoint_id: str,
    adapter: str,
    selected_key: str,
    selected_root: str,
    request_id: str,
    revision: int,
) -> dict[str, Any]:
    root_result = selected_root or None
    cur.execute(
        """
        SELECT id, status, account_set_key, adapter, result_revision
        FROM erp_target_refresh_requests
        WHERE tenant_id = %s AND endpoint_id = %s AND account_set_key = %s
        ORDER BY requested_at DESC, created_at DESC, id DESC
        LIMIT 1
        """,
        (tenant_id, endpoint_id, ENDPOINT_SCOPE_KEY),
    )
    refresh = cur.fetchone()
    if not refresh:
        reason = "refresh_not_found"
    elif str(refresh.get("id") or "") != request_id:
        reason = "refresh_superseded"
    elif str(refresh.get("status") or "") != "succeeded":
        reason = "refresh_not_succeeded"
    elif str(refresh.get("account_set_key") or "") != ENDPOINT_SCOPE_KEY:
        reason = "refresh_scope_mismatch"
    elif _adapter(refresh.get("adapter")) != adapter:
        reason = "adapter_mismatch"
    elif _revision(refresh.get("result_revision")) != revision:
        reason = "revision_mismatch"
    else:
        reason = ""
    if reason:
        return _result(
            ok=False,
            proof_required=True,
            reason=reason,
            account_set_key=selected_key,
            root_key=root_result,
            request_id=request_id,
            revision=revision,
        )

    cur.execute(
        """
        SELECT s.id AS snapshot_id, s.adapter, s.account_sets,
               h.current_snapshot_id AS head_snapshot_id,
               h.current_revision AS head_revision,
               h.last_refresh_status AS head_status
        FROM erp_target_projection_snapshots s
        LEFT JOIN erp_target_projection_heads h
          ON h.tenant_id = s.tenant_id AND h.endpoint_id = s.endpoint_id
         AND h.scope_kind = s.scope_kind AND h.scope_key = s.scope_key
        WHERE s.tenant_id = %s AND s.endpoint_id = %s
          AND s.scope_kind = 'endpoint' AND s.scope_key = %s AND s.revision = %s
        """,
        (tenant_id, endpoint_id, ENDPOINT_SCOPE_KEY, revision),
    )
    snapshot = cur.fetchone()
    if not snapshot:
        reason = "snapshot_not_found"
    elif str(snapshot.get("head_status") or "") != "fresh":
        reason = "projection_not_fresh"
    elif _revision(snapshot.get("head_revision")) != revision:
        reason = "snapshot_superseded"
    elif str(snapshot.get("head_snapshot_id") or "") != str(snapshot.get("snapshot_id") or ""):
        reason = "snapshot_superseded"
    elif _adapter(snapshot.get("adapter")) != adapter:
        reason = "adapter_mismatch"
    else:
        account_sets = _account_sets(snapshot.get("account_sets"))
        if account_sets is None:
            reason = "snapshot_invalid"
        else:
            selected = _selected_account(account_sets, adapter, selected_key)
            if selected is None:
                reason = "account_not_found"
            elif selected.get("active", True) is False:
                reason = "account_inactive"
            elif adapter == "express":
                attributes = (
                    selected.get("attributes")
                    if isinstance(selected.get("attributes"), Mapping)
                    else {}
                )
                snapshot_root = _root_identity(attributes.get("root"))
                if attributes.get("writable", True) is False:
                    reason = "account_not_writable"
                else:
                    reason = "" if snapshot_root == selected_root else "root_mismatch"
            else:
                reason = ""
    if reason:
        return _result(
            ok=False,
            proof_required=True,
            reason=reason,
            account_set_key=selected_key,
            root_key=root_result,
            request_id=request_id,
            revision=revision,
        )
    return _result(
        ok=True,
        proof_required=True,
        reason="validated_snapshot",
        account_set_key=selected_key,
        root_key=root_result,
        request_id=request_id,
        revision=revision,
    )


def validate_selection(
    cur=None,
    *,
    tenant_id: str,
    user_id: str,
    endpoint_id: str,
    adapter: str,
    selected_account_set_key: Any,
    bound_account_set_key: Any,
    selected_root_key: Any = None,
    bound_root_key: Any = None,
    request_id: Any = None,
    revision: Any = None,
) -> dict[str, Any]:
    """Validate with a supplied RLS cursor, or open one read-only when omitted."""
    adapter = _adapter(adapter)
    selected_key = _account_identity(adapter, selected_account_set_key)
    bound_key = _account_identity(adapter, bound_account_set_key)
    selected_root = _root_identity(selected_root_key) if adapter == "express" else ""
    bound_root = _root_identity(bound_root_key) if adapter == "express" else ""
    if adapter == "express":
        selected_root = selected_root or _account_root(selected_key)
        expected_bound_root = bound_root or _account_root(bound_key)
        root_matches_default = (
            selected_root == expected_bound_root if expected_bound_root else not selected_root
        )
    else:
        root_matches_default = True
    is_bound_default = bool(selected_key and selected_key == bound_key and root_matches_default)
    root_result = selected_root or None

    if adapter not in {"mrerp", "express"} or not selected_key:
        return _result(
            ok=False,
            proof_required=not is_bound_default,
            reason="selection_invalid",
            account_set_key=selected_key,
            root_key=root_result,
        )
    if is_bound_default:
        return _result(
            ok=True,
            proof_required=False,
            reason="bound_default",
            account_set_key=selected_key,
            root_key=root_result,
        )
    if request_id in (None, "") or revision in (None, ""):
        return _result(
            ok=False,
            proof_required=True,
            reason="proof_missing",
            account_set_key=selected_key,
            root_key=root_result,
        )

    validated_request_id = _request_id(request_id)
    validated_revision = _revision(revision)
    if not validated_request_id or validated_revision is None:
        return _result(
            ok=False,
            proof_required=True,
            reason="proof_malformed",
            account_set_key=selected_key,
            root_key=root_result,
        )
    tenant_id = str(tenant_id or "").strip()
    user_id = str(user_id or "").strip()
    endpoint_id = str(endpoint_id or "").strip()
    if not tenant_id or not user_id or not endpoint_id:
        return _result(
            ok=False,
            proof_required=True,
            reason="context_invalid",
            account_set_key=selected_key,
            root_key=root_result,
            request_id=validated_request_id,
            revision=validated_revision,
        )

    proof_kwargs = {
        "tenant_id": tenant_id,
        "endpoint_id": endpoint_id,
        "adapter": adapter,
        "selected_key": selected_key,
        "selected_root": selected_root,
        "request_id": validated_request_id,
        "revision": validated_revision,
    }
    if cur is not None:
        return _validate_proof_with_cursor(cur, **proof_kwargs)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=False) as rls_cur:
        return _validate_proof_with_cursor(rls_cur, **proof_kwargs)


__all__ = [
    "CATALOG_REFRESH_INVALID",
    "CATALOG_REFRESH_REQUIRED",
    "validate_selection",
]

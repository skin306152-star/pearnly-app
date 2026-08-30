# -*- coding: utf-8 -*-
"""Owner-only CAS lifecycle operations for a managed Express endpoint."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException

from core import db
from services.audit.store import insert_operation_log_tx
from services.authz.resolver import resolve
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp.shared_express_lifecycle_schema import (
    enable_shared_express_lifecycle_access,
    endpoint_has_managed_activity,
    lifecycle_schema_ready,
)

logger = logging.getLogger(__name__)

_ACTIONS = {"rebind", "enable", "disable", "revoke"}
_AUDIT_ACTIONS = {f"erp.endpoint.{action}" for action in _ACTIONS}
_OPERATION_UNIQUE_CONSTRAINTS = {
    "uq_operation_logs_erp_endpoint_lifecycle_operation",
}
_WORKSPACE_UNIQUE_CONSTRAINTS = {
    "uq_erp_endpoints_shared_express_workspace",
}


class LifecycleError(Exception):
    """Expected lifecycle failure represented by a stable API error code."""

    def __init__(self, code: str, status: int = 409):
        super().__init__(code)
        self.code = code
        self.status = status


def _integrity_error_code(exc: Exception) -> Optional[str]:
    """Map only the two expected unique races; never hide unrelated DB errors."""
    constraint = str(
        getattr(getattr(exc, "diag", None), "constraint_name", None)
        or getattr(exc, "constraint_name", "")
    )
    if constraint in _OPERATION_UNIQUE_CONSTRAINTS:
        return "erp.operation_id_conflict"
    if constraint in _WORKSPACE_UNIQUE_CONSTRAINTS:
        return "erp.workspace_endpoint_conflict"
    return None


def _http(code: str, status: int = 409) -> HTTPException:
    return HTTPException(status_code=status, detail=code)


def _safe(endpoint: Dict[str, Any], *, changed: bool, operation_id: str) -> Dict[str, Any]:
    return {
        "ok": True,
        "endpoint_id": str(endpoint.get("id") or ""),
        "workspace_client_id": endpoint.get("workspace_client_id"),
        "generation": int(endpoint.get("binding_generation") or 0),
        "enabled": bool(endpoint.get("enabled")),
        "shared_scope": bool(endpoint.get("shared_scope")),
        "revoked": endpoint.get("revoked_at") is not None,
        "lifecycle": "revoked" if endpoint.get("revoked_at") is not None else "managed",
        "changed": bool(changed),
        "operation_id": operation_id,
    }


def _uuid(value: str, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise _http(code, 422 if code == "erp.operation_id_invalid" else 404) from exc


def _operation_replay(
    cur,
    *,
    tenant_id: str,
    actor_id: str,
    operation_id: str,
    endpoint_id: str,
    action: str,
    source_workspace_id: int,
    target_workspace_id: Optional[int],
    expected_generation: int,
    reason: str,
) -> Optional[Dict[str, Any]]:
    cur.execute(
        "SELECT actor_user_id, details FROM operation_logs WHERE tenant_id = %s "
        "AND details->>'operation_id' = %s "
        "AND target_type = 'erp_endpoint' AND action IN ("
        "'erp.endpoint.rebind', 'erp.endpoint.enable', 'erp.endpoint.disable', "
        "'erp.endpoint.revoke') LIMIT 1",
        (tenant_id, operation_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    row_actor = row.get("actor_user_id") if hasattr(row, "get") else row[0]
    if row_actor is not None and str(row_actor) != actor_id:
        raise LifecycleError("erp.operation_id_conflict")
    details = row.get("details") if hasattr(row, "get") else row[1]
    if not isinstance(details, dict):
        raise LifecycleError("erp.operation_id_conflict")
    expected = {
        "endpoint_id": endpoint_id,
        "action": action,
        "workspace_before": source_workspace_id,
        "target_workspace_client_id": target_workspace_id,
        "expected_generation": expected_generation,
        "reason": reason,
    }
    if any(details.get(key) != value for key, value in expected.items()):
        raise LifecycleError("erp.operation_id_conflict")
    workspace_after = details.get("workspace_after")
    response = {
        "ok": True,
        "endpoint_id": endpoint_id,
        "workspace_client_id": workspace_after,
        "generation": int(details.get("generation_after") or 0),
        "enabled": bool(details.get("enabled_after")),
        "shared_scope": bool(details.get("shared_scope_after")),
        "revoked": bool(details.get("revoked_after")),
        "lifecycle": "revoked" if details.get("revoked_after") else "managed",
        "changed": True,
        "operation_id": operation_id,
    }
    return response


def _lock_workspaces(
    cur, tenant_id: str, endpoint_id: str, source_id: int, target_id: Optional[int]
):
    ids = sorted({int(source_id), *([int(target_id)] if target_id is not None else [])})
    placeholders = ", ".join(["%s"] * len(ids))
    cur.execute(
        "SELECT id, tenant_id, is_active, erp_endpoint_id FROM workspace_clients "
        "WHERE is_active = TRUE AND tenant_id = %s AND "
        f"(id IN ({placeholders}) OR erp_endpoint_id = %s) ORDER BY id FOR UPDATE",
        (tenant_id, *ids, endpoint_id),
    )
    return {int(row["id"]): row for row in cur.fetchall()}


def change_shared_express_endpoint(
    *,
    user: Dict[str, Any],
    endpoint_id: str,
    action: str,
    operation_id: str,
    expected_generation: int,
    source_workspace_id: int,
    target_workspace_id: Optional[int] = None,
    reason: str = "",
    confirm: bool = False,
    request_ip: Optional[str] = None,
    request_ua: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply one lifecycle transition in one transaction, or raise a stable error."""
    if action not in _ACTIONS:
        raise _http("erp.lifecycle_action_invalid", 400)
    tenant_id = str(user.get("tenant_id") or "").strip()
    actor_id = str(user.get("id") or "").strip()
    if (
        not isinstance(expected_generation, int)
        or isinstance(expected_generation, bool)
        or expected_generation < 1
    ):
        raise _http("erp.endpoint_generation_invalid", 422)
    endpoint_id = _uuid(endpoint_id, "erp.endpoint_not_found")
    operation_id = _uuid(operation_id, "erp.operation_id_invalid")
    if not tenant_id or not actor_id:
        raise _http("authz.not_found", 404)
    if not lifecycle_schema_ready():
        raise _http("erp.shared_endpoint_unavailable", 503)

    try:
        with db.get_cursor_rls(
            tenant_id=tenant_id,
            user_id=actor_id,
            workspace_client_id=source_workspace_id,
            commit=True,
        ) as cur:
            lock_endpoint_binding(cur, endpoint_id)
            authz = resolve(user, cur=cur, lock=True)
            if (
                authz.membership_id is None
                or authz.role_key != "owner"
                or not authz.has("erp.endpoint.manage")
            ):
                raise _http("authz.forbidden", 403)
            cur.execute(
                "SELECT id FROM users WHERE id = %s AND tenant_id = %s "
                "AND is_active = TRUE FOR UPDATE",
                (actor_id, tenant_id),
            )
            if not cur.fetchone():
                raise _http("authz.not_found", 404)

            # The advisory lock is held before this lookup. A retried request therefore
            # observes the operation written by a competing request instead of racing it.
            replay = _operation_replay(
                cur,
                tenant_id=tenant_id,
                actor_id=actor_id,
                operation_id=operation_id,
                endpoint_id=endpoint_id,
                action=action,
                source_workspace_id=source_workspace_id,
                target_workspace_id=target_workspace_id,
                expected_generation=expected_generation,
                reason=reason,
            )
            if replay is not None:
                return replay

            if action == "revoke" and not confirm:
                raise _http("erp.revoke_confirmation_required", 400)
            if action == "rebind" and target_workspace_id is None:
                raise _http("workspace.required", 400)

            access_ok = enable_shared_express_lifecycle_access(
                cur,
                tenant_id=tenant_id,
                actor_user_id=actor_id,
                endpoint_id=endpoint_id,
                action=action,
                source_workspace_id=source_workspace_id,
                target_workspace_id=(
                    target_workspace_id
                    if action == "rebind"
                    else source_workspace_id if action in {"enable", "disable"} else None
                ),
                expected_generation=expected_generation,
            )
            if not access_ok:
                raise _http("erp.shared_endpoint_unavailable", 503)
            # Bind the canonical request id only after the helper's context checks and
            # before any UPDATE. The schema trigger reads this transaction-local value.
            cur.execute(
                "SELECT set_config('app.erp_endpoint_lifecycle_operation_id', %s, true)",
                (operation_id,),
            )

            cur.execute(
                "SELECT id, user_id, tenant_id, adapter, config, enabled, shared_scope, "
                "workspace_client_id, binding_generation, revoked_at, revoked_by, name "
                "FROM erp_endpoints WHERE id = %s FOR UPDATE",
                (endpoint_id,),
            )
            endpoint = cur.fetchone()
            if not endpoint or str(endpoint.get("tenant_id")) != tenant_id:
                raise _http("erp.endpoint_not_found", 404)
            if (
                str(endpoint.get("adapter") or "").lower() != "express"
                or not endpoint.get("shared_scope")
                or int(endpoint.get("binding_generation") or 0) < 1
            ):
                raise _http("erp.endpoint_not_found", 404)

            workspaces = _lock_workspaces(
                cur, tenant_id, endpoint_id, source_workspace_id, target_workspace_id
            )
            source = workspaces.get(int(source_workspace_id))
            if not source:
                raise _http("workspace.not_found", 404)
            duplicate_pointers = [
                int(row_id)
                for row_id, row in workspaces.items()
                if int(row_id) not in {int(source_workspace_id), int(target_workspace_id or 0)}
                and str(row.get("erp_endpoint_id") or "") == endpoint_id
            ]
            if duplicate_pointers:
                raise LifecycleError("erp.endpoint_workspace_conflict")
            if str(source.get("erp_endpoint_id") or "") != endpoint_id:
                raise _http("erp.endpoint_not_found", 404)
            if int(endpoint.get("workspace_client_id") or 0) != int(source_workspace_id):
                raise _http("erp.endpoint_not_found", 404)
            target = None
            if target_workspace_id is not None:
                target = workspaces.get(int(target_workspace_id))
                if not target:
                    raise _http("workspace.not_found", 404)
                target_owner = str(target.get("erp_endpoint_id") or "")
                if target_owner and target_owner != endpoint_id:
                    raise LifecycleError("erp.workspace_endpoint_conflict")
            if endpoint.get("revoked_at") is not None:
                raise _http("erp.endpoint_revoked", 409)
            generation = int(endpoint.get("binding_generation") or 0)
            if generation != int(expected_generation):
                raise LifecycleError("erp.endpoint_stale_generation")
            old_enabled = bool(endpoint.get("enabled"))
            if action in {"enable", "disable"} and old_enabled == (action == "enable"):
                return _safe(endpoint, changed=False, operation_id=operation_id)

            if endpoint_has_managed_activity(cur, endpoint_id):
                raise LifecycleError("erp.endpoint_busy")

            old_shared_scope = bool(endpoint.get("shared_scope"))
            old_revoked = endpoint.get("revoked_at") is not None
            old_workspace = endpoint.get("workspace_client_id")
            changed = True
            if action == "rebind":
                if int(target_workspace_id) == int(source_workspace_id):
                    if old_enabled:
                        raise LifecycleError("erp.endpoint_state_conflict")
                    changed = False
                elif old_enabled:
                    raise LifecycleError("erp.endpoint_state_conflict")
                else:
                    cur.execute(
                        "UPDATE workspace_clients SET erp_endpoint_id = NULL, updated_at = NOW() "
                        "WHERE id = %s AND tenant_id = %s AND is_active = TRUE "
                        "AND erp_endpoint_id = %s",
                        (source_workspace_id, tenant_id, endpoint_id),
                    )
                    if cur.rowcount != 1:
                        raise LifecycleError("erp.endpoint_stale_generation")
                    cur.execute(
                        "UPDATE workspace_clients SET erp_endpoint_id = %s, updated_at = NOW() "
                        "WHERE id = %s AND tenant_id = %s AND is_active = TRUE "
                        "AND (erp_endpoint_id IS NULL OR erp_endpoint_id = %s)",
                        (endpoint_id, target_workspace_id, tenant_id, endpoint_id),
                    )
                    if cur.rowcount != 1:
                        raise LifecycleError("erp.workspace_endpoint_conflict")
                    cur.execute(
                        "UPDATE erp_endpoints SET workspace_client_id = %s, "
                        "binding_generation = binding_generation + 1, updated_at = NOW() "
                        "WHERE id = %s AND binding_generation = %s RETURNING *",
                        (target_workspace_id, endpoint_id, expected_generation),
                    )
                    endpoint = cur.fetchone()
            elif action in {"enable", "disable"}:
                desired = action == "enable"
                if old_enabled == desired:
                    changed = False
                else:
                    cur.execute(
                        "UPDATE erp_endpoints SET enabled = %s, binding_generation = "
                        "binding_generation + 1, updated_at = NOW() WHERE id = %s "
                        "AND binding_generation = %s RETURNING *",
                        (desired, endpoint_id, expected_generation),
                    )
                    endpoint = cur.fetchone()
            else:
                if old_enabled:
                    raise LifecycleError("erp.endpoint_state_conflict")
                cur.execute(
                    "UPDATE workspace_clients SET erp_endpoint_id = NULL, updated_at = NOW() "
                    "WHERE id = %s AND tenant_id = %s AND is_active = TRUE "
                    "AND erp_endpoint_id = %s",
                    (source_workspace_id, tenant_id, endpoint_id),
                )
                if cur.rowcount != 1:
                    raise LifecycleError("erp.endpoint_stale_generation")
                cur.execute(
                    "UPDATE erp_endpoints SET workspace_client_id = NULL, shared_scope = FALSE, "
                    "enabled = FALSE, revoked_at = NOW(), revoked_by = %s, config = "
                    "config - ARRAY['agent_token','agent_token_hash','agent_token_tail',"
                    "'agent_token_created_at']::text[], binding_generation = binding_generation + 1, "
                    "updated_at = NOW() WHERE id = %s AND binding_generation = %s RETURNING *",
                    (actor_id, endpoint_id, expected_generation),
                )
                endpoint = cur.fetchone()

            if endpoint is None:
                raise LifecycleError("erp.endpoint_stale_generation")
            response = _safe(endpoint, changed=changed, operation_id=operation_id)
            if changed:
                details = {
                    "operation_id": operation_id,
                    "endpoint_id": endpoint_id,
                    "action": action,
                    "workspace_before": int(old_workspace or source_workspace_id),
                    "workspace_after": endpoint.get("workspace_client_id"),
                    "target_workspace_client_id": (
                        target_workspace_id if action == "rebind" else None
                    ),
                    "expected_generation": int(expected_generation),
                    "actual_generation": int(endpoint.get("binding_generation") or 0),
                    "generation_before": int(expected_generation),
                    "generation_after": int(endpoint.get("binding_generation") or 0),
                    "enabled_before": old_enabled,
                    "enabled_after": bool(endpoint.get("enabled")),
                    "shared_scope_before": old_shared_scope,
                    "shared_scope_after": bool(endpoint.get("shared_scope")),
                    "revoked_before": old_revoked,
                    "revoked_after": endpoint.get("revoked_at") is not None,
                    "reason": reason,
                }
                insert_operation_log_tx(
                    cur,
                    tenant_id=tenant_id,
                    actor_user_id=actor_id,
                    actor_username=user.get("username"),
                    actor_is_super=False,
                    action=f"erp.endpoint.{action}",
                    target_type="erp_endpoint",
                    target_id=endpoint_id,
                    target_name=str(endpoint.get("name") or "")[:80],
                    details=details,
                    ip=request_ip,
                    ua=request_ua,
                )
            return response
    except HTTPException:
        raise
    except LifecycleError as exc:
        raise _http(exc.code, exc.status) from exc
    except Exception as exc:
        if getattr(exc, "pgcode", None) == "23505":
            mapped = _integrity_error_code(exc)
            if mapped:
                raise _http(mapped) from exc
        logger.exception("managed Express lifecycle failed")
        raise

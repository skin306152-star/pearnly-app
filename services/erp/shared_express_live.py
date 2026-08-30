# -*- coding: utf-8 -*-
"""Managed Express agent heartbeat and explicit live-profile confirmation."""

from __future__ import annotations

import uuid
from datetime import timezone
from typing import Any, Dict, Optional

from core import db
from services.audit.store import insert_operation_log_tx
from services.authz.resolver import resolve
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp.shared_express_agent_auth import parse_managed_agent_token
from services.erp.shared_express_live_schema import (
    enable_managed_live_confirm,
    enable_managed_live_heartbeat,
    live_schema_ready,
)
from services.erp.shared_express_managed_schema import enable_managed_express_owner_access
from services.erp.shared_express_profile import profile_key

_MAX_CLOCK_SKEW_SECONDS = 5


class ManagedLiveError(Exception):
    """Stable error returned by both managed live operations."""

    def __init__(self, code: str, status: int = 409):
        super().__init__(code)
        self.code = code
        self.status = status


def _uuid(value: object, code: str = "erp.agent_unauthorized") -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ManagedLiveError(code, 401 if code == "erp.agent_unauthorized" else 422) from exc


def _row_value(row: Any, key: str, index: int = 0) -> Any:
    return row.get(key) if hasattr(row, "get") else row[index]


def _version(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > 120 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        return None
    return value


def _context(cur, tenant_id: str, user_id: str, workspace_id: Optional[object]) -> None:
    cur.execute(
        "SELECT set_config('app.current_tenant_id', %s, true), "
        "set_config('app.current_user_id', %s, true), "
        "set_config('app.current_workspace_id', %s, true)",
        (tenant_id, user_id, "" if workspace_id is None else str(workspace_id)),
    )


def _apply_rls_role(cur) -> None:
    """Switch only to db.py's validated non-bypass role after token lookup."""
    role_getter = getattr(db, "_rls_local_role", None)
    role = role_getter() if callable(role_getter) else ""
    if role:
        cur.execute(f"SET LOCAL ROLE {role}")


def _managed_endpoint(cur, endpoint_id: str, token_digest: str) -> Dict[str, Any]:
    cur.execute(
        "SELECT public.erp_managed_live_authenticate(%s, %s) AS endpoint",
        (endpoint_id, token_digest),
    )
    auth_row = cur.fetchone()
    row = auth_row.get("endpoint") if auth_row and hasattr(auth_row, "get") else None
    if not isinstance(row, dict):
        raise ManagedLiveError("erp.agent_unauthorized", 401)
    tenant_id = _row_value(row, "tenant_id")
    workspace_id = _row_value(row, "workspace_client_id")
    generation = int(_row_value(row, "binding_generation") or 0)
    if (
        generation < 1
        or tenant_id is None
        or workspace_id is None
        or not _row_value(row, "shared_scope")
    ):
        raise ManagedLiveError("erp.agent_unauthorized", 401)
    if not _row_value(row, "enabled"):
        raise ManagedLiveError("erp.endpoint_disabled", 403)
    return dict(row) if hasattr(row, "keys") else row


def _profile_status(row: Dict[str, Any], valid: bool) -> tuple[str, bool]:
    if not valid:
        return "needs_attention", False
    bound_set = row.get("bound_account_set")
    bound_key = row.get("bound_profile_key")
    live_set = row.get("live_account_set")
    live_key = row.get("live_profile_key")
    if bound_set is None and bound_key is None:
        return "unbound", False
    if bound_set == live_set and bound_key == live_key:
        return "ready", True
    return "mismatch", False


def _observed_profile(
    account_set: object, account_dir: object
) -> tuple[Optional[str], Optional[str], bool]:
    try:
        observed_set = account_set.strip().casefold() if isinstance(account_set, str) else None
        observed_key = profile_key(account_set, account_dir)
    except (TypeError, ValueError):
        return None, None, False
    return observed_set, observed_key, True


def _profile_is_fresh(seen, db_now) -> bool:
    if seen is None or db_now is None:
        return False
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    if db_now.tzinfo is None:
        db_now = db_now.replace(tzinfo=timezone.utc)
    age = (db_now - seen).total_seconds()
    return -_MAX_CLOCK_SKEW_SECONDS <= age < 180


def record_managed_heartbeat(
    token: str,
    *,
    account_set: object,
    account_dir: object,
    agent_version: object,
    offline: bool = False,
) -> Dict[str, Any]:
    """Authenticate and record only the four typed live fields in one transaction."""
    if not live_schema_ready():
        raise ManagedLiveError("erp.shared_endpoint_unavailable", 503)
    try:
        parsed = parse_managed_agent_token(token)
    except (TypeError, ValueError):
        raise ManagedLiveError("erp.agent_unauthorized", 401) from None
    if parsed is None:
        raise ManagedLiveError("erp.agent_unauthorized", 401)
    endpoint_id = str(parsed.endpoint_id)
    with db.get_cursor(commit=True) as cur:
        lock_endpoint_binding(cur, endpoint_id)
        row = _managed_endpoint(cur, endpoint_id, parsed.token_digest)
        tenant_id = str(row["tenant_id"])
        _context(cur, tenant_id, "", row["workspace_client_id"])
        _apply_rls_role(cur)
        generation = int(row["binding_generation"])
        if not enable_managed_live_heartbeat(
            cur,
            tenant_id=tenant_id,
            actor_user_id="",
            endpoint_id=endpoint_id,
            generation=generation,
        ):
            raise ManagedLiveError("erp.shared_endpoint_unavailable", 503)
        observed_set, observed_key, valid = _observed_profile(account_set, account_dir)
        if offline is True:
            update_sql = (
                "UPDATE erp_endpoints SET agent_last_seen_at = to_timestamp(0), agent_version = %s "
            )
            update_values = (_version(agent_version),)
        else:
            update_sql = (
                "UPDATE erp_endpoints SET live_account_set = %s, live_profile_key = %s, "
                "agent_last_seen_at = clock_timestamp(), agent_version = %s "
            )
            update_values = (observed_set, observed_key, _version(agent_version))
        cur.execute(
            update_sql
            + "WHERE id = %s AND binding_generation = %s RETURNING live_account_set, live_profile_key, agent_last_seen_at, agent_version",
            update_values + (endpoint_id, generation),
        )
        updated = cur.fetchone()
        if not updated:
            raise ManagedLiveError("erp.endpoint_stale_generation", 409)
        row.update(dict(updated) if hasattr(updated, "keys") else {})
        status, ready = _profile_status(row, valid)
        if offline is True:
            status, ready = "offline", False
        return {
            "ok": True,
            "connected": offline is not True,
            "endpoint_id": endpoint_id,
            "profile_status": status,
            "profile_ready": ready,
            "account_set": row.get("live_account_set"),
            "generation": generation,
        }


def confirm_managed_live_profile(
    user: Dict[str, Any],
    endpoint_id: str,
    source_workspace_id: object,
    expected_generation: int,
    confirm: bool,
    request_ip: object,
    request_ua: object,
) -> Dict[str, Any]:
    """Owner-confirm the observed profile with a generation CAS and required audit."""
    if confirm is not True:
        raise ManagedLiveError("erp.profile_confirmation_required", 400)
    if (
        not isinstance(expected_generation, int)
        or isinstance(expected_generation, bool)
        or expected_generation < 1
    ):
        raise ManagedLiveError("erp.endpoint_generation_invalid", 422)
    endpoint_id = _uuid(endpoint_id, "erp.endpoint_not_found")
    tenant_id = str(user.get("tenant_id") or "").strip()
    actor_id = str(user.get("id") or "").strip()
    try:
        source_workspace_id = int(source_workspace_id)
    except (TypeError, ValueError):
        raise ManagedLiveError("workspace.not_found", 404) from None
    if source_workspace_id < 1:
        raise ManagedLiveError("workspace.not_found", 404)
    if not tenant_id or not actor_id:
        raise ManagedLiveError("authz.not_found", 404)
    if not live_schema_ready():
        raise ManagedLiveError("erp.shared_endpoint_unavailable", 503)
    with db.get_cursor_rls(
        tenant_id=tenant_id, user_id=actor_id, workspace_client_id=source_workspace_id, commit=True
    ) as cur:
        lock_endpoint_binding(cur, endpoint_id)
        authz = resolve(user, cur=cur, lock=True)
        if (
            authz.membership_id is None
            or authz.role_key != "owner"
            or not authz.has("erp.endpoint.manage")
        ):
            raise ManagedLiveError("authz.forbidden", 403)
        if not enable_managed_express_owner_access(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=source_workspace_id,
            actor_user_id=actor_id,
        ):
            raise ManagedLiveError("erp.endpoint_not_found", 404)
        cur.execute(
            "SELECT id FROM tenants WHERE id = %s AND status IN ('active', 'warning') FOR SHARE",
            (tenant_id,),
        )
        if not cur.fetchone():
            raise ManagedLiveError("erp.endpoint_not_found", 404)
        cur.execute("SELECT * FROM erp_endpoints WHERE id = %s FOR UPDATE", (endpoint_id,))
        row = cur.fetchone()
        if not row or str(row.get("tenant_id")) != tenant_id:
            raise ManagedLiveError("erp.endpoint_not_found", 404)
        if (
            str(row.get("adapter") or "").lower() != "express"
            or int(row.get("binding_generation") or 0) < 1
            or row.get("revoked_at") is not None
            or not row.get("enabled")
            or not row.get("shared_scope")
        ):
            raise ManagedLiveError("erp.endpoint_not_found", 404)
        if row.get("workspace_client_id") != source_workspace_id:
            raise ManagedLiveError("erp.endpoint_not_found", 404)
        if int(row.get("binding_generation") or 0) != expected_generation:
            raise ManagedLiveError("erp.endpoint_stale_generation", 409)
        if row.get("live_account_set") is None or row.get("live_profile_key") is None:
            raise ManagedLiveError("erp.profile_not_ready", 409)
        old_bound = (row.get("bound_account_set"), row.get("bound_profile_key"))
        if (old_bound[0] is None) is not (old_bound[1] is None):
            raise ManagedLiveError("erp.shared_endpoint_unavailable", 503)
        live_pair = (row.get("live_account_set"), row.get("live_profile_key"))
        seen = row.get("agent_last_seen_at")
        cur.execute("SELECT clock_timestamp() AS now")
        clock_row = cur.fetchone()
        db_now = clock_row.get("now") if clock_row and hasattr(clock_row, "get") else None
        if not _profile_is_fresh(seen, db_now):
            raise ManagedLiveError("erp.profile_stale", 409)
        cur.execute("SELECT public.erp_managed_endpoint_has_activity(%s) AS busy", (endpoint_id,))
        busy = cur.fetchone()
        if busy and bool(busy.get("busy")):
            raise ManagedLiveError("erp.endpoint_busy", 409)
        _context(cur, tenant_id, actor_id, source_workspace_id)
        if not enable_managed_live_confirm(
            cur,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            endpoint_id=endpoint_id,
            expected_generation=expected_generation,
        ):
            raise ManagedLiveError("erp.shared_endpoint_unavailable", 503)
        cur.execute(
            "UPDATE erp_endpoints SET bound_account_set = live_account_set, "
            "bound_profile_key = live_profile_key, binding_generation = binding_generation + 1 "
            "WHERE id = %s AND binding_generation = %s RETURNING *",
            (endpoint_id, expected_generation),
        )
        updated = cur.fetchone()
        if not updated:
            raise ManagedLiveError("erp.endpoint_stale_generation", 409)
        updated = dict(updated)
        first_binding = old_bound == (None, None)
        profile_changed = old_bound != live_pair
        audit_action = "erp.endpoint.bind" if first_binding else "erp.endpoint.rebind"
        detail_action = "bind" if first_binding else "rebind"
        if first_binding:
            reason = "managed_live_profile_confirmed"
        elif profile_changed:
            reason = "managed_live_profile_switched"
        else:
            reason = "managed_live_profile_reconfirmed"
        insert_operation_log_tx(
            cur,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            actor_username=user.get("username"),
            actor_is_super=False,
            action=audit_action,
            target_type="erp_endpoint",
            target_id=endpoint_id,
            target_name=str(updated.get("name") or "")[:80],
            details={
                "endpoint_id": endpoint_id,
                "action": detail_action,
                "workspace_before": source_workspace_id,
                "workspace_after": source_workspace_id,
                "generation_before": expected_generation,
                "generation_after": int(updated.get("binding_generation") or 0),
                "profile_changed": profile_changed,
                "reason": reason,
            },
            ip=request_ip,
            ua=request_ua,
        )
        return {
            "ok": True,
            "endpoint_id": endpoint_id,
            "generation": int(updated.get("binding_generation") or 0),
            "bound_account_set": updated.get("bound_account_set"),
            "profile_ready": True,
        }


__all__ = ["ManagedLiveError", "confirm_managed_live_profile", "record_managed_heartbeat"]

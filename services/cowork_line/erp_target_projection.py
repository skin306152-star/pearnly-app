"""Safe connection and active-push projection for Cowork LINE ERP targets."""

from __future__ import annotations

import json
from typing import Any

from services.erp.push_log_meta import _derive_v3_meta
from services.erp.shared_express_store import safe_endpoint_dto


def _setup_action(missing: list[str]) -> str | None:
    actions = {
        "workspace_unbound": "bind_workspace",
        "workspace_binding_conflict": "resolve_workspace_binding",
        "endpoint_disabled": "enable_erp_connection",
        "endpoint_revoked": "reconnect_erp",
        "credentials_missing": "configure_erp_connection",
        "companion_offline": "restart_companion",
        "companion_not_ready": "check_companion",
        "profile_unconfirmed": "confirm_companion_profile",
        "profile_mismatch": "confirm_companion_profile",
        "account_set_locked": "close_express_or_wait",
    }
    return next((actions[code] for code in missing if code in actions), None)


def managed_target(
    row: dict[str, Any],
    workspace: dict[str, Any],
    *,
    duplicate: bool = False,
    cloud_in_flight: bool = False,
    waiting_lock: bool = False,
) -> dict[str, Any]:
    endpoint_id = str(row.get("id") or "")
    workspace_id = int(workspace["id"])
    dto = safe_endpoint_dto(row, row.get("server_now"))
    state = str(dto.get("connection_state") or "needs_attention")
    binding_ok = (
        str(workspace.get("erp_endpoint_id") or "") == endpoint_id
        and int(row.get("workspace_client_id") or 0) == workspace_id
    )
    bound = (row.get("bound_account_set"), row.get("bound_profile_key"))
    live = (row.get("live_account_set"), row.get("live_profile_key"))
    configured = None not in bound
    profile_matches = configured and bound == live
    missing: list[str] = []
    if duplicate:
        missing.append("workspace_binding_conflict")
    if waiting_lock:
        missing.append("account_set_locked")
    if not binding_ok:
        missing.append("workspace_unbound")
    if row.get("revoked_at") is not None:
        missing.append("endpoint_revoked")
    elif row.get("enabled") is not True:
        missing.append("endpoint_disabled")
    if state == "offline":
        missing.append("companion_offline")
    elif state == "unbound":
        missing.append("profile_unconfirmed")
    elif state == "mismatch":
        missing.append("profile_mismatch")
    elif state not in {"online", "disabled", "revoked"}:
        missing.append("companion_not_ready")
    profile_label = str(dto.get("account_set") or "").strip()
    endpoint_label = str(row.get("name") or "Express").strip()[:80]
    return {
        "endpoint_id": endpoint_id,
        "workspace_client_id": workspace_id,
        "workspace_name": str(workspace.get("name") or "")[:200] or None,
        "adapter": "express",
        "label": f"{endpoint_label} · {profile_label}" if profile_label else endpoint_label,
        "connection_state": state,
        "configured": configured,
        "selectable": not missing,
        "mode_options": ["stock", "service"],
        "ready_checks": {
            "permissions": True,
            "workspace_access": True,
            "workspace_bound": binding_ok and not duplicate,
            "erp_connection": state == "online",
            "companion_online": state == "online",
            "profile_matches": profile_matches,
            "cloud_in_flight": cloud_in_flight,
            "local_account_lock": "waiting_lock" if waiting_lock else None,
            "document_preflight": None,
        },
        "missing": missing,
        "block_reason": missing[0] if missing else None,
        "setup_action": _setup_action(missing),
    }


def _legacy_configured(config: Any) -> bool:
    if not isinstance(config, dict):
        return False
    encrypted = bool(config.get("username_enc") and config.get("password_enc"))
    plaintext = bool(config.get("username") and config.get("password"))
    return encrypted or plaintext


def legacy_target(
    endpoint: dict[str, Any],
    workspace: dict[str, Any] | None,
    *,
    binding_count: int,
    can_auto_create: bool = False,
) -> dict[str, Any]:
    configured = _legacy_configured(endpoint.get("config"))
    enabled = endpoint.get("enabled") is True
    missing: list[str] = []
    if not enabled:
        missing.append("endpoint_disabled")
    if not configured:
        missing.append("credentials_missing")
    if workspace is None:
        if not can_auto_create:
            missing.append("workspace_unbound")
    elif binding_count != 1:
        missing.append("workspace_binding_conflict")
    state = "disabled" if not enabled else "configured" if configured else "unconfigured"
    target = {
        "endpoint_id": str(endpoint.get("id") or ""),
        "workspace_client_id": int(workspace["id"]) if workspace else None,
        "workspace_name": str(workspace.get("name") or "")[:200] if workspace else None,
        "adapter": "mrerp",
        "label": str(endpoint.get("name") or "MR.ERP").strip()[:80],
        "connection_state": state,
        "configured": configured,
        "selectable": not missing,
        "mode_options": ["cash", "credit"],
        "ready_checks": {
            "permissions": True,
            "workspace_access": workspace is not None,
            "workspace_bound": workspace is not None and binding_count == 1,
            "workspace_auto_create": workspace is None and can_auto_create,
            "erp_connection": configured and enabled,
            "companion_online": None,
            "profile_matches": None,
            "document_preflight": None,
        },
        "missing": missing,
        "block_reason": missing[0] if missing else None,
        "setup_action": _setup_action(missing),
    }
    if workspace is None and can_auto_create and not missing:
        target["setup_action"] = "auto_create_workspace"
    return target


def active_push_state(cur, endpoint_id: str) -> tuple[bool, bool]:
    cur.execute(
        "SELECT response_body FROM erp_push_logs WHERE endpoint_id = %s "
        "AND status IN ('pending','retrying') ORDER BY created_at DESC,id DESC",
        (endpoint_id,),
    )
    activities = [dict(row) for row in (cur.fetchall() or [])]
    waiting_lock = False
    for activity in activities:
        body = activity.get("response_body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except (TypeError, ValueError):
                body = None
        meta = _derive_v3_meta(body)
        if meta.get("push_stage") == "waiting_lock":
            waiting_lock = True
            break
    return bool(activities), waiting_lock


__all__ = ["active_push_state", "legacy_target", "managed_target"]

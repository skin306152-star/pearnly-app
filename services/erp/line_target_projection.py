"""Safe connection and active-push projection shared by LINE ERP flows."""

from __future__ import annotations

import json
from typing import Any

from services.erp import target_readiness
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
        "account_set_unavailable": "configure_erp_connection",
        "account_set_locked": "close_express_or_wait",
    }
    return next((actions[code] for code in missing if code in actions), None)


def _legacy_account_label(
    endpoint: dict[str, Any], adapter: str, probe: dict[str, Any] | None
) -> str:
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    if adapter == "express":
        return str(config.get("account_set_label") or config.get("account_set") or "").strip()[:200]
    if adapter != "mrerp":
        return ""
    comidyear = str(config.get("comidyear") or "6").strip()
    seldb = str(config.get("seldb") or "1").strip()
    for company in (probe or {}).get("companies") or []:
        if not isinstance(company, dict):
            continue
        if (
            str(company.get("comidyear") or "").strip() == comidyear
            and str(company.get("seldb") or "").strip() == seldb
        ):
            return str(company.get("label") or "").strip()[:80]
    return f"{comidyear}/{seldb}"


def _mrerp_account_available(endpoint: dict[str, Any], probe: dict[str, Any] | None) -> bool | None:
    if not probe or not probe.get("ok"):
        return None
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    selected = (
        str(config.get("comidyear") or "6").strip(),
        str(config.get("seldb") or "1").strip(),
    )
    companies = [row for row in probe.get("companies") or [] if isinstance(row, dict)]
    return any(
        (
            str(row.get("comidyear") or "").strip(),
            str(row.get("seldb") or "").strip(),
        )
        == selected
        for row in companies
    )


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
        "account_set_label": profile_label or None,
        "connection_state": state,
        "configured": configured,
        "selectable": not missing,
        "mode_options": ["stock", "service"],
        "managed": True,
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


def legacy_target(
    endpoint: dict[str, Any],
    workspace: dict[str, Any] | None,
    *,
    binding_count: int,
    can_auto_create: bool = False,
    probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    adapter = str(endpoint.get("adapter") or "mrerp").strip().lower()
    status = target_readiness.endpoint_status({**endpoint, "adapter": adapter}, probe=probe)
    configured = bool(status["configured"])
    missing = list(status["missing"])
    account_available = _mrerp_account_available(endpoint, probe) if adapter == "mrerp" else None
    if account_available is False:
        missing.append("account_set_unavailable")
    if workspace is None:
        if not can_auto_create:
            missing.append("workspace_unbound")
    elif binding_count != 1:
        missing.append("workspace_binding_conflict")
    state = str(status["connection_state"])
    account_label = _legacy_account_label(endpoint, adapter, probe)
    endpoint_label = str(
        endpoint.get("name") or ("Express" if adapter == "express" else "MR.ERP")
    ).strip()[:80]
    target = {
        "endpoint_id": str(endpoint.get("id") or ""),
        "workspace_client_id": int(workspace["id"]) if workspace else None,
        "workspace_name": str(workspace.get("name") or "")[:200] if workspace else None,
        "adapter": adapter,
        "label": f"{endpoint_label} · {account_label}" if account_label else endpoint_label,
        "account_set_label": account_label or None,
        "connection_state": state,
        "configured": configured,
        "selectable": not missing,
        "mode_options": ["stock", "service"] if adapter == "express" else ["cash", "credit"],
        "managed": False,
        "ready_checks": {
            "permissions": True,
            "workspace_access": workspace is not None,
            "workspace_bound": workspace is not None and binding_count == 1,
            "workspace_auto_create": workspace is None and can_auto_create,
            "erp_connection": state == "online" or (probe is None and state == "configured"),
            "companion_online": state == "online" if adapter == "express" else None,
            "profile_matches": account_available,
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

"""Safe connection and active-push projection shared by LINE ERP flows."""

from __future__ import annotations

import json
import ntpath
from typing import Any

from services.erp import target_readiness
from services.erp.express_target_projection import normalize_express_account_key
from services.erp.push_log_meta import _derive_v3_meta
from services.erp.shared_express_store import safe_endpoint_dto

_MASTER_REFRESH_MIN_VERSION = (1, 1, 75)


def supports_master_refresh(version: Any) -> bool:
    try:
        parsed = tuple(int(part) for part in str(version or "").strip().split("."))
    except ValueError:
        return False
    return parsed >= _MASTER_REFRESH_MIN_VERSION


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


def _choice_key(*parts: object) -> str:
    return ":".join(str(part or "").strip() for part in parts)


def _root_label(root: str) -> str:
    clean = str(root or "").strip().rstrip("\\/")
    return ntpath.basename(clean) or clean


def _path_identity(path: object) -> str:
    value = str(path or "").strip()
    return ntpath.normcase(ntpath.normpath(value)) if value else ""


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _mrerp_account_choices(probe: dict[str, Any] | None) -> list[dict[str, Any]]:
    choices = []
    for company in (probe or {}).get("companies") or []:
        if not isinstance(company, dict):
            continue
        comidyear = str(company.get("comidyear") or "").strip()
        seldb = str(company.get("seldb") or "").strip()
        if not comidyear or not seldb:
            continue
        label = str(company.get("label") or company.get("name") or "").strip()
        choices.append(
            {
                "key": _choice_key(comidyear, seldb),
                "label": label or f"{comidyear}/{seldb}",
                "comidyear": comidyear,
                "seldb": seldb,
            }
        )
    return choices


def _projection_express_choices(probe: dict[str, Any] | None) -> list[dict[str, Any]]:
    choices = []
    for row in (probe or {}).get("account_sets") or []:
        if not isinstance(row, dict):
            continue
        attributes = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
        key = normalize_express_account_key(row.get("source_id"))
        if not key:
            continue
        choices.append(
            {
                "key": key,
                "label": str(row.get("label") or key).strip(),
                "root_key": str(attributes.get("root") or "").strip(),
                "root_label": str(attributes.get("root_label") or "").strip()
                or _root_label(str(attributes.get("root") or "")),
                "account_set": key,
                "account_dir": str(attributes.get("path") or key).strip(),
                "account_company": str(attributes.get("company") or "").strip(),
                "account_set_row": _int_value(attributes.get("row")),
                "writable": bool(attributes.get("writable", True)),
                "mapping": (
                    attributes.get("mapping") if isinstance(attributes.get("mapping"), dict) else {}
                ),
            }
        )
    return choices


def _express_account_choices(
    endpoint: dict[str, Any], probe: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    projected = _projection_express_choices(probe)
    if projected:
        return projected
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    reported = config.get("reported_account_sets")
    rows = reported if isinstance(reported, list) else []
    choices: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip()
        identity = _path_identity(path)
        if not identity or identity in seen:
            continue
        seen.add(identity)
        root = str(row.get("root") or "").strip() or ntpath.dirname(path.rstrip("\\/"))
        name = str(row.get("name") or row.get("company") or row.get("code") or "").strip()
        choices.append(
            {
                "key": path,
                "label": name or ntpath.basename(path.rstrip("\\/")) or path,
                "root_key": root,
                "root_label": str(row.get("root_label") or "").strip() or _root_label(root),
                "account_set": path,
                "account_dir": path,
                "account_company": str(row.get("company") or "").strip(),
                "account_set_row": _int_value(row.get("row")),
                "writable": bool(row.get("writable")),
                "mapping": row.get("mapping") if isinstance(row.get("mapping"), dict) else {},
            }
        )
    current = str(config.get("account_set") or config.get("account_dir") or "").strip()
    if current and _path_identity(current) not in seen:
        root = str(config.get("express_root") or "").strip() or ntpath.dirname(
            current.rstrip("\\/")
        )
        choices.append(
            {
                "key": current,
                "label": str(config.get("account_set_label") or "").strip()
                or ntpath.basename(current.rstrip("\\/"))
                or current,
                "root_key": root,
                "root_label": _root_label(root),
                "account_set": current,
                "account_dir": str(config.get("account_dir") or current).strip(),
                "account_company": str(config.get("account_company") or "").strip(),
                "account_set_row": _int_value(config.get("account_set_row")),
                "writable": True,
                "mapping": {},
            }
        )
    return choices


def _legacy_account_choices(
    endpoint: dict[str, Any], adapter: str, probe: dict[str, Any] | None
) -> list[dict[str, Any]]:
    if adapter == "mrerp":
        return _mrerp_account_choices(probe)
    if adapter == "express":
        return _express_account_choices(endpoint, probe)
    return []


def _legacy_account_label(
    endpoint: dict[str, Any], adapter: str, choices: list[dict[str, Any]]
) -> str:
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    selected = (
        _choice_key(config.get("comidyear") or "6", config.get("seldb") or "1")
        if adapter == "mrerp"
        else normalize_express_account_key(config.get("account_set") or config.get("account_dir"))
    )
    for choice in choices:
        choice_key = str(choice.get("key") or "")
        if choice_key == selected or (
            adapter == "express"
            and normalize_express_account_key(choice_key) == normalize_express_account_key(selected)
        ):
            return str(choice.get("label") or "").strip()[:200]
    return selected


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
    account_sets: list[dict[str, Any]] | None = None,
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
    account_choices = _projection_express_choices({"account_sets": account_sets or []}) or (
        [
            {
                "key": profile_label,
                "label": profile_label,
                "account_set": profile_label,
                "writable": True,
            }
        ]
        if profile_label
        else []
    )
    profile_key = normalize_express_account_key(profile_label)
    selected_choice = next(
        (
            choice
            for choice in account_choices
            if normalize_express_account_key(choice.get("key")) == profile_key
        ),
        None,
    )
    selected_account_key = str((selected_choice or {}).get("key") or profile_label).strip()
    account_label = str((selected_choice or {}).get("label") or profile_label).strip()
    return {
        "endpoint_id": endpoint_id,
        "workspace_client_id": workspace_id,
        "workspace_name": str(workspace.get("name") or "")[:200] or None,
        "adapter": "express",
        "connection_label": endpoint_label,
        "label": f"{endpoint_label} · {account_label}" if account_label else endpoint_label,
        "account_set_label": account_label or None,
        "account_choices": account_choices,
        "selected_account_key": selected_account_key or None,
        "connection_state": state,
        "configured": configured,
        "selectable": not missing,
        "mode_options": ["stock", "service"],
        "supports_master_refresh": supports_master_refresh(row.get("agent_version")),
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
    account_choices = _legacy_account_choices(endpoint, adapter, probe)
    account_label = _legacy_account_label(endpoint, adapter, account_choices)
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    configured_account_key = (
        _choice_key(config.get("comidyear") or "6", config.get("seldb") or "1")
        if adapter == "mrerp"
        else str(config.get("account_set") or config.get("account_dir") or "").strip()
    )
    selected_account_key = next(
        (
            str(choice.get("key") or "")
            for choice in account_choices
            if str(choice.get("key") or "") == configured_account_key
            or (
                adapter == "express"
                and normalize_express_account_key(choice.get("key"))
                == normalize_express_account_key(configured_account_key)
            )
        ),
        configured_account_key,
    )
    endpoint_label = str(
        endpoint.get("name") or ("Express" if adapter == "express" else "MR.ERP")
    ).strip()[:80]
    target = {
        "endpoint_id": str(endpoint.get("id") or ""),
        "workspace_client_id": int(workspace["id"]) if workspace else None,
        "workspace_name": str(workspace.get("name") or "")[:200] if workspace else None,
        "adapter": adapter,
        "connection_label": endpoint_label,
        "label": f"{endpoint_label} · {account_label}" if account_label else endpoint_label,
        "account_set_label": account_label or None,
        "account_choices": account_choices,
        "selected_account_key": selected_account_key or None,
        "connection_state": state,
        "configured": configured,
        "selectable": not missing,
        "mode_options": ["stock", "service"] if adapter == "express" else ["cash", "credit"],
        "supports_master_refresh": (
            supports_master_refresh(config.get("companion_version"))
            if adapter == "express"
            else True
        ),
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


__all__ = [
    "active_push_state",
    "legacy_target",
    "managed_target",
    "supports_master_refresh",
]

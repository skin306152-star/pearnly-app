"""ERP target access and selection normalization for Cowork LINE intake."""

from __future__ import annotations

from services.erp import target_catalog_evidence
from services.erp.line_target_choice import find_account_choice, target_label_for_account


class CoworkLineIntakeError(Exception):
    def __init__(self, code: str, status_code: int = 409):
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def _service():
    from services.cowork_line import erp_targets

    return erp_targets


def _error(exc: Exception) -> CoworkLineIntakeError:
    code = str(getattr(exc, "code", "target_not_ready"))
    status = (
        403 if code in {"forbidden", "identity_inactive", "workspace_manage_forbidden"} else 409
    )
    return CoworkLineIntakeError(code, status)


def list_targets(
    identity: dict, *, refresh: bool = False, include_account_catalog: bool = True
) -> list[dict]:
    try:
        return _service().list_targets(
            identity,
            refresh=refresh,
            include_account_catalog=include_account_catalog,
        )
    except Exception as exc:
        if exc.__class__.__name__ != "CoworkLineErpTargetError":
            raise
        raise _error(exc) from exc


def get_target(
    identity: dict,
    endpoint_id: str,
    workspace_client_id: int | None,
    *,
    include_account_catalog: bool = True,
    refresh_probe: bool = False,
) -> dict:
    try:
        return _service().require_target(
            identity,
            endpoint_id,
            workspace_client_id,
            refresh_probe=refresh_probe,
            include_account_catalog=include_account_catalog,
        )
    except Exception as exc:
        if exc.__class__.__name__ != "CoworkLineErpTargetError":
            raise
        raise _error(exc) from exc


def _connection_workspace(target: dict) -> int | None:
    raw = (
        target.get("connection_workspace_client_id")
        if "connection_workspace_client_id" in target
        else target.get("workspace_client_id")
    )
    return int(raw) if raw is not None else None


def normalize_selection(target: dict, selection: dict) -> dict:
    adapter = str(target.get("adapter") or "").lower()
    direction = str(selection.get("direction") or "").lower()
    if direction not in {"purchase", "sales"}:
        raise CoworkLineIntakeError("direction_required", 422)
    mode_key = "posting_kind" if adapter == "express" else "payment"
    mode = str(selection.get(mode_key) or "").lower()
    allowed = {str(value).lower() for value in target.get("mode_options") or []}
    if not mode or (allowed and mode not in allowed):
        raise CoworkLineIntakeError("mode_required", 422)
    account_key = str(selection.get("account_set") or "").strip()
    if not account_key:
        raise CoworkLineIntakeError("account_set_required", 422)
    account = find_account_choice(target, account_key=account_key)
    if not account:
        raise CoworkLineIntakeError("account_set_required", 422)
    account_root = str(account.get("root_key") or "").strip() or None
    requested_root = str(selection.get("account_root") or "").strip() or None
    if requested_root and requested_root != account_root:
        raise CoworkLineIntakeError("account_set_required", 422)
    connection_workspace_id = _connection_workspace(target)
    if "connection_workspace_client_id" in target:
        workspace_client_id = target.get("workspace_client_id")
    elif "connection_workspace_client_id" in selection:
        workspace_client_id = selection.get("workspace_client_id")
    else:
        workspace_client_id = target.get("workspace_client_id")
    normalized = {
        "endpoint_id": str(target["endpoint_id"]),
        "connection_workspace_client_id": connection_workspace_id,
        "workspace_client_id": (
            int(workspace_client_id) if workspace_client_id is not None else None
        ),
        "adapter": adapter,
        "target_label": target_label_for_account(target, account),
        "account_root": account_root,
        "account_set": account_key,
        "account_config": {
            key: account.get(key)
            for key in (
                "comidyear",
                "seldb",
                "account_set",
                "account_dir",
                "account_company",
                "account_set_row",
                "root_key",
                "mapping",
            )
            if account.get(key) not in (None, "")
        },
        "direction": direction,
        "posting_kind": mode if adapter == "express" else None,
        "payment": mode if adapter != "express" else None,
    }
    for key in ("catalog_refresh_request_id", "catalog_refresh_revision"):
        if selection.get(key) not in (None, ""):
            normalized[key] = selection[key]
    return normalized


def validated_selection(
    identity: dict, selection: dict, *, refresh_probe: bool = False
) -> tuple[dict, dict]:
    endpoint_id = str(selection.get("endpoint_id") or "").strip()
    if not endpoint_id:
        raise CoworkLineIntakeError("target_required", 422)
    if not str(selection.get("account_set") or "").strip():
        raise CoworkLineIntakeError("account_set_required", 422)
    compact_target = get_target(
        identity,
        endpoint_id,
        (
            selection.get("connection_workspace_client_id")
            if "connection_workspace_client_id" in selection
            else selection.get("workspace_client_id")
        ),
        include_account_catalog=False,
        refresh_probe=False,
    )
    adapter = str(compact_target.get("adapter") or "").lower()
    requested_account = str(selection.get("account_set") or "").strip()
    compact_account = find_account_choice(compact_target, account_key=requested_account)
    requested_root = str(selection.get("account_root") or "").strip() or None
    if compact_account and requested_root != (
        str(compact_account.get("root_key") or "").strip() or None
    ):
        raise CoworkLineIntakeError("account_set_required", 422)
    bound_key = str(compact_target.get("selected_account_key") or "").strip()
    bound_choice = find_account_choice(compact_target, account_key=bound_key) or {}
    evidence = target_catalog_evidence.validate_selection(
        tenant_id=str(identity.get("tenant_id") or ""),
        user_id=str(identity.get("user_id") or ""),
        endpoint_id=endpoint_id,
        adapter=adapter,
        selected_account_set_key=requested_account,
        bound_account_set_key=bound_key,
        selected_root_key=requested_root,
        bound_root_key=bound_choice.get("root_key"),
        request_id=selection.get("catalog_refresh_request_id"),
        revision=selection.get("catalog_refresh_revision"),
    )
    if not evidence["ok"]:
        raise CoworkLineIntakeError(str(evidence["error_code"]), 409)
    target = compact_target
    if evidence["proof_required"]:
        target = get_target(
            identity,
            endpoint_id,
            (
                selection.get("connection_workspace_client_id")
                if "connection_workspace_client_id" in selection
                else selection.get("workspace_client_id")
            ),
            include_account_catalog=True,
            refresh_probe=False,
        )
        selection = {
            **selection,
            "catalog_refresh_request_id": evidence["request_id"],
            "catalog_refresh_revision": evidence["revision"],
        }
    else:
        selection = {
            key: value
            for key, value in selection.items()
            if key not in {"catalog_refresh_request_id", "catalog_refresh_revision"}
        }
    normalized = normalize_selection(target, selection)
    projected = {
        **target,
        "connection_workspace_client_id": normalized["connection_workspace_client_id"],
        "workspace_client_id": normalized["workspace_client_id"],
    }
    return projected, normalized


def resolve_history_workspace(
    identity: dict,
    target: dict,
    history_ids: list[str],
    direction: str,
    *,
    provisional_history_assignment: bool,
) -> dict:
    try:
        return _service().resolve_history_workspace(
            identity,
            target,
            history_ids,
            direction,
            provisional_history_assignment=provisional_history_assignment,
        )
    except Exception as exc:
        if exc.__class__.__name__ != "CoworkLineErpTargetError":
            raise
        raise _error(exc) from exc


def preflight_target(identity: dict, target: dict, history_ids: list[str], selection: dict) -> dict:
    missing = list(target.get("missing") or [])
    for history_id in history_ids:
        result = _service().preflight_document(
            identity,
            target,
            history_id,
            selection["direction"],
            posting_kind=selection.get("posting_kind"),
            payment=selection.get("payment"),
            account_config=selection.get("account_config"),
        )
        for code in result.get("missing") or []:
            if code not in missing:
                missing.append(code)
    projected = dict(target)
    checks = dict(projected.get("ready_checks") or {})
    checks["document_preflight"] = not missing
    projected.update(
        {
            "ready_checks": checks,
            "missing": missing,
            "block_reason": missing[0] if missing else None,
            "selectable": bool(projected.get("selectable", True)) and not missing,
        }
    )
    return projected


def replace_target(targets: list[dict], selected: dict) -> list[dict]:
    return [
        (
            selected
            if (
                str(target.get("endpoint_id")) == str(selected.get("endpoint_id"))
                and _connection_workspace(target) == _connection_workspace(selected)
            )
            else target
        )
        for target in targets
    ]


__all__ = [
    "CoworkLineIntakeError",
    "get_target",
    "list_targets",
    "normalize_selection",
    "preflight_target",
    "replace_target",
    "resolve_history_workspace",
    "validated_selection",
]

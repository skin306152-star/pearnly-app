"""Keep master refresh evidence aligned with the account selected in an editor."""

from __future__ import annotations

from typing import Any

from core.feature_flags import erp_target_projection_enabled_for
from services.erp import target_refresh
from services.erp.express_target_projection import normalize_express_account_key


def _account_identity(adapter: str, value: Any) -> str:
    raw = str(value or "").strip()
    if adapter == "express":
        return normalize_express_account_key(raw)
    return raw


def _enabled(identity: dict[str, Any], target: dict[str, Any]) -> bool:
    return bool(target.get("supports_master_refresh")) and erp_target_projection_enabled_for(
        str(identity.get("tenant_id") or ""),
        str(identity.get("user_id") or ""),
    )


def status_for_selection(
    identity: dict[str, Any],
    target: dict[str, Any],
    account_set_key: Any,
    request_id: Any,
) -> dict[str, Any] | None:
    request_id = str(request_id or "").strip()
    if not request_id:
        return None
    state = target_refresh.refresh_status(
        request_id,
        tenant_id=str(identity["tenant_id"]),
        endpoint_id=str(target["endpoint_id"]),
    )
    if not state:
        return None
    adapter = str(target.get("adapter") or "").lower()
    expected = _account_identity(adapter, account_set_key)
    actual = _account_identity(adapter, state.get("account_set_key"))
    if not expected or expected != actual:
        return {**state, "status": "mismatch"}
    return state


def ensure_for_editor(
    identity: dict[str, Any],
    target: dict[str, Any],
    account_set_key: Any,
    *,
    previous_request_id: Any = None,
) -> dict[str, Any] | None:
    """Reuse matching evidence or refresh the exact account selected by the user."""
    if not _enabled(identity, target):
        return None
    adapter = str(target.get("adapter") or "").lower()
    account_key = _account_identity(adapter, account_set_key)
    if adapter not in {"mrerp", "express"} or not account_key:
        raise ValueError("erp.target_refresh_invalid")
    state = status_for_selection(
        identity,
        target,
        account_key,
        previous_request_id,
    )
    if not state or str(state.get("status") or "") in {"failed", "mismatch"}:
        request = target_refresh.request_refresh(
            tenant_id=str(identity["tenant_id"]),
            user_id=str(identity["user_id"]),
            endpoint_id=str(target["endpoint_id"]),
            account_set_key=account_key,
            adapter=adapter,
            reason="line_editor_selection",
        )
        request_id = str(request["request_id"])
        state = status_for_selection(identity, target, account_key, request_id) or {
            "status": request.get("status"),
            "account_set_key": account_key,
        }
    else:
        request_id = str(previous_request_id)
    if adapter == "mrerp" and str(state.get("status") or "") != "succeeded":
        target_refresh.process_mrerp_request(request_id)
        state = status_for_selection(identity, target, account_key, request_id) or state
    return {
        "request_id": request_id,
        "status": str(state.get("status") or ""),
        "account_set_key": account_key,
        "error_code": state.get("error_code"),
    }


__all__ = ["ensure_for_editor", "status_for_selection"]

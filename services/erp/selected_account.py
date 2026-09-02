"""Resolve a requested ERP account only from server-side target projections."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from services.erp import line_target_projection, target_readiness
from services.erp.express_target_projection import normalize_express_account_key
from services.erp.line_target_choice import endpoint_with_account_choice
from services.erp.target_projection_store import load_state, load_state_with_cursor


def _requested_key(
    endpoint: dict[str, Any],
    account_set_key: object,
    trusted_account_config: dict[str, Any] | None,
) -> str:
    direct = str(account_set_key or "").strip()
    if direct:
        return direct
    choice = trusted_account_config if isinstance(trusted_account_config, dict) else {}
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    if adapter == "mrerp":
        for source in (choice, config):
            year = str(source.get("comidyear") or "").strip()
            database = str(source.get("seldb") or "").strip()
            if year and database:
                return f"{year}:{database}"
        return ""
    return str(
        choice.get("account_set")
        or choice.get("account_dir")
        or config.get("account_set")
        or config.get("account_dir")
        or endpoint.get("bound_account_set")
        or ""
    ).strip()


def _projection_probe(endpoint: dict[str, Any], state: dict[str, Any] | None) -> dict[str, Any]:
    snapshot = (state or {}).get("snapshot") or {}
    account_sets = snapshot.get("account_sets") or []
    if str(endpoint.get("adapter") or "").strip().lower() != "mrerp":
        return {"account_sets": account_sets}
    companies = []
    for row in account_sets:
        if not isinstance(row, dict):
            continue
        attributes = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
        companies.append(
            {
                "label": row.get("label"),
                "comidyear": attributes.get("comidyear"),
                "seldb": attributes.get("seldb"),
            }
        )
    return {"companies": companies}


def _matches(adapter: str, left: object, right: object) -> bool:
    if adapter == "express":
        return normalize_express_account_key(left) == normalize_express_account_key(right)
    return str(left or "").strip() == str(right or "").strip()


def _trusted_fallback(
    endpoint: dict[str, Any],
    requested: str,
    trusted_account_config: dict[str, Any] | None,
) -> dict[str, Any] | None:
    trusted = trusted_account_config if isinstance(trusted_account_config, dict) else {}
    if not trusted:
        return None
    trusted_key = _requested_key(endpoint, None, trusted)
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    if not trusted_key or not _matches(adapter, requested, trusted_key):
        return None
    return {"key": trusted_key, **trusted}


def resolve_account_choice(
    endpoint: dict[str, Any],
    *,
    tenant_id: str,
    user_id: str,
    account_set_key: object = None,
    trusted_account_config: dict[str, Any] | None = None,
    cur=None,
) -> dict[str, Any] | None:
    """Validate one final destination; no request value is ever copied through blindly."""
    requested = _requested_key(endpoint, account_set_key, trusted_account_config)
    if not requested:
        return None
    endpoint_id = str(endpoint.get("id") or "").strip()
    state = (
        load_state_with_cursor(cur, tenant_id=tenant_id, endpoint_id=endpoint_id)
        if cur is not None
        else load_state(
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint_id=endpoint_id,
        )
    )
    probe = _projection_probe(endpoint, state)
    choices = line_target_projection.account_choices_for_endpoint(endpoint, probe)
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    if adapter == "mrerp" and not choices and cur is None:
        probe = target_readiness.probe_endpoint(endpoint, refresh=False)
        choices = line_target_projection.account_choices_for_endpoint(endpoint, probe)
    choice = next(
        (
            row
            for row in choices
            if isinstance(row, dict) and _matches(adapter, row.get("key"), requested)
        ),
        None,
    )
    if choice is None:
        choice = _trusted_fallback(endpoint, requested, trusted_account_config)
    if choice is None or choice.get("writable") is False:
        raise HTTPException(409, detail="erp.account_set_unavailable")
    return choice


def allowed_express_account_keys(endpoint: dict[str, Any], *, tenant_id: str, cur) -> list[str]:
    """Return normalized writable Express targets visible to one authenticated agent."""
    state = load_state_with_cursor(
        cur,
        tenant_id=tenant_id,
        endpoint_id=str(endpoint.get("id") or ""),
    )
    choices = line_target_projection.account_choices_for_endpoint(
        endpoint, _projection_probe(endpoint, state)
    )
    keys = {
        normalize_express_account_key(choice.get("key"))
        for choice in choices
        if isinstance(choice, dict) and choice.get("writable") is not False
    }
    keys.discard("")
    return sorted(keys)


def resolve_endpoint_account(
    endpoint: dict[str, Any],
    *,
    tenant_id: str,
    user_id: str,
    account_set_key: object = None,
    trusted_account_config: dict[str, Any] | None = None,
    cur=None,
) -> tuple[dict[str, Any], str]:
    """Return an endpoint configured with one validated final destination."""
    choice = resolve_account_choice(
        endpoint,
        tenant_id=tenant_id,
        user_id=user_id,
        account_set_key=account_set_key,
        trusted_account_config=trusted_account_config,
        cur=cur,
    )
    selected_endpoint = endpoint_with_account_choice(endpoint, choice)
    config = selected_endpoint.get("config") or {}
    selected_account = str(config.get("account_set") or config.get("account_dir") or "").strip()
    if not selected_account:
        raise HTTPException(409, detail="erp.account_set_unavailable")
    return selected_endpoint, selected_account


__all__ = [
    "allowed_express_account_keys",
    "resolve_account_choice",
    "resolve_endpoint_account",
]

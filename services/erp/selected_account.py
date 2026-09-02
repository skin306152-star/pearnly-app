"""Resolve a requested ERP account only from server-side target projections."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from services.erp import line_target_projection, target_catalog_evidence
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
        year = str(choice.get("comidyear") or "").strip()
        database = str(choice.get("seldb") or "").strip()
        if year and database:
            return f"{year}:{database}"
        return (
            f"{str(config.get('comidyear') or '6').strip()}:"
            f"{str(config.get('seldb') or '1').strip()}"
        )
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


def _configured_default_choice(endpoint: dict[str, Any], requested: str) -> dict[str, Any] | None:
    """Return the server-owned binding default without probing mutable ERP state."""
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    if adapter == "mrerp":
        comidyear = str(config.get("comidyear") or "6").strip()
        seldb = str(config.get("seldb") or "1").strip()
        key = f"{comidyear}:{seldb}"
        if _matches(adapter, requested, key):
            return {
                "key": key,
                "comidyear": comidyear,
                "seldb": seldb,
            }
        return None
    if adapter != "express":
        return None
    configured = str(config.get("account_set") or config.get("account_dir") or "").strip()
    bound = str(endpoint.get("bound_account_set") or "").strip()
    default_key = bound if int(endpoint.get("binding_generation") or 0) > 0 else configured
    default_key = default_key or configured or bound
    if not default_key or not _matches(adapter, requested, default_key):
        return None
    account_dir = (
        configured if configured and _matches(adapter, configured, default_key) else default_key
    )
    return {
        "key": normalize_express_account_key(default_key),
        "root_key": str(config.get("express_root") or "").strip(),
        "account_set": normalize_express_account_key(default_key),
        "account_dir": account_dir,
        "account_company": str(config.get("account_company") or "").strip(),
        "account_set_row": int(config.get("account_set_row") or 0),
        "writable": True,
    }


def _bound_account_key(endpoint: dict[str, Any]) -> str:
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    if adapter == "mrerp":
        return f"{str(config.get('comidyear') or '6').strip()}:{str(config.get('seldb') or '1').strip()}"
    if adapter != "express":
        return ""
    managed_bound = str(endpoint.get("bound_account_set") or "").strip()
    configured = str(config.get("account_set") or config.get("account_dir") or "").strip()
    if int(endpoint.get("binding_generation") or 0) > 0:
        return managed_bound or configured
    return configured or managed_bound


def require_catalog_evidence(
    endpoint: dict[str, Any],
    *,
    tenant_id: str,
    user_id: str,
    account_set_key: object = None,
    trusted_account_config: dict[str, Any] | None = None,
    request_id: object = None,
    revision: object = None,
    cur=None,
) -> dict[str, Any] | None:
    """Fail closed when a web-selected non-default target lacks fresh evidence."""
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    if adapter not in {"mrerp", "express"}:
        return None
    selected_key = _requested_key(endpoint, account_set_key, trusted_account_config)
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    trusted = trusted_account_config if isinstance(trusted_account_config, dict) else {}
    result = target_catalog_evidence.validate_selection(
        cur,
        tenant_id=tenant_id,
        user_id=user_id,
        endpoint_id=str(endpoint.get("id") or ""),
        adapter=adapter,
        selected_account_set_key=selected_key,
        bound_account_set_key=_bound_account_key(endpoint),
        selected_root_key=trusted.get("root_key"),
        bound_root_key=config.get("express_root"),
        request_id=request_id,
        revision=revision,
    )
    if result.get("ok") is not True:
        raise HTTPException(
            409,
            detail={
                "code": result.get("error_code") or target_catalog_evidence.CATALOG_REFRESH_INVALID,
                "reason": result.get("reason") or "catalog_evidence_invalid",
            },
        )
    return result


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
    if not trusted_account_config:
        default_choice = _configured_default_choice(endpoint, requested)
        if default_choice is not None:
            return default_choice
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
    "require_catalog_evidence",
    "resolve_account_choice",
    "resolve_endpoint_account",
]

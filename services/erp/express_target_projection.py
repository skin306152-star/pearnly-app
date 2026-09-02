# -*- coding: utf-8 -*-
"""Publish Companion heartbeat catalogs into the canonical ERP projection."""

from __future__ import annotations

import ntpath
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from core import db
from services.erp.target_projection_contract import normalize_projection
from services.erp.target_projection_store import publish_with_cursor

_COLLECTOR_KIND = "companion"


def _value(item: Mapping[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return ""


def _attributes(item: Mapping[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in keys:
        value = item.get(key)
        if value is None or value == "":
            continue
        if isinstance(value, (bool, int)):
            result[key] = value
        elif isinstance(value, Mapping):
            result[key] = {
                str(child_key).strip()[:100]: str(child_value).strip()[:500]
                for child_key, child_value in value.items()
                if str(child_key).strip() and child_value not in (None, "")
            }
        else:
            result[key] = str(value).strip()[:500]
    return result


def _options(
    raw: Any,
    *,
    source_keys: tuple[str, ...],
    label_keys: tuple[str, ...],
    attribute_keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, Mapping):
            continue
        source_id = _value(item, source_keys)[:300]
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        rows.append(
            {
                "source_id": source_id,
                "label": (_value(item, label_keys) or source_id)[:500],
                "attributes": _attributes(item, attribute_keys),
            }
        )
    return rows


def _account_sets(raw: Any) -> list[dict[str, Any]]:
    rows = _options(
        raw,
        source_keys=("path", "code"),
        label_keys=("name", "company", "code", "path"),
        attribute_keys=(
            "code",
            "path",
            "company",
            "tax_id",
            "writable",
            "row",
            "root",
            "root_label",
            "mapping",
        ),
    )
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        source_id = normalize_express_account_key(row["source_id"])
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        normalized.append({**row, "source_id": source_id})
    return normalized


def normalize_express_account_key(value: Any) -> str:
    raw = str(value or "").strip().replace("/", "\\").rstrip("\\")
    return ntpath.normcase(ntpath.normpath(raw))[:500] if raw else ""


def _selected_account_set(body: Mapping[str, Any]) -> str:
    return normalize_express_account_key(body.get("account_set") or body.get("account_dir"))


def _ensure_selected_choice(
    account_sets: list[dict[str, Any]], body: Mapping[str, Any], selected_key: str
) -> list[dict[str, Any]]:
    if not selected_key or any(row["source_id"] == selected_key for row in account_sets):
        return account_sets
    return [
        *account_sets,
        {
            "source_id": selected_key,
            "label": str(body.get("account_company") or selected_key).strip()[:500],
            "attributes": {
                "path": str(body.get("account_dir") or selected_key).strip()[:500],
                "writable": True,
            },
        },
    ]


def _masters(body: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    catalog = body.get("catalog") if isinstance(body.get("catalog"), Mapping) else {}
    return {
        "products": _options(
            catalog.get("products"),
            source_keys=("code",),
            label_keys=("name", "code"),
            attribute_keys=("kind",),
        ),
        "customers": _options(
            catalog.get("customers"),
            source_keys=("code",),
            label_keys=("name", "code"),
            attribute_keys=("tax_id", "kind", "branch"),
        ),
        "accounts": _options(
            body.get("accounts"),
            source_keys=("code",),
            label_keys=("name", "code"),
            attribute_keys=("type",),
        ),
    }


def _form_schema() -> dict[str, Any]:
    fields = [
        {
            "key": "product_id",
            "label": "Product",
            "type": "reference",
            "options_source": "products",
        },
        {
            "key": "customer_id",
            "label": "Customer",
            "type": "reference",
            "options_source": "customers",
        },
        {
            "key": "account_id",
            "label": "Account",
            "type": "reference",
            "options_source": "accounts",
        },
    ]
    fields.extend(
        {
            "key": f"{entity[:-1]}_id",
            "label": entity.title(),
            "type": "unsupported",
            "visible": False,
            "attributes": {"status": "collector_not_connected"},
        }
        for entity in ("suppliers", "units", "branches")
    )
    return {"fields": fields}


def _capabilities() -> dict[str, Any]:
    actions = [
        {"key": f"master.{entity}.read", "label": entity.title()}
        for entity in ("products", "customers", "accounts")
    ]
    actions.extend(
        {
            "key": f"master.{entity}.read",
            "label": entity.title(),
            "enabled": False,
            "block_reason": "erp.target_projection_collector_not_connected",
        }
        for entity in ("suppliers", "units", "branches")
    )
    return {"actions": actions}


def _collector(body: Mapping[str, Any]) -> dict[str, str]:
    version = str(body.get("companion_version") or "").strip()[:200]
    result = {"kind": _COLLECTOR_KIND}
    if version:
        result["adapter_version"] = version
    return result


def _endpoint_observation(
    body: Mapping[str, Any], account_sets: list[dict[str, Any]], observed_at: datetime
) -> dict[str, Any]:
    return {
        "adapter": "express",
        "observed_at": observed_at,
        "collector": _collector(body),
        "account_sets": account_sets,
        "masters": {},
        "form_schema": {"fields": []},
        "capabilities": {"actions": []},
    }


def _account_observation(
    body: Mapping[str, Any],
    account_sets: list[dict[str, Any]],
    selected_key: str,
    observed_at: datetime,
) -> dict[str, Any]:
    return {
        "adapter": "express",
        "account_set_key": selected_key,
        "observed_at": observed_at,
        "collector": _collector(body),
        "account_sets": account_sets,
        "masters": _masters(body),
        "form_schema": _form_schema(),
        "capabilities": _capabilities(),
    }


def ingest_express_heartbeat(endpoint_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
    """Publish only complete heartbeat components; absent catalog never clears masters."""
    endpoint_id = str(endpoint_id or "").strip()
    if not endpoint_id or not isinstance(body, Mapping):
        return {"published": False, "reason": "invalid"}
    account_sets = _account_sets(body.get("account_sets"))
    selected_key = _selected_account_set(body)
    account_sets = _ensure_selected_choice(account_sets, body, selected_key)
    has_catalog = isinstance(body.get("catalog"), Mapping)
    request_scope = str(body.get("master_refresh_scope") or "").strip()
    refreshed_account_key = normalize_express_account_key(body.get("master_refresh_account_set"))
    projection_key = (
        refreshed_account_key
        if request_scope == "account_set" and refreshed_account_key
        else selected_key
    )
    projection_key_is_registered = any(row["source_id"] == projection_key for row in account_sets)
    if not account_sets and not (has_catalog and selected_key):
        return {"published": False, "reason": "empty"}

    observed_at = datetime.now(timezone.utc)
    published: dict[str, Any] = {}
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            SELECT ep.id, ep.tenant_id, ep.binding_generation, owner_user.tenant_id AS owner_tenant_id
            FROM erp_endpoints ep
            LEFT JOIN users owner_user ON owner_user.id = ep.user_id
            WHERE ep.id = %s AND ep.adapter = 'express' AND ep.enabled = TRUE
            FOR UPDATE OF ep
            """,
            (endpoint_id,),
        )
        endpoint = cur.fetchone()
        if not endpoint:
            return {"published": False, "reason": "endpoint_not_found"}
        tenant_id = str(endpoint.get("tenant_id") or endpoint.get("owner_tenant_id") or "")
        if not tenant_id:
            return {"published": False, "reason": "tenant_missing"}
        if endpoint.get("tenant_id") is None:
            if int(endpoint.get("binding_generation") or 0) != 0:
                return {"published": False, "reason": "tenant_missing"}
            cur.execute(
                "UPDATE erp_endpoints SET tenant_id = %s WHERE id = %s AND tenant_id IS NULL",
                (tenant_id, endpoint_id),
            )

        request_id = body.get("master_refresh_request_id")
        refresh_error = str(body.get("master_refresh_error") or "").strip()
        if request_id and refresh_error and request_scope in {"endpoint", "account_set"}:
            from services.erp.target_refresh import complete_express_refresh_with_cursor

            complete_express_refresh_with_cursor(
                cur,
                request_id=request_id,
                endpoint_id=endpoint_id,
                account_set_key=projection_key,
                scope_kind=request_scope,
                error_code=refresh_error,
            )

        if account_sets:
            published["endpoint"] = publish_with_cursor(
                cur,
                tenant_id=tenant_id,
                endpoint_id=endpoint_id,
                projection=normalize_projection(
                    _endpoint_observation(body, account_sets, observed_at)
                ),
            )
            if request_id and request_scope == "endpoint" and not refresh_error:
                from services.erp.target_refresh import complete_express_refresh_with_cursor

                complete_express_refresh_with_cursor(
                    cur,
                    request_id=request_id,
                    endpoint_id=endpoint_id,
                    account_set_key=selected_key,
                    scope_kind="endpoint",
                    revision=int(published["endpoint"]["revision"]),
                )
        if has_catalog and projection_key and projection_key_is_registered:
            published["account_set"] = publish_with_cursor(
                cur,
                tenant_id=tenant_id,
                endpoint_id=endpoint_id,
                projection=normalize_projection(
                    _account_observation(body, account_sets, projection_key, observed_at)
                ),
            )
            request_id = body.get("master_refresh_request_id")
            if request_id and request_scope == "account_set" and not refresh_error:
                from services.erp.target_refresh import complete_express_refresh_with_cursor

                complete_express_refresh_with_cursor(
                    cur,
                    request_id=request_id,
                    endpoint_id=endpoint_id,
                    account_set_key=projection_key,
                    scope_kind="account_set",
                    revision=int(published["account_set"]["revision"]),
                )
    return {"published": bool(published), "scopes": published}


__all__ = ["ingest_express_heartbeat", "normalize_express_account_key"]

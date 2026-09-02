# -*- coding: utf-8 -*-
"""Live MR.ERP collector for the canonical target projection."""

from __future__ import annotations

import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from services.erp.erp_mrerp_crud import list_mrerp_customers, list_mrerp_products
from services.erp.erp_mrerp_listing import test_mrerp_endpoint
from services.erp.target_projection_store import (
    load_state,
    publish_projection,
    record_refresh_state,
)

_COLLECTOR = {"kind": "cloud", "adapter_version": "mrerp-live-v1"}
_TRANSIENT_ERRORS = {"ERR_TECHNICAL", "ERR_UNEXPECTED", "ERR_NETWORK"}
_RETRY_DELAY_SECONDS = 2.0


class MRErpProjectionError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def claim_endpoint_tenant_with_cursor(cur, *, tenant_id: str, endpoint_id: str) -> None:
    """Attach a legacy endpoint only to its owner's existing tenant."""
    cur.execute(
        """
        SELECT ep.id, ep.tenant_id
        FROM erp_endpoints ep
        JOIN users owner_user ON owner_user.id = ep.user_id
        WHERE ep.id = %s AND ep.enabled = TRUE AND lower(ep.adapter) = 'mrerp'
          AND owner_user.tenant_id = %s
          AND (ep.tenant_id IS NULL OR ep.tenant_id = %s)
        FOR UPDATE OF ep
        """,
        (endpoint_id, tenant_id, tenant_id),
    )
    endpoint = cur.fetchone()
    if not endpoint:
        raise MRErpProjectionError("erp.endpoint_not_found")
    if endpoint.get("tenant_id") is None:
        cur.execute(
            "UPDATE erp_endpoints SET tenant_id = %s WHERE id = %s AND tenant_id IS NULL",
            (tenant_id, endpoint_id),
        )


def _claim_endpoint_tenant(*, tenant_id: str, endpoint_id: str) -> None:
    from core import db

    with db.get_cursor(commit=True) as cur:
        claim_endpoint_tenant_with_cursor(cur, tenant_id=tenant_id, endpoint_id=endpoint_id)


def _run_live(loader: Callable[[dict[str, Any]], dict[str, Any]], config: dict[str, Any]):
    result: dict[str, Any] = {}
    for attempt in range(2):
        try:
            result = loader(config)
        except Exception:
            result = {"ok": False, "error_code": "ERR_UNEXPECTED"}
        if result.get("ok") or result.get("error_code") not in _TRANSIENT_ERRORS:
            return result
        if attempt == 0:
            time.sleep(_RETRY_DELAY_SECONDS)
    return result


def _account_sets(companies: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for company in companies if isinstance(companies, list) else []:
        if not isinstance(company, Mapping):
            continue
        comidyear = str(company.get("comidyear") or "").strip()
        seldb = str(company.get("seldb") or "").strip()
        if not comidyear or not seldb:
            continue
        source_id = f"{comidyear}:{seldb}"
        rows.append(
            {
                "source_id": source_id,
                "label": str(company.get("label") or source_id).strip() or source_id,
                "attributes": {"comidyear": comidyear, "seldb": seldb},
            }
        )
    return rows


def _selected_account_set(
    account_sets: list[dict[str, Any]], config: Mapping[str, Any], requested_key: str | None
) -> dict[str, Any] | None:
    key = str(requested_key or "").strip()
    if not key:
        comidyear = str(config.get("comidyear") or "").strip()
        seldb = str(config.get("seldb") or "").strip()
        key = f"{comidyear}:{seldb}" if comidyear and seldb else ""
    if not key and len(account_sets) == 1:
        return account_sets[0]
    return next((row for row in account_sets if row["source_id"] == key), None)


def _master_rows(rows: Any, *, kind: str) -> list[dict[str, Any]]:
    projected: list[dict[str, Any]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        source_id = str(row.get("code") or "").strip()
        if not source_id:
            continue
        label = str(row.get("name") or source_id).strip() or source_id
        if kind == "products":
            attributes = {
                "category_code": str(row.get("category_code") or "").strip(),
                "category_name": str(row.get("category_name") or "").strip(),
            }
        else:
            attributes = {
                "type_name": str(row.get("type_name") or "").strip(),
                "prefix": str(row.get("prefix") or "").strip(),
            }
        projected.append({"source_id": source_id, "label": label, "attributes": attributes})
    return projected


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
    ]
    unsupported_fields = {
        "suppliers": "supplier_id",
        "units": "unit_id",
        "branches": "branch_id",
        "accounts": "account_id",
    }
    fields.extend(
        {
            "key": field_key,
            "label": entity.title(),
            "type": "unsupported",
            "visible": False,
            "attributes": {"status": "collector_not_connected"},
        }
        for entity, field_key in unsupported_fields.items()
    )
    return {"fields": fields}


def _capabilities() -> dict[str, Any]:
    actions = [
        {"key": "master.products.read", "label": "Products"},
        {"key": "master.customers.read", "label": "Customers"},
    ]
    actions.extend(
        {
            "key": f"master.{entity}.read",
            "label": entity.title(),
            "enabled": False,
            "block_reason": "erp.target_projection_collector_not_connected",
        }
        for entity in ("suppliers", "units", "branches", "accounts")
    )
    return {"actions": actions}


def _observation(
    *,
    observed_at: datetime,
    account_sets: list[dict[str, Any]],
    account_set_key: str | None = None,
    masters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    observation = {
        "adapter": "mrerp",
        "observed_at": observed_at,
        "collector": _COLLECTOR,
        "account_sets": account_sets,
        "masters": dict(masters or {}),
        "form_schema": _form_schema() if account_set_key else {"fields": []},
        "capabilities": _capabilities() if account_set_key else {"actions": []},
    }
    if account_set_key:
        observation["account_set_key"] = account_set_key
    return observation


def _status_for(error_code: str) -> str:
    return "offline" if error_code in _TRANSIENT_ERRORS else "error"


def _state(
    *, tenant_id: str, user_id: str, endpoint_id: str, account_set_key: str | None
) -> dict[str, Any] | None:
    return load_state(
        tenant_id=tenant_id,
        user_id=user_id,
        endpoint_id=endpoint_id,
        account_set_key=account_set_key,
        entity_types=("products", "customers", "suppliers", "units", "branches", "accounts"),
    )


def _failed(
    *,
    tenant_id: str,
    user_id: str,
    endpoint_id: str,
    account_set_key: str | None,
    observed_at: datetime,
    error_code: str,
) -> dict[str, Any]:
    record_refresh_state(
        tenant_id=tenant_id,
        endpoint_id=endpoint_id,
        account_set_key=account_set_key,
        status=_status_for(error_code),
        observed_at=observed_at,
        collector=_COLLECTOR,
        error_code=error_code,
    )
    return {
        "ok": False,
        "error_code": error_code,
        "data": _state(
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint_id=endpoint_id,
            account_set_key=account_set_key,
        ),
    }


def refresh_mrerp_projection(
    *,
    tenant_id: str,
    user_id: str,
    endpoint: Mapping[str, Any],
    account_set_key: str | None = None,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    """Refresh live account sets, customers and products without wizard caches."""
    endpoint_id = str(endpoint.get("id") or "")
    if str(endpoint.get("adapter") or "").strip().lower() != "mrerp":
        raise MRErpProjectionError("erp.target_projection_adapter_mismatch")
    config = endpoint.get("config") if isinstance(endpoint.get("config"), Mapping) else {}
    config = deepcopy(dict(config))
    timestamp = observed_at or datetime.now(timezone.utc)
    _claim_endpoint_tenant(tenant_id=tenant_id, endpoint_id=endpoint_id)

    account_result = _run_live(test_mrerp_endpoint, config)
    if not account_result.get("ok"):
        return _failed(
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint_id=endpoint_id,
            account_set_key=None,
            observed_at=timestamp,
            error_code=str(account_result.get("error_code") or "ERR_UNEXPECTED"),
        )
    account_sets = _account_sets(account_result.get("companies"))
    if not account_sets:
        return _failed(
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint_id=endpoint_id,
            account_set_key=None,
            observed_at=timestamp,
            error_code="ERR_ACCOUNT_SET_EMPTY",
        )
    catalog = publish_projection(
        tenant_id=tenant_id,
        endpoint_id=endpoint_id,
        observation=_observation(observed_at=timestamp, account_sets=account_sets),
    )

    selected = _selected_account_set(account_sets, config, account_set_key)
    if selected is None:
        requested = str(account_set_key or "").strip() or None
        return {
            **_failed(
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint_id=endpoint_id,
                account_set_key=requested,
                observed_at=timestamp,
                error_code="ERR_ACCOUNT_SET_UNAVAILABLE",
            ),
            "catalog": catalog,
        }
    selected_key = selected["source_id"]
    config.update(selected["attributes"])

    product_result = _run_live(list_mrerp_products, config)
    if not product_result.get("ok"):
        return {
            **_failed(
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint_id=endpoint_id,
                account_set_key=selected_key,
                observed_at=timestamp,
                error_code=str(product_result.get("error_code") or "ERR_UNEXPECTED"),
            ),
            "catalog": catalog,
        }
    customer_result = _run_live(list_mrerp_customers, config)
    if not customer_result.get("ok"):
        return {
            **_failed(
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint_id=endpoint_id,
                account_set_key=selected_key,
                observed_at=timestamp,
                error_code=str(customer_result.get("error_code") or "ERR_UNEXPECTED"),
            ),
            "catalog": catalog,
        }

    projection = publish_projection(
        tenant_id=tenant_id,
        endpoint_id=endpoint_id,
        observation=_observation(
            observed_at=timestamp,
            account_sets=account_sets,
            account_set_key=selected_key,
            masters={
                "products": _master_rows(product_result.get("products"), kind="products"),
                "customers": _master_rows(customer_result.get("customers"), kind="customers"),
            },
        ),
    )
    return {
        "ok": True,
        "error_code": None,
        "catalog": catalog,
        "projection": projection,
        "data": _state(
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint_id=endpoint_id,
            account_set_key=selected_key,
        ),
    }


__all__ = [
    "MRErpProjectionError",
    "claim_endpoint_tenant_with_cursor",
    "refresh_mrerp_projection",
]

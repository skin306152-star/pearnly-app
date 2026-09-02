# -*- coding: utf-8 -*-
"""Canonical ERP target projection payload and stable hashing."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

ENTITY_TYPES = (
    "products",
    "customers",
    "suppliers",
    "units",
    "branches",
    "accounts",
)
FIELD_TYPES = {
    "text",
    "number",
    "date",
    "boolean",
    "select",
    "multiselect",
    "reference",
    "unsupported",
}
FRESH_STATUS = "fresh"
REFRESH_STATUSES = {FRESH_STATUS, "refreshing", "stale", "offline", "error", "unsupported"}
MAX_ACCOUNT_SETS = 1_000
MAX_MASTER_ITEMS = 100_000
MAX_FIELDS = 500
MAX_ACTIONS = 200
_SENSITIVE_KEY = re.compile(
    r"(^|_)(authorization|cookie|credential|password|secret|token)(_|$)", re.IGNORECASE
)


class ProjectionContractError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class NormalizedProjection:
    scope_kind: str
    scope_key: str
    adapter: str
    observed_at: datetime
    collector: dict[str, str]
    account_sets: list[dict[str, Any]]
    masters: dict[str, list[dict[str, Any]]]
    form_schema: dict[str, Any]
    capabilities: dict[str, Any]
    source_hash: str
    component_hashes: dict[str, str]
    entity_counts: dict[str, int]


def _text(value: Any, *, required: bool = False, limit: int = 500) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise ProjectionContractError("erp.target_projection_value_required")
    if len(text) > limit:
        raise ProjectionContractError("erp.target_projection_value_too_long")
    return text


def _safe_json(value: Any, *, key: str = "") -> Any:
    if key and _SENSITIVE_KEY.search(key):
        raise ProjectionContractError("erp.target_projection_sensitive_field")
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ProjectionContractError("erp.target_projection_invalid_number")
        return value
    if isinstance(value, list):
        return [_safe_json(item) for item in value]
    if isinstance(value, Mapping):
        return {
            _text(raw_key, required=True, limit=100): _safe_json(raw_value, key=str(raw_key))
            for raw_key, raw_value in value.items()
        }
    raise ProjectionContractError("erp.target_projection_invalid_json")


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _option(item: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _text(item.get("source_id"), required=True, limit=300)
    return {
        "source_id": source_id,
        "label": _text(item.get("label"), limit=500) or source_id,
        "active": bool(item.get("active", True)),
        "attributes": _safe_json(item.get("attributes") or {}),
    }


def _options(raw: Any, *, limit: int) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > limit:
        raise ProjectionContractError("erp.target_projection_too_large")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ProjectionContractError("erp.target_projection_invalid_option")
        normalized = _option(item)
        source_id = normalized["source_id"]
        if source_id in seen:
            raise ProjectionContractError("erp.target_projection_duplicate_source_id")
        seen.add(source_id)
        result.append(normalized)
    return sorted(result, key=lambda row: row["source_id"])


def _masters(raw: Any) -> dict[str, list[dict[str, Any]]]:
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        raise ProjectionContractError("erp.target_projection_invalid_masters")
    unknown = set(raw) - set(ENTITY_TYPES)
    if unknown:
        raise ProjectionContractError("erp.target_projection_unknown_entity")
    result = {entity: _options(raw.get(entity), limit=MAX_MASTER_ITEMS) for entity in ENTITY_TYPES}
    if sum(len(items) for items in result.values()) > MAX_MASTER_ITEMS:
        raise ProjectionContractError("erp.target_projection_too_large")
    return result


def _form_schema(raw: Any) -> dict[str, Any]:
    raw = raw or {}
    if not isinstance(raw, Mapping):
        raise ProjectionContractError("erp.target_projection_invalid_form_schema")
    fields = raw.get("fields") or []
    if not isinstance(fields, list) or len(fields) > MAX_FIELDS:
        raise ProjectionContractError("erp.target_projection_too_large")
    seen: set[str] = set()
    normalized = []
    for field in fields:
        if not isinstance(field, Mapping):
            raise ProjectionContractError("erp.target_projection_invalid_field")
        key = _text(field.get("key"), required=True, limit=100)
        field_type = _text(field.get("type"), required=True, limit=30).lower()
        if key in seen or field_type not in FIELD_TYPES:
            code = (
                "erp.target_projection_duplicate_field"
                if key in seen
                else "erp.target_projection_unknown_field_type"
            )
            raise ProjectionContractError(code)
        seen.add(key)
        normalized.append(
            {
                "key": key,
                "label": _text(field.get("label"), limit=300) or key,
                "type": field_type,
                "required": bool(field.get("required", False)),
                "visible": bool(field.get("visible", True)),
                "read_only": bool(field.get("read_only", False)),
                "options_source": _text(field.get("options_source"), limit=100) or None,
                "options": _options(field.get("options"), limit=MAX_MASTER_ITEMS),
                "attributes": _safe_json(field.get("attributes") or {}),
            }
        )
    return {"fields": sorted(normalized, key=lambda field: field["key"])}


def _capabilities(raw: Any) -> dict[str, Any]:
    raw = raw or {}
    if not isinstance(raw, Mapping):
        raise ProjectionContractError("erp.target_projection_invalid_capabilities")
    actions = raw.get("actions") or []
    if not isinstance(actions, list) or len(actions) > MAX_ACTIONS:
        raise ProjectionContractError("erp.target_projection_too_large")
    seen: set[str] = set()
    normalized = []
    for action in actions:
        if not isinstance(action, Mapping):
            raise ProjectionContractError("erp.target_projection_invalid_action")
        key = _text(action.get("key"), required=True, limit=100)
        if key in seen:
            raise ProjectionContractError("erp.target_projection_duplicate_action")
        seen.add(key)
        normalized.append(
            {
                "key": key,
                "label": _text(action.get("label"), limit=300) or key,
                "visible": bool(action.get("visible", True)),
                "enabled": bool(action.get("enabled", True)),
                "block_reason": _text(action.get("block_reason"), limit=200) or None,
                "attributes": _safe_json(action.get("attributes") or {}),
            }
        )
    return {"actions": sorted(normalized, key=lambda action: action["key"])}


def _observed_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        observed = value
    else:
        try:
            observed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ProjectionContractError("erp.target_projection_observed_at_invalid") from exc
    if observed.tzinfo is None:
        raise ProjectionContractError("erp.target_projection_observed_at_invalid")
    return observed.astimezone(timezone.utc)


def normalize_scope(account_set_key: Any) -> tuple[str, str]:
    normalized = _text(account_set_key, limit=500)
    return ("account_set", normalized) if normalized else ("endpoint", "@endpoint")


def normalize_collector(raw: Any) -> dict[str, str]:
    raw = raw or {}
    if not isinstance(raw, Mapping):
        raise ProjectionContractError("erp.target_projection_collector_invalid")
    allowed = {"kind", "profile_id", "device_id", "adapter_version"}
    if set(raw) - allowed:
        raise ProjectionContractError("erp.target_projection_collector_invalid")
    collector: dict[str, str] = {}
    for key, value in raw.items():
        normalized = _text(value, limit=200)
        if normalized:
            collector[key] = normalized
    return collector


def normalize_observed_at(value: Any) -> datetime:
    return _observed_at(value)


def normalize_projection(raw: Mapping[str, Any]) -> NormalizedProjection:
    if not isinstance(raw, Mapping):
        raise ProjectionContractError("erp.target_projection_invalid")
    scope_kind, scope_key = normalize_scope(raw.get("account_set_key"))
    adapter = _text(raw.get("adapter"), required=True, limit=30).lower()
    if adapter not in {"mrerp", "express"}:
        raise ProjectionContractError("erp.target_projection_adapter_invalid")
    collector = normalize_collector(raw.get("collector"))
    account_sets = _options(raw.get("account_sets"), limit=MAX_ACCOUNT_SETS)
    masters = _masters(raw.get("masters"))
    form_schema = _form_schema(raw.get("form_schema"))
    capabilities = _capabilities(raw.get("capabilities"))
    components = {
        "account_sets": account_sets,
        "masters": masters,
        "form_schema": form_schema,
        "capabilities": capabilities,
    }
    identity = {
        "scope_kind": scope_kind,
        "scope_key": scope_key,
        "adapter": adapter,
        **components,
    }
    return NormalizedProjection(
        scope_kind=scope_kind,
        scope_key=scope_key,
        adapter=adapter,
        observed_at=_observed_at(raw.get("observed_at")),
        collector=collector,
        account_sets=account_sets,
        masters=masters,
        form_schema=form_schema,
        capabilities=capabilities,
        source_hash=_hash(identity),
        component_hashes={key: _hash(value) for key, value in components.items()},
        entity_counts={entity: len(masters[entity]) for entity in ENTITY_TYPES},
    )


def normalize_refresh_status(status: Any) -> str:
    normalized = _text(status, required=True, limit=30).lower()
    if normalized not in REFRESH_STATUSES or normalized == FRESH_STATUS:
        raise ProjectionContractError("erp.target_projection_refresh_status_invalid")
    return normalized


__all__ = [
    "ENTITY_TYPES",
    "FRESH_STATUS",
    "NormalizedProjection",
    "ProjectionContractError",
    "normalize_collector",
    "normalize_observed_at",
    "normalize_projection",
    "normalize_refresh_status",
    "normalize_scope",
]

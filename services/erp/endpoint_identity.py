"""Canonical identity rules for legacy ERP connections."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any

LegacySpec = tuple[dict[str, Any], dict[str, Any] | None, int, bool]


def mrerp_credential_identity(source: dict[str, Any]) -> tuple[str, str] | None:
    """Return a secret-free identity for an MR.ERP login."""
    raw_config = source.get("config") if "config" in source else source
    config = raw_config if isinstance(raw_config, dict) else {}
    try:
        from services.erp.erp_mrerp_listing import _resolve_creds

        username, password, error = _resolve_creds(config)
    except (ImportError, TypeError, ValueError):
        return None
    if error or not username or not password:
        return None
    system_url = str(config.get("system_url") or "https://www.mrerp4sme.com")
    digest = hashlib.sha256(f"{username}\0{password}".encode()).hexdigest()
    return system_url.rstrip("/").casefold(), digest


def advisory_lock_key(user_id: str, identity: tuple[str, str]) -> int:
    """Map one user's connection identity to a PostgreSQL advisory-lock key."""
    material = f"{user_id}\0{identity[0]}\0{identity[1]}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=True)


def _endpoint_priority(endpoint: dict[str, Any], *, bound: bool) -> tuple[Any, ...]:
    activity = int(endpoint.get("success_count") or 0) + int(endpoint.get("failure_count") or 0)
    return (
        bound,
        activity,
        bool(endpoint.get("is_default")),
        str(endpoint.get("created_at") or ""),
        str(endpoint.get("id") or ""),
    )


def deduplicate_legacy_specs(specs: list[LegacySpec]) -> list[LegacySpec]:
    """Collapse duplicate MR.ERP rows while preserving distinct bound workspaces."""
    groups: dict[int, tuple[str, ...] | None] = {}
    bound_groups: set[tuple[str, ...]] = set()
    for index, spec in enumerate(specs):
        endpoint, workspace, *_ = spec
        adapter = str(endpoint.get("adapter") or "").lower()
        credential = mrerp_credential_identity(endpoint) if adapter == "mrerp" else None
        group = (adapter, *credential) if credential else None
        groups[index] = group
        if group and workspace is not None:
            bound_groups.add(group)

    selected: dict[tuple[Any, ...], tuple[int, tuple[Any, ...], LegacySpec]] = {}
    for index, spec in enumerate(specs):
        endpoint, workspace, *_ = spec
        adapter = str(endpoint.get("adapter") or "").lower()
        credential_group = groups[index]
        if credential_group in bound_groups and workspace is None:
            continue
        workspace_id = str(workspace.get("id")) if workspace else None
        key = (
            (*credential_group, workspace_id)
            if credential_group
            else (adapter, str(endpoint.get("id") or ""), workspace_id)
        )
        priority = _endpoint_priority(endpoint, bound=workspace is not None)
        current = selected.get(key)
        if current is None or priority > current[1]:
            selected[key] = (index if current is None else current[0], priority, spec)
    return [value[2] for value in sorted(selected.values(), key=lambda value: value[0])]


def _binding_ids(endpoint: dict[str, Any]) -> list[str]:
    raw = endpoint.get("_workspace_binding_ids") or []
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes, dict)):
        return []
    return [str(value) for value in raw if value not in (None, "")]


def deduplicate_legacy_endpoints(endpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the shared LINE identity rule to ordinary endpoint lists."""
    specs: list[LegacySpec] = []
    for endpoint in endpoints:
        bindings = _binding_ids(endpoint)
        if bindings:
            specs.extend((endpoint, {"id": binding}, len(bindings), False) for binding in bindings)
        else:
            specs.append((endpoint, None, 0, False))

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for endpoint, *_ in deduplicate_legacy_specs(specs):
        endpoint_id = str(endpoint.get("id") or "")
        if endpoint_id in seen:
            continue
        seen.add(endpoint_id)
        item = dict(endpoint)
        item.pop("_workspace_binding_ids", None)
        unique.append(item)
    return unique


def matching_mrerp_endpoint(
    endpoints: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, Any] | None:
    """Choose the canonical stored row for an incoming MR.ERP login."""
    identity = mrerp_credential_identity(config)
    if identity is None:
        return None
    matches = [
        endpoint for endpoint in endpoints if mrerp_credential_identity(endpoint) == identity
    ]
    if not matches:
        return None
    return max(
        matches,
        key=lambda endpoint: _endpoint_priority(endpoint, bound=bool(_binding_ids(endpoint))),
    )


__all__ = [
    "LegacySpec",
    "advisory_lock_key",
    "deduplicate_legacy_endpoints",
    "deduplicate_legacy_specs",
    "matching_mrerp_endpoint",
    "mrerp_credential_identity",
]

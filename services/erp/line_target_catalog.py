"""Shared ERP target catalogue used by LINE intake channels."""

from __future__ import annotations

import hashlib
from typing import Any

from services.erp import line_target_projection, target_readiness
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for
from services.erp.shared_express_schema import enable_shared_express_select

LegacySpec = tuple[dict[str, Any], dict[str, Any] | None, int, bool]


def _mrerp_credential_identity(endpoint: dict[str, Any]) -> tuple[str, str] | None:
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
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


def _deduplicate_legacy_specs(
    specs: list[LegacySpec],
) -> list[LegacySpec]:
    credential_groups: dict[int, tuple[str, ...] | None] = {}
    bound_groups: set[tuple[str, ...]] = set()
    for index, spec in enumerate(specs):
        endpoint, workspace, *_ = spec
        adapter = str(endpoint.get("adapter") or "").lower()
        credential = _mrerp_credential_identity(endpoint) if adapter == "mrerp" else None
        group = (adapter, *credential) if credential else None
        credential_groups[index] = group
        if group and workspace is not None:
            bound_groups.add(group)

    selected: dict[tuple[Any, ...], tuple[int, tuple[bool, bool, str, str], LegacySpec]] = {}
    for index, spec in enumerate(specs):
        endpoint, workspace, *_ = spec
        adapter = str(endpoint.get("adapter") or "").lower()
        credential_group = credential_groups[index]
        if credential_group in bound_groups and workspace is None:
            continue
        workspace_id = int(workspace["id"]) if workspace else None
        key = (
            (*credential_group, workspace_id)
            if credential_group
            else (adapter, str(endpoint.get("id") or ""), workspace_id)
        )
        priority = (
            workspace is not None,
            bool(endpoint.get("is_default")),
            str(endpoint.get("created_at") or ""),
            str(endpoint.get("id") or ""),
        )
        current = selected.get(key)
        if current is None or priority > current[1]:
            selected[key] = (index if current is None else current[0], priority, spec)
    return [value[2] for value in sorted(selected.values(), key=lambda value: value[0])]


def workspaces(cur, tenant_id: str) -> list[dict[str, Any]]:
    cur.execute(
        "SELECT id, name, erp_endpoint_id FROM workspace_clients "
        "WHERE tenant_id = %s AND is_active = TRUE ORDER BY created_at, id",
        (tenant_id,),
    )
    return [dict(row) for row in (cur.fetchall() or [])]


def managed_targets(
    cur, tenant_id: str, visible_workspaces: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not erp_shared_express_endpoint_enabled_for(tenant_id):
        return []
    targets: list[dict[str, Any]] = []
    for workspace in visible_workspaces:
        workspace_id = int(workspace["id"])
        cur.execute("SELECT set_config('app.current_workspace_id', %s, true)", (str(workspace_id),))
        if not enable_shared_express_select(cur, tenant_id, workspace_id):
            continue
        cur.execute(
            """
            SELECT id, name, adapter, enabled, shared_scope, workspace_client_id,
                   binding_generation, bound_account_set, bound_profile_key,
                   live_account_set, live_profile_key, agent_last_seen_at,
                   agent_version, revoked_at, clock_timestamp() AS server_now
            FROM erp_endpoints
            WHERE tenant_id = %s
              AND workspace_client_id = %s
              AND adapter = 'express'
              AND binding_generation > 0
              AND shared_scope = TRUE
            ORDER BY created_at, id
            """,
            (tenant_id, workspace_id),
        )
        rows = [dict(row) for row in (cur.fetchall() or [])]
        duplicate = len(rows) != 1
        for row in rows:
            cloud_in_flight, waiting_lock = line_target_projection.active_push_state(
                cur, str(row["id"])
            )
            targets.append(
                line_target_projection.managed_target(
                    row,
                    workspace,
                    duplicate=duplicate,
                    cloud_in_flight=cloud_in_flight,
                    waiting_lock=waiting_lock,
                )
            )
    return targets


def legacy_target_specs(
    cur,
    *,
    user_id: str,
    tenant_id: str,
    all_workspaces: list[dict[str, Any]],
    allowed_workspaces: list[dict[str, Any]],
    can_auto_create: bool,
) -> list[LegacySpec]:
    cur.execute(
        """
        SELECT id, name, adapter, config, enabled, last_status, is_default, created_at,
               binding_generation, clock_timestamp() AS server_now
        FROM erp_endpoints
        WHERE user_id = %s
          AND adapter IN ('mrerp', 'express')
          AND binding_generation = 0
          AND (tenant_id IS NULL OR tenant_id = %s)
        ORDER BY is_default DESC, created_at, id
        """,
        (user_id, tenant_id),
    )
    endpoints = [dict(row) for row in (cur.fetchall() or [])]
    all_by_endpoint: dict[str, list[dict[str, Any]]] = {}
    allowed_by_endpoint: dict[str, list[dict[str, Any]]] = {}
    for workspace in all_workspaces:
        endpoint_id = str(workspace.get("erp_endpoint_id") or "")
        if endpoint_id:
            all_by_endpoint.setdefault(endpoint_id, []).append(workspace)
    for workspace in allowed_workspaces:
        endpoint_id = str(workspace.get("erp_endpoint_id") or "")
        if endpoint_id:
            allowed_by_endpoint.setdefault(endpoint_id, []).append(workspace)

    specs: list[LegacySpec] = []
    for endpoint in endpoints:
        endpoint_id = str(endpoint.get("id") or "")
        all_bindings = all_by_endpoint.get(endpoint_id, [])
        visible_bindings = allowed_by_endpoint.get(endpoint_id, [])
        if all_bindings and not visible_bindings:
            continue
        if not visible_bindings:
            specs.append(
                (
                    endpoint,
                    None,
                    len(all_bindings),
                    can_auto_create and not all_bindings,
                )
            )
            continue
        specs.extend(
            (endpoint, workspace, len(all_bindings), False) for workspace in visible_bindings
        )
    return _deduplicate_legacy_specs(specs)


def collect_target_specs(cur, user: dict[str, Any], authz):
    tenant_id = str(user["tenant_id"])
    all_workspaces = workspaces(cur, tenant_id)
    allowed_workspaces = [
        workspace for workspace in all_workspaces if authz.allows_workspace(int(workspace["id"]))
    ]
    targets = managed_targets(cur, tenant_id, allowed_workspaces)
    specs = legacy_target_specs(
        cur,
        user_id=str(user["id"]),
        tenant_id=tenant_id,
        all_workspaces=all_workspaces,
        allowed_workspaces=allowed_workspaces,
        can_auto_create=(authz.has("settings.workspace.manage") and authz.scope_mode != "assigned"),
    )
    return targets, specs


def project_legacy_targets(
    targets: list[dict[str, Any]],
    specs: list[tuple[dict[str, Any], dict[str, Any] | None, int, bool]],
    *,
    refresh_probes: bool = False,
) -> list[dict[str, Any]]:
    probes: dict[str, dict[str, Any]] = {}
    for endpoint, workspace, binding_count, can_auto_create in specs:
        endpoint_id = str(endpoint.get("id") or "")
        if endpoint_id not in probes:
            probes[endpoint_id] = target_readiness.probe_endpoint(
                endpoint,
                refresh=refresh_probes,
            )
        targets.append(
            line_target_projection.legacy_target(
                endpoint,
                workspace,
                binding_count=binding_count,
                can_auto_create=can_auto_create,
                probe=probes[endpoint_id],
            )
        )
    return targets


__all__ = [
    "collect_target_specs",
    "legacy_target_specs",
    "managed_targets",
    "project_legacy_targets",
    "workspaces",
]

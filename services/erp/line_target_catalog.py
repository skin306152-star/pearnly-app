"""Shared ERP target catalogue used by LINE intake channels."""

from __future__ import annotations

from typing import Any

from core.feature_flags import erp_target_projection_enabled_for
from services.erp import line_target_projection, target_readiness
from services.erp.endpoint_identity import LegacySpec, deduplicate_legacy_specs
from services.erp.mrerp_target_projection import refresh_mrerp_account_catalog
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for
from services.erp.shared_express_schema import enable_shared_express_select
from services.erp.target_projection_store import load_state, load_state_with_cursor


def workspaces(cur, tenant_id: str) -> list[dict[str, Any]]:
    cur.execute(
        "SELECT id, name, erp_endpoint_id FROM workspace_clients "
        "WHERE tenant_id = %s AND is_active = TRUE ORDER BY created_at, id",
        (tenant_id,),
    )
    return [dict(row) for row in (cur.fetchall() or [])]


def managed_targets(
    cur,
    tenant_id: str,
    visible_workspaces: list[dict[str, Any]],
    *,
    include_account_catalog: bool = True,
    account_catalog_endpoint_id: str | None = None,
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
                   agent_version, revoked_at,
                   config ->> 'account_set' AS configured_account_set,
                   config ->> 'account_dir' AS configured_account_dir,
                   config ->> 'express_root' AS configured_express_root,
                   config ->> 'account_set_label' AS configured_account_set_label,
                   config ->> 'account_company' AS configured_account_company,
                   clock_timestamp() AS server_now
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
            endpoint_id = str(row["id"])
            load_account_catalog = include_account_catalog and (
                not account_catalog_endpoint_id or endpoint_id == account_catalog_endpoint_id
            )
            projection_state = (
                load_state_with_cursor(
                    cur,
                    tenant_id=tenant_id,
                    endpoint_id=endpoint_id,
                )
                if load_account_catalog
                else None
            )
            projection_snapshot = (projection_state or {}).get("snapshot") or {}
            targets.append(
                line_target_projection.managed_target(
                    row,
                    workspace,
                    duplicate=duplicate,
                    cloud_in_flight=cloud_in_flight,
                    waiting_lock=waiting_lock,
                    account_sets=projection_snapshot.get("account_sets"),
                    account_catalog_loaded=load_account_catalog,
                    projection_revision=projection_snapshot.get("revision"),
                    account_sets_revision=projection_snapshot.get("account_sets_revision"),
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
    return deduplicate_legacy_specs(specs)


def collect_target_specs(
    cur,
    user: dict[str, Any],
    authz,
    *,
    include_account_catalog: bool = True,
    account_catalog_endpoint_id: str | None = None,
):
    tenant_id = str(user["tenant_id"])
    all_workspaces = workspaces(cur, tenant_id)
    allowed_workspaces = [
        workspace for workspace in all_workspaces if authz.allows_workspace(int(workspace["id"]))
    ]
    targets = managed_targets(
        cur,
        tenant_id,
        allowed_workspaces,
        include_account_catalog=include_account_catalog,
        account_catalog_endpoint_id=account_catalog_endpoint_id,
    )
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
    tenant_id: str | None = None,
    user_id: str | None = None,
    include_account_catalog: bool = True,
    account_catalog_endpoint_id: str | None = None,
) -> list[dict[str, Any]]:
    probes: dict[str, dict[str, Any]] = {}
    for endpoint, workspace, binding_count, can_auto_create in specs:
        endpoint_id = str(endpoint.get("id") or "")
        load_account_catalog = include_account_catalog and (
            not account_catalog_endpoint_id or endpoint_id == account_catalog_endpoint_id
        )
        if endpoint_id not in probes:
            probes[endpoint_id] = _projection_probe(
                endpoint,
                tenant_id=tenant_id,
                user_id=user_id,
                refresh=refresh_probes,
                include_account_catalog=load_account_catalog,
            )
        targets.append(
            line_target_projection.legacy_target(
                endpoint,
                workspace,
                binding_count=binding_count,
                can_auto_create=can_auto_create,
                probe=probes[endpoint_id],
                include_account_catalog=load_account_catalog,
            )
        )
    return targets


def _projection_probe(
    endpoint: dict[str, Any],
    *,
    tenant_id: str | None,
    user_id: str | None,
    refresh: bool,
    include_account_catalog: bool = True,
) -> dict[str, Any] | None:
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    enabled = bool(tenant_id and user_id and erp_target_projection_enabled_for(tenant_id, user_id))
    if not include_account_catalog:
        return None
    if adapter == "express" and enabled and include_account_catalog:
        probe = target_readiness.probe_endpoint(endpoint, refresh=False)
        state = load_state(
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            endpoint_id=str(endpoint.get("id") or ""),
        )
        snapshot = (state or {}).get("snapshot") or {}
        if snapshot:
            probe = {
                **probe,
                "account_sets": snapshot.get("account_sets") or [],
                "projection_revision": snapshot.get("revision"),
                "account_sets_revision": snapshot.get("account_sets_revision"),
            }
        return probe
    if adapter != "mrerp" or not enabled:
        return target_readiness.probe_endpoint(endpoint, refresh=refresh)

    refresh_result = None
    if refresh:
        refresh_result = refresh_mrerp_account_catalog(
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            endpoint=endpoint,
        )
    state = load_state(
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        endpoint_id=str(endpoint.get("id") or ""),
    )
    snapshot = (state or {}).get("snapshot") or {}
    freshness = (state or {}).get("freshness") or {}
    if not snapshot and refresh_result is None:
        return target_readiness.probe_endpoint(endpoint, refresh=False)
    account_sets = snapshot.get("account_sets") or []
    companies = [
        {
            "label": row.get("label"),
            "comidyear": (row.get("attributes") or {}).get("comidyear"),
            "seldb": (row.get("attributes") or {}).get("seldb"),
        }
        for row in account_sets
        if isinstance(row, dict)
    ]
    fresh = freshness.get("status") == "fresh" and bool(snapshot)
    if refresh_result is not None:
        fresh = fresh and bool(refresh_result.get("ok"))
    attempted_at = freshness.get("attempted_at")
    return {
        "ok": fresh,
        "error_code": (
            (refresh_result or {}).get("error_code")
            or freshness.get("error_code")
            or (None if fresh else "ERR_TECHNICAL")
        ),
        "companies": companies,
        "elapsed_ms": 0,
        "last_tested_at": (
            attempted_at.isoformat() if hasattr(attempted_at, "isoformat") else attempted_at
        ),
        "cached": not refresh,
        "projection_revision": snapshot.get("revision"),
        "account_sets_revision": snapshot.get("account_sets_revision"),
    }


__all__ = [
    "collect_target_specs",
    "legacy_target_specs",
    "managed_targets",
    "project_legacy_targets",
    "workspaces",
]

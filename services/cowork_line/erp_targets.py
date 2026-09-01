"""Employee-safe ERP target projection for Cowork LINE."""

from __future__ import annotations

from typing import Any

from core import db
from services.authz.resolver import resolve
from services.erp.line_target_projection import (
    active_push_state as _active_push_state,
    legacy_target as _legacy_target,
    managed_target as _managed_target,
)
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp import target_readiness
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for
from services.erp.shared_express_schema import enable_shared_express_select

_VIEW_PERMISSION = "erp.endpoint.view"
_PUSH_PERMISSION = "erp.push.operate"


class CoworkLineErpTargetError(Exception):
    def __init__(self, code: str, *, missing: list[str] | None = None):
        self.code = code
        self.missing = tuple(missing or ())
        super().__init__(code)


def _active_actor(cur, identity: dict[str, Any]):
    membership_id = str(identity.get("membership_id") or "").strip()
    tenant_id = str(identity.get("tenant_id") or "").strip()
    user_id = str(identity.get("user_id") or "").strip()
    if not membership_id or not tenant_id or not user_id:
        raise CoworkLineErpTargetError("identity_inactive")
    cur.execute(
        """
        SELECT i.membership_id, i.tenant_id, i.user_id, u.role, u.invited_by
        FROM cowork_line_identities i
        JOIN memberships m
          ON m.id = i.membership_id
         AND m.user_id = i.user_id
         AND m.tenant_id = i.tenant_id
        JOIN users u ON u.id = i.user_id AND u.tenant_id = i.tenant_id
        WHERE i.membership_id = %s
          AND i.tenant_id = %s
          AND i.user_id = %s
          AND i.revoked_at IS NULL
          AND m.status = 'active'
          AND u.is_active = TRUE
        FOR SHARE OF i, m, u
        """,
        (membership_id, tenant_id, user_id),
    )
    row = cur.fetchone()
    if not row:
        raise CoworkLineErpTargetError("identity_inactive")
    user = {
        "id": str(row["user_id"]),
        "tenant_id": str(row["tenant_id"]),
        "role": row.get("role"),
        "invited_by": row.get("invited_by"),
    }
    authz = resolve(user, cur=cur)
    if str(authz.membership_id or "") != membership_id:
        raise CoworkLineErpTargetError("identity_inactive")
    if not authz.has(_VIEW_PERMISSION) or not authz.has(_PUSH_PERMISSION):
        raise CoworkLineErpTargetError("forbidden")
    return user, authz


def _workspaces(cur, tenant_id: str) -> list[dict[str, Any]]:
    cur.execute(
        "SELECT id, name, erp_endpoint_id FROM workspace_clients "
        "WHERE tenant_id = %s AND is_active = TRUE ORDER BY created_at, id",
        (tenant_id,),
    )
    return [dict(row) for row in (cur.fetchall() or [])]


def _managed_targets(cur, tenant_id: str, workspaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not erp_shared_express_endpoint_enabled_for(tenant_id):
        return []
    targets: list[dict[str, Any]] = []
    for workspace in workspaces:
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
            cloud_in_flight, waiting_lock = _active_push_state(cur, str(row["id"]))
            targets.append(
                _managed_target(
                    row,
                    workspace,
                    duplicate=duplicate,
                    cloud_in_flight=cloud_in_flight,
                    waiting_lock=waiting_lock,
                )
            )
    return targets


def _legacy_target_specs(
    cur,
    *,
    user_id: str,
    tenant_id: str,
    all_workspaces: list[dict[str, Any]],
    allowed_workspaces: list[dict[str, Any]],
    can_auto_create: bool,
) -> list[tuple[dict[str, Any], dict[str, Any] | None, int, bool]]:
    cur.execute(
        """
        SELECT id, name, adapter, config, enabled, last_status,
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

    specs: list[tuple[dict[str, Any], dict[str, Any] | None, int, bool]] = []
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
    return specs


def _project_targets(
    identity: dict[str, Any],
    *,
    lock_endpoint_id: str | None = None,
    refresh_probes: bool = False,
):
    tenant_id = str(identity.get("tenant_id") or "").strip()
    user_id = str(identity.get("user_id") or "").strip()
    with db.get_cursor_rls(tenant_id=tenant_id or None, user_id=user_id or None) as cur:
        if lock_endpoint_id:
            lock_endpoint_binding(cur, lock_endpoint_id)
        user, authz = _active_actor(cur, identity)
        all_workspaces = _workspaces(cur, user["tenant_id"])
        allowed_workspaces = [
            workspace
            for workspace in all_workspaces
            if authz.allows_workspace(int(workspace["id"]))
        ]
        targets = _managed_targets(cur, user["tenant_id"], allowed_workspaces)
        legacy_specs = _legacy_target_specs(
            cur,
            user_id=user["id"],
            tenant_id=user["tenant_id"],
            all_workspaces=all_workspaces,
            allowed_workspaces=allowed_workspaces,
            can_auto_create=(
                authz.has("settings.workspace.manage") and authz.scope_mode != "assigned"
            ),
        )
    probes: dict[str, dict[str, Any]] = {}
    for endpoint, workspace, binding_count, can_auto_create in legacy_specs:
        endpoint_id = str(endpoint.get("id") or "")
        if endpoint_id not in probes:
            probes[endpoint_id] = target_readiness.probe_endpoint(
                endpoint,
                refresh=refresh_probes,
            )
        targets.append(
            _legacy_target(
                endpoint,
                workspace,
                binding_count=binding_count,
                can_auto_create=can_auto_create,
                probe=probes[endpoint_id],
            )
        )
    return targets


def list_targets(identity: dict[str, Any]) -> list[dict[str, Any]]:
    """List only ERP targets currently visible to this active LINE member."""
    return _project_targets(identity)


def require_target(
    identity: dict[str, Any],
    endpoint_id: str,
    workspace_client_id: int | None = None,
    *,
    refresh_probe: bool = False,
) -> dict[str, Any]:
    """Re-read and lock a target before a later push flow accepts the selection."""
    endpoint_id = str(endpoint_id or "").strip()
    if not endpoint_id:
        raise CoworkLineErpTargetError("target_not_found")
    project_kwargs: dict[str, Any] = {"lock_endpoint_id": endpoint_id}
    if refresh_probe:
        project_kwargs["refresh_probes"] = True
    targets = _project_targets(identity, **project_kwargs)
    matches = [target for target in targets if target["endpoint_id"] == endpoint_id]
    if workspace_client_id is not None:
        matches = [
            target
            for target in matches
            if target["workspace_client_id"] == int(workspace_client_id)
        ]
    if not matches:
        raise CoworkLineErpTargetError("target_not_found")
    if len(matches) != 1:
        raise CoworkLineErpTargetError("target_ambiguous")
    target = matches[0]
    if not target["selectable"]:
        raise CoworkLineErpTargetError("target_not_ready", missing=target["missing"])
    return target


def _selected_target(identity: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    endpoint_id = str(target.get("endpoint_id") or "").strip()
    workspace_id = target.get("workspace_client_id")
    return require_target(identity, endpoint_id, workspace_id)


def _history_party(history: dict[str, Any], direction: str) -> tuple[str, str]:
    from services.erp.erp_payload import flatten_history_for_mrerp

    flat = flatten_history_for_mrerp(history)
    fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
    prefix = "seller" if direction == "sales" else "buyer"
    tax_id = str(fields.get(f"{prefix}_tax") or fields.get(f"{prefix}_tax_id") or "").strip()
    name = str(fields.get(f"{prefix}_name") or "").strip()
    return tax_id, name


def _route_workspace(
    *, direction: str, tax_id: str, name: str, user_id: str, tenant_id: str
) -> dict[str, Any]:
    if direction == "sales":
        return db.match_workspace_for_seller(tax_id, name, user_id, tenant_id)
    return db.match_workspace_for_buyer(tax_id, name, user_id, tenant_id)


def _workspace_permission(identity: dict[str, Any]):
    tenant_id = str(identity.get("tenant_id") or "").strip()
    user_id = str(identity.get("user_id") or "").strip()
    with db.get_cursor_rls(tenant_id=tenant_id or None, user_id=user_id or None) as cur:
        user, authz = _active_actor(cur, identity)
    if not authz.has("settings.workspace.manage") or authz.scope_mode == "assigned":
        raise CoworkLineErpTargetError("workspace_manage_forbidden")
    return user


def resolve_history_workspace(
    identity: dict[str, Any],
    target: dict[str, Any],
    history_ids: list[str],
    direction: str,
    *,
    provisional_history_assignment: bool = False,
) -> dict[str, Any]:
    """Preserve or establish one Pearnly workspace for an explicitly selected batch."""
    direction = str(direction or "").strip().lower()
    if direction not in {"purchase", "sales"}:
        raise CoworkLineErpTargetError("direction_required")
    ids = list(
        dict.fromkeys(str(value).strip() for value in history_ids or [] if str(value).strip())
    )
    if not ids:
        raise CoworkLineErpTargetError("history_required")
    fresh_target = _selected_target(identity, target)
    user_id = str(identity.get("user_id") or "")
    tenant_id = str(identity.get("tenant_id") or "")
    histories = db.get_ocr_history_details_bulk(user_id, ids, tenant_id=tenant_id)
    if len(histories) != len(ids):
        raise CoworkLineErpTargetError("history_not_found")

    may_reassign = provisional_history_assignment
    existing_ids = {
        int(history["workspace_client_id"])
        for history in histories.values()
        if history.get("workspace_client_id") is not None and not may_reassign
    }
    if len(existing_ids) > 1:
        raise CoworkLineErpTargetError("history_workspace_mismatch")
    target_workspace = fresh_target.get("workspace_client_id")
    if existing_ids and target_workspace is not None and int(target_workspace) not in existing_ids:
        raise CoworkLineErpTargetError("history_workspace_mismatch")

    subjects: set[tuple[str, str]] = set()
    routed_ids: set[int] = set()
    for history_id in ids:
        history = histories[history_id]
        if may_reassign and target_workspace is not None:
            continue
        if history.get("workspace_client_id") is not None and not may_reassign:
            continue
        tax_id, name = _history_party(history, direction)
        route = _route_workspace(
            direction=direction,
            tax_id=tax_id,
            name=name,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        action = route.get("action")
        if action == "multi":
            raise CoworkLineErpTargetError("workspace_ambiguous")
        if route.get("reason") == "lookup_error":
            raise CoworkLineErpTargetError("workspace_lookup_failed")
        routed = route.get("workspace_client_id") if action in {"assigned", "unbound"} else None
        if routed is not None:
            routed_ids.add(int(routed))
        else:
            normalized_tax = tax_id.replace("-", "").replace(" ", "")
            normalized_name = " ".join(name.casefold().split())
            if not normalized_tax and not normalized_name:
                raise CoworkLineErpTargetError("workspace_subject_missing")
            subjects.add((normalized_tax, normalized_name))
    if len(routed_ids) > 1 or len(subjects) > 1 or (routed_ids and subjects):
        raise CoworkLineErpTargetError("workspace_ambiguous")

    chosen = next(iter(existing_ids or routed_ids), None)
    if target_workspace is not None:
        if chosen is not None and chosen != int(target_workspace):
            raise CoworkLineErpTargetError("history_workspace_mismatch")
        chosen = int(target_workspace)
    elif chosen is not None:
        _workspace_permission(identity)
        if not db.bind_workspace_endpoint(chosen, fresh_target["endpoint_id"], user_id, tenant_id):
            raise CoworkLineErpTargetError("workspace_binding_failed")
    else:
        user = _workspace_permission(identity)
        tax_id, name = _history_party(histories[ids[0]], direction)
        if not name:
            raise CoworkLineErpTargetError("workspace_subject_missing")
        chosen = db.create_workspace_client(
            user["id"],
            user["tenant_id"],
            name,
            tax_id=tax_id or None,
            erp_endpoint_id=fresh_target["endpoint_id"],
        )
        if chosen is None:
            raise CoworkLineErpTargetError("workspace_create_failed")

    for history_id in ids:
        history = histories[history_id]
        if history.get("workspace_client_id") is not None and not may_reassign:
            continue
        if not db.update_history_workspace_client_id(history_id, chosen, user_id, tenant_id):
            raise CoworkLineErpTargetError("history_workspace_update_failed")
    return require_target(identity, fresh_target["endpoint_id"], int(chosen))


def preflight_document(identity, target, history_id, direction, posting_kind=None, payment=None):
    from services.cowork_line.document_preflight import preflight_document as run

    return run(identity, target, history_id, direction, posting_kind, payment)


__all__ = [
    "CoworkLineErpTargetError",
    "resolve_history_workspace",
    "list_targets",
    "preflight_document",
    "require_target",
]

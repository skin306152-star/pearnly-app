"""Employee-safe ERP target projection for Cowork LINE."""

from __future__ import annotations

from typing import Any

from core import db
from services.authz.resolver import resolve
from services.erp import line_history_workspace, line_target_catalog, line_target_projection
from services.erp.legacy_generation import lock_endpoint_binding

_VIEW_PERMISSION = "erp.endpoint.view"
_PUSH_PERMISSION = "erp.push.operate"
_active_push_state = line_target_projection.active_push_state
_legacy_target = line_target_projection.legacy_target
_managed_target = line_target_projection.managed_target


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


_workspaces = line_target_catalog.workspaces
_managed_targets = line_target_catalog.managed_targets
_legacy_target_specs = line_target_catalog.legacy_target_specs


def _project_targets(
    identity: dict[str, Any],
    *,
    lock_endpoint_id: str | None = None,
    refresh_probes: bool = False,
    include_account_catalog: bool = True,
):
    tenant_id = str(identity.get("tenant_id") or "").strip()
    user_id = str(identity.get("user_id") or "").strip()
    with db.get_cursor_rls(tenant_id=tenant_id or None, user_id=user_id or None) as cur:
        if lock_endpoint_id:
            lock_endpoint_binding(cur, lock_endpoint_id)
        user, authz = _active_actor(cur, identity)
        targets, legacy_specs = line_target_catalog.collect_target_specs(
            cur,
            user,
            authz,
            include_account_catalog=include_account_catalog,
            account_catalog_endpoint_id=lock_endpoint_id,
        )
    return line_target_catalog.project_legacy_targets(
        targets,
        legacy_specs,
        refresh_probes=refresh_probes,
        tenant_id=tenant_id,
        user_id=user_id,
        include_account_catalog=include_account_catalog,
        account_catalog_endpoint_id=lock_endpoint_id,
    )


def list_targets(
    identity: dict[str, Any],
    *,
    refresh: bool = False,
    include_account_catalog: bool = True,
) -> list[dict[str, Any]]:
    """List only ERP targets currently visible to this active LINE member."""
    return _project_targets(
        identity,
        refresh_probes=refresh,
        include_account_catalog=include_account_catalog,
    )


def require_target(
    identity: dict[str, Any],
    endpoint_id: str,
    workspace_client_id: int | None = None,
    *,
    refresh_probe: bool = False,
    include_account_catalog: bool = True,
) -> dict[str, Any]:
    """Re-read and lock a target before a later push flow accepts the selection."""
    endpoint_id = str(endpoint_id or "").strip()
    if not endpoint_id:
        raise CoworkLineErpTargetError("target_not_found")
    project_kwargs: dict[str, Any] = {
        "lock_endpoint_id": endpoint_id,
        "include_account_catalog": include_account_catalog,
    }
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
    workspace_id = (
        target.get("connection_workspace_client_id")
        if "connection_workspace_client_id" in target
        else target.get("workspace_client_id")
    )
    return require_target(identity, endpoint_id, workspace_id)


def _finalized_target(identity: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    fresh = _selected_target(identity, target)
    return {
        **fresh,
        "connection_workspace_client_id": fresh.get("workspace_client_id"),
        "workspace_client_id": target.get("workspace_client_id"),
    }


_history_party = line_history_workspace._history_party
_route_workspace = line_history_workspace._route_workspace


def _workspace_permission(identity: dict[str, Any]):
    tenant_id = str(identity.get("tenant_id") or "").strip()
    user_id = str(identity.get("user_id") or "").strip()
    with db.get_cursor_rls(tenant_id=tenant_id or None, user_id=user_id or None) as cur:
        user, authz = _active_actor(cur, identity)
    if not authz.has("settings.workspace.manage") or authz.scope_mode == "assigned":
        raise CoworkLineErpTargetError("workspace_manage_forbidden")
    return user


def _workspace_access(identity: dict[str, Any], workspace_client_id: int) -> None:
    tenant_id = str(identity.get("tenant_id") or "").strip()
    user_id = str(identity.get("user_id") or "").strip()
    with db.get_cursor_rls(tenant_id=tenant_id or None, user_id=user_id or None) as cur:
        _user, authz = _active_actor(cur, identity)
    if not authz.allows_workspace(workspace_client_id):
        raise CoworkLineErpTargetError("workspace_scope_forbidden")


def resolve_history_workspace(
    identity: dict[str, Any],
    target: dict[str, Any],
    history_ids: list[str],
    direction: str,
    *,
    provisional_history_assignment: bool = False,
) -> dict[str, Any]:
    """Preserve or establish one Pearnly workspace for an explicitly selected batch."""
    return line_history_workspace.resolve(
        identity,
        target,
        history_ids,
        direction,
        select_target=_selected_target,
        require_workspace_actor=_workspace_permission,
        error_type=CoworkLineErpTargetError,
        authorize_workspace=_workspace_access,
        history_party=_history_party,
        route_workspace=_route_workspace,
        finalize_target=_finalized_target,
        provisional_history_assignment=provisional_history_assignment,
    )


def preflight_document(
    identity,
    target,
    history_id,
    direction,
    posting_kind=None,
    payment=None,
    account_config=None,
):
    from services.cowork_line.document_preflight import preflight_document as run

    return run(
        identity,
        target,
        history_id,
        direction,
        posting_kind,
        payment,
        account_config,
    )


__all__ = [
    "CoworkLineErpTargetError",
    "resolve_history_workspace",
    "list_targets",
    "preflight_document",
    "require_target",
]

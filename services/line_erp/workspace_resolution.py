"""Cowork-compatible workspace resolution for ERP LINE drafts."""

from __future__ import annotations

from typing import Any

from core import db
from services.authz.resolver import resolve as resolve_authz
from services.erp import line_history_workspace
from services.line_erp import target_preflight


class WorkspaceResolutionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _workspace_actor(binding: dict[str, Any]) -> dict[str, Any]:
    user = target_preflight._active_user(binding)
    with db.get_cursor_rls(
        tenant_id=str(binding.get("tenant_id") or ""),
        user_id=str(binding.get("user_id") or ""),
    ) as cur:
        authz = resolve_authz(user, cur=cur)
    if not authz.has("settings.workspace.manage") or authz.scope_mode == "assigned":
        raise WorkspaceResolutionError("workspace_manage_forbidden")
    return user


def _workspace_access(binding: dict[str, Any], workspace_client_id: int) -> None:
    user = target_preflight._active_user(binding)
    with db.get_cursor_rls(
        tenant_id=str(binding.get("tenant_id") or ""),
        user_id=str(binding.get("user_id") or ""),
    ) as cur:
        authz = resolve_authz(user, cur=cur)
    if not authz.allows_workspace(workspace_client_id):
        raise WorkspaceResolutionError("workspace_scope_forbidden")


def resolve_history_workspace(
    binding: dict[str, Any],
    target: dict[str, Any],
    history_ids: list[str],
    direction: str,
    *,
    provisional_history_assignment: bool = False,
) -> dict[str, Any]:
    identity = {
        "tenant_id": str(binding.get("tenant_id") or ""),
        "user_id": str(binding.get("user_id") or ""),
    }

    def selected(_identity: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        connection_workspace_id = (
            candidate.get("connection_workspace_client_id")
            if "connection_workspace_client_id" in candidate
            else candidate.get("workspace_client_id")
        )
        result = target_preflight.require_ready(
            binding,
            endpoint_id=str(candidate.get("endpoint_id") or ""),
            workspace_client_id=connection_workspace_id,
        )
        return dict(result["target"])

    def finalized(_identity: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        fresh = selected(_identity, candidate)
        return {
            **fresh,
            "connection_workspace_client_id": fresh.get("workspace_client_id"),
            "workspace_client_id": candidate.get("workspace_client_id"),
        }

    return line_history_workspace.resolve(
        identity,
        target,
        history_ids,
        direction,
        select_target=selected,
        require_workspace_actor=lambda _identity: _workspace_actor(binding),
        error_type=WorkspaceResolutionError,
        authorize_workspace=lambda _identity, workspace_id: _workspace_access(
            binding, workspace_id
        ),
        finalize_target=finalized,
        provisional_history_assignment=provisional_history_assignment,
    )


__all__ = ["WorkspaceResolutionError", "resolve_history_workspace"]

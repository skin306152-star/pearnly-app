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
        result = target_preflight.require_ready(
            binding,
            endpoint_id=str(candidate.get("endpoint_id") or ""),
            workspace_client_id=candidate.get("workspace_client_id"),
        )
        return dict(result["target"])

    return line_history_workspace.resolve(
        identity,
        target,
        history_ids,
        direction,
        select_target=selected,
        require_workspace_actor=lambda _identity: _workspace_actor(binding),
        error_type=WorkspaceResolutionError,
        provisional_history_assignment=provisional_history_assignment,
    )


__all__ = ["WorkspaceResolutionError", "resolve_history_workspace"]

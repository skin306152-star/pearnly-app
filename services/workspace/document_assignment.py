"""Resolve or create the Pearnly workspace that owns an OCR document."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any


class WorkspaceAssignmentError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _normalize_tax_id(value: Any) -> str:
    return re.sub(r"[-\s]+", "", str(value or ""))


def document_subject(fields: dict[str, Any], direction: str) -> dict[str, str]:
    normalized_direction = str(direction or "").strip().lower()
    if normalized_direction not in {"purchase", "sales"}:
        raise WorkspaceAssignmentError("direction_required")

    values = fields if isinstance(fields, dict) else {}
    prefix = "seller" if normalized_direction == "sales" else "buyer"
    tax_id = values.get(f"{prefix}_tax") or values.get(f"{prefix}_tax_id")
    return {
        "tax_id": _normalize_tax_id(tax_id),
        "name": str(values.get(f"{prefix}_name") or "").strip(),
    }


def _default_route_workspace(
    *, direction: str, tax_id: str, name: str, user_id: str, tenant_id: str | None
) -> dict[str, Any]:
    from core import db

    if direction == "sales":
        return db.match_workspace_for_seller(tax_id, name, user_id, tenant_id)
    return db.match_workspace_for_buyer(tax_id, name, user_id, tenant_id)


def _default_create_workspace(
    user_id: str,
    tenant_id: str | None,
    name: str,
    *,
    tax_id: str | None,
    erp_endpoint_id: None,
) -> int | None:
    from core import db

    return db.create_workspace_client(
        user_id,
        tenant_id,
        name,
        tax_id=tax_id,
        erp_endpoint_id=erp_endpoint_id,
    )


def _workspace_id(value: Any) -> int | None:
    try:
        workspace_client_id = int(value)
    except (TypeError, ValueError):
        return None
    return workspace_client_id if workspace_client_id > 0 else None


def _matched_result(
    route: dict[str, Any] | None,
    subject: dict[str, str],
    *,
    action: str,
) -> dict[str, Any] | None:
    candidate = route if isinstance(route, dict) else {}
    route_action = str(candidate.get("action") or "").strip().lower()
    if candidate.get("reason") == "lookup_error":
        raise WorkspaceAssignmentError("workspace_lookup_failed")
    if route_action == "multi":
        raise WorkspaceAssignmentError("workspace_ambiguous")
    if route_action in {"assigned", "unbound"}:
        workspace_client_id = _workspace_id(candidate.get("workspace_client_id"))
        if workspace_client_id is None:
            raise WorkspaceAssignmentError("workspace_lookup_failed")
        return {
            "workspace_client_id": workspace_client_id,
            "action": action,
            "workspace_name": str(candidate.get("workspace_name") or subject["name"]).strip(),
            "subject": dict(subject),
        }
    if route_action not in {"", "none"}:
        raise WorkspaceAssignmentError("workspace_lookup_failed")
    return None


def _authorize(
    decision: dict[str, Any], authorize_workspace: Callable[[int], Any] | None
) -> dict[str, Any]:
    if authorize_workspace is not None:
        authorize_workspace(int(decision["workspace_client_id"]))
    return decision


def prepare_assignment(
    fields: dict[str, Any],
    direction: str,
    user_id: str,
    tenant_id: str | None,
    *,
    require_create_actor: Callable[[], Any] | None = None,
    authorize_workspace: Callable[[int], Any] | None = None,
    route_workspace: Callable[..., dict[str, Any]] = _default_route_workspace,
) -> dict[str, Any]:
    """Validate one assignment without creating a workspace."""
    normalized_direction = str(direction or "").strip().lower()
    subject = document_subject(fields, normalized_direction)
    if not subject["tax_id"] and not subject["name"]:
        raise WorkspaceAssignmentError("workspace_subject_missing")

    route = route_workspace(
        direction=normalized_direction,
        tax_id=subject["tax_id"],
        name=subject["name"],
        user_id=str(user_id),
        tenant_id=tenant_id,
    )
    matched = _matched_result(route, subject, action="matched")
    if matched is not None:
        return _authorize(matched, authorize_workspace)

    if not subject["name"]:
        raise WorkspaceAssignmentError("workspace_subject_missing")
    if require_create_actor is not None:
        require_create_actor()
    return {
        "workspace_client_id": None,
        "action": "create",
        "workspace_name": subject["name"],
        "subject": dict(subject),
        "direction": normalized_direction,
    }


def materialize_assignment(
    prepared: dict[str, Any],
    user_id: str,
    tenant_id: str | None,
    *,
    authorize_workspace: Callable[[int], Any] | None = None,
    route_workspace: Callable[..., dict[str, Any]] = _default_route_workspace,
    create_workspace: Callable[..., int | None] = _default_create_workspace,
) -> dict[str, Any]:
    """Create a prepared missing workspace, handling a concurrent winner."""
    existing_id = _workspace_id(prepared.get("workspace_client_id"))
    if existing_id is not None:
        return dict(prepared)
    if prepared.get("action") != "create":
        raise WorkspaceAssignmentError("workspace_lookup_failed")
    subject = prepared.get("subject") if isinstance(prepared.get("subject"), dict) else {}
    direction = str(prepared.get("direction") or "").strip().lower()
    if direction not in {"purchase", "sales"} or not subject.get("name"):
        raise WorkspaceAssignmentError("workspace_subject_missing")

    created = create_workspace(
        str(user_id),
        tenant_id,
        str(subject["name"]),
        tax_id=str(subject.get("tax_id") or "") or None,
        erp_endpoint_id=None,
    )
    workspace_client_id = _workspace_id(created)
    if workspace_client_id is not None:
        return _authorize(
            {
                "workspace_client_id": workspace_client_id,
                "action": "created",
                "workspace_name": str(subject["name"]),
                "subject": dict(subject),
            },
            authorize_workspace,
        )

    raced_route = route_workspace(
        direction=direction,
        tax_id=str(subject.get("tax_id") or ""),
        name=str(subject["name"]),
        user_id=str(user_id),
        tenant_id=tenant_id,
    )
    raced = _matched_result(raced_route, subject, action="raced")
    if raced is not None:
        return _authorize(raced, authorize_workspace)
    raise WorkspaceAssignmentError("workspace_create_failed")


def resolve_or_create(
    fields: dict[str, Any],
    direction: str,
    user_id: str,
    tenant_id: str | None,
    *,
    require_create_actor: Callable[[], Any] | None = None,
    authorize_workspace: Callable[[int], Any] | None = None,
    route_workspace: Callable[..., dict[str, Any]] = _default_route_workspace,
    create_workspace: Callable[..., int | None] = _default_create_workspace,
) -> dict[str, Any]:
    prepared = prepare_assignment(
        fields,
        direction,
        user_id,
        tenant_id,
        require_create_actor=require_create_actor,
        authorize_workspace=authorize_workspace,
        route_workspace=route_workspace,
    )
    return materialize_assignment(
        prepared,
        user_id,
        tenant_id,
        authorize_workspace=authorize_workspace,
        route_workspace=route_workspace,
        create_workspace=create_workspace,
    )


__all__ = [
    "WorkspaceAssignmentError",
    "document_subject",
    "materialize_assignment",
    "prepare_assignment",
    "resolve_or_create",
]

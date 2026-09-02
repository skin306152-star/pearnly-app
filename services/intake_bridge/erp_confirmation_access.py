# -*- coding: utf-8 -*-
"""Pre-write access contract for flag-gated ERP formal-document confirmation."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException

from core import db
from core import workspace_context as wc
from services.auth.entrance import require_erp_portal
from services.authz.deps import check_workspace_scope, require_perm
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for
from services.intake_bridge import convert as convert_svc

_DIRECTION_PERMISSIONS = {
    "purchase": ("purchase.doc.create", "purchase.doc.approve"),
    "sales": ("sales.doc.create", "sales.doc.approve"),
}
_SHARED_CONFIRMATION_ENTRIES = frozenset({"main", "cowork", "erp"})


@dataclass(frozen=True)
class ConfirmationPreflight:
    directions: tuple[str, ...]
    required_permissions: tuple[str, ...]
    history_directions: tuple[tuple[str, str], ...] = ()


def is_shared_confirmation_context(user: dict, tenant_id: str) -> bool:
    """Select the F1 branch only for an explicit supported web entrance and enabled tenant."""
    if user.get("entry") not in _SHARED_CONFIRMATION_ENTRIES:
        return False
    return erp_shared_express_endpoint_enabled_for(tenant_id)


def guard_confirmation(cur, request, user, tenant_id, workspace_client_id, history_ids):
    """Keep the legacy gate when disabled; otherwise enforce the full batch preflight."""
    if not is_shared_confirmation_context(user, tenant_id):
        wc.assert_workspace_in_tenant(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        return None
    require_erp_portal(user)
    return _shared_preflight(cur, request, user, tenant_id, workspace_client_id, history_ids)


def commit_shared_confirmation(request, user, tenant_id, history_ids) -> int | None:
    """Atomically validate and finish flag-on shared formal confirmations."""
    if not is_shared_confirmation_context(user, tenant_id):
        return None
    require_erp_portal(user)
    actor_id = str(user["id"])
    ids = _history_ids(history_ids)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        workspace_client_id = _snapshot_commit_workspace(
            cur, tenant_id=tenant_id, actor_id=actor_id, history_ids=ids
        )
        preflight = _shared_preflight(cur, request, user, tenant_id, workspace_client_id, ids)
        _require_formal_conversion(
            cur,
            preflight=preflight,
            tenant_id=tenant_id,
            actor_id=actor_id,
            workspace_client_id=workspace_client_id,
            history_ids=ids,
        )
        cur.execute(
            "UPDATE ocr_history SET staged = FALSE, updated_at = NOW() "
            "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
            "AND user_id = %s::uuid AND workspace_client_id = %s AND staged = TRUE",
            (ids, tenant_id, actor_id, workspace_client_id),
        )
        return int(cur.rowcount or 0)


def _shared_preflight(
    cur,
    request,
    user,
    tenant_id,
    workspace_client_id,
    history_ids,
    *,
    lock_histories: bool = True,
):
    check_workspace_scope(request, user, workspace_client_id)
    preflight_args = {
        "tenant_id": tenant_id,
        "actor_id": str(user["id"]),
        "workspace_client_id": workspace_client_id,
        "history_ids": history_ids,
    }
    if not lock_histories:
        preflight_args["lock_histories"] = False
    preflight = preflight_confirmation(cur, **preflight_args)
    for permission in preflight.required_permissions:
        require_perm(request, permission)
    return preflight


def confirmation_status(cur, request, user, tenant_id, workspace_client_id, history_ids) -> dict:
    """Read the canonical formal-document state without replaying confirmation writes."""
    require_erp_portal(user)
    ids = _history_ids(history_ids)
    preflight = _shared_preflight(
        cur,
        request,
        user,
        tenant_id,
        workspace_client_id,
        ids,
        lock_histories=False,
    )
    converted = _formal_history_ids_by_direction(
        cur,
        tenant_id=tenant_id,
        actor_id=str(user["id"]),
        workspace_client_id=int(workspace_client_id),
        history_ids=ids,
    )
    directions = dict(preflight.history_directions)
    resolved = [history_id for history_id in ids if history_id in converted[directions[history_id]]]
    unresolved = [history_id for history_id in ids if history_id not in resolved]
    return {"resolved": resolved, "unresolved": unresolved}


def finish_resolved_histories(
    cur, preflight, tenant_id, actor_id, workspace_client_id, history_ids
) -> None:
    """Keep the legacy update off-flag; bind actor and workspace on the shared path."""
    if preflight is None:
        cur.execute(
            "UPDATE ocr_history SET staged = FALSE, updated_at = NOW() "
            "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
            "AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)",
            (list(history_ids), tenant_id, tenant_id),
        )
        return
    _require_formal_conversion(
        cur,
        preflight=preflight,
        tenant_id=tenant_id,
        actor_id=actor_id,
        workspace_client_id=int(workspace_client_id),
        history_ids=list(history_ids),
    )
    cur.execute(
        "UPDATE ocr_history SET staged = FALSE, updated_at = NOW() "
        "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
        "AND user_id = %s::uuid AND workspace_client_id = %s",
        (list(history_ids), tenant_id, actor_id, int(workspace_client_id)),
    )


def _history_ids(values: list) -> list[str]:
    ids = []
    seen = set()
    for value in values or []:
        try:
            history_id = str(UUID(str(value)))
        except (TypeError, ValueError, AttributeError):
            raise HTTPException(404, detail="history.not_found") from None
        if history_id not in seen:
            seen.add(history_id)
            ids.append(history_id)
    if not ids:
        raise HTTPException(404, detail="history.not_found")
    return ids


def _snapshot_commit_workspace(
    cur, *, tenant_id: str, actor_id: str, history_ids: list[str]
) -> int:
    """Snapshot the actor-owned batch workspace; preflight then locks workspace before history."""
    cur.execute(
        "SELECT id::text AS id, workspace_client_id FROM ocr_history "
        "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid AND user_id = %s::uuid "
        "ORDER BY id",
        (history_ids, tenant_id, actor_id),
    )
    rows = cur.fetchall() or []
    if len({str(row["id"]) for row in rows}) != len(history_ids):
        raise HTTPException(404, detail="history.not_found")
    try:
        workspaces = {int(row.get("workspace_client_id")) for row in rows}
    except (TypeError, ValueError):
        raise HTTPException(404, detail="history.not_found") from None
    if len(workspaces) != 1:
        raise HTTPException(404, detail="history.not_found")
    return workspaces.pop()


def _require_formal_conversion(
    cur,
    *,
    preflight: ConfirmationPreflight,
    tenant_id: str,
    actor_id: str,
    workspace_client_id: int,
    history_ids: list[str],
) -> None:
    """Require the canonical formal document created by this actor in this workspace."""
    converted = _formal_history_ids_by_direction(
        cur,
        tenant_id=tenant_id,
        actor_id=actor_id,
        workspace_client_id=workspace_client_id,
        history_ids=history_ids,
    )
    requested = set(history_ids)
    missing = [
        history_id
        for history_id, direction in preflight.history_directions
        if history_id in requested and history_id not in converted[direction]
    ]
    known_directions = dict(preflight.history_directions)
    missing.extend(history_id for history_id in history_ids if history_id not in known_directions)
    if missing:
        raise HTTPException(
            409,
            detail={
                "code": "erp.formal_document_required",
                "history_ids": list(dict.fromkeys(missing)),
            },
        )


def _formal_history_ids_by_direction(
    cur, *, tenant_id: str, actor_id: str, workspace_client_id: int, history_ids: list[str]
) -> dict[str, set[str]]:
    cur.execute(
        "SELECT ocr_history_id::text AS history_id FROM purchase_docs "
        "WHERE tenant_id = %s::uuid AND workspace_client_id = %s "
        "AND created_by = %s::uuid AND status = 'posted' "
        "AND ocr_history_id = ANY(%s::uuid[]) FOR SHARE",
        (tenant_id, workspace_client_id, actor_id, history_ids),
    )
    purchase_ids = {str(row["history_id"]) for row in cur.fetchall() or []}
    cur.execute(
        "SELECT ocr_history_id::text AS history_id FROM sales_documents "
        "WHERE tenant_id = %s::uuid AND seller_workspace_client_id = %s "
        "AND created_by = %s::uuid AND status = 'issued' "
        "AND ocr_history_id = ANY(%s::uuid[]) FOR SHARE",
        (tenant_id, workspace_client_id, actor_id, history_ids),
    )
    sales_ids = {str(row["history_id"]) for row in cur.fetchall() or []}
    return {"purchase": purchase_ids, "sales": sales_ids}


def preflight_confirmation(
    cur,
    *,
    tenant_id: str,
    actor_id: str,
    workspace_client_id: int,
    history_ids: list,
    lock_histories: bool = True,
) -> ConfirmationPreflight:
    """Lock and validate the entire batch before formal-document writes begin."""
    ids = _history_ids(history_ids)
    cur.execute(
        "SELECT id, tax_id FROM workspace_clients "
        "WHERE id = %s AND tenant_id = %s::uuid AND is_active = TRUE FOR SHARE",
        (int(workspace_client_id), tenant_id),
    )
    workspace = cur.fetchone()
    if workspace is None:
        raise HTTPException(404, detail="authz.not_found")

    history_lock = " FOR UPDATE" if lock_histories else ""
    cur.execute(
        "SELECT id::text AS id, user_id::text AS user_id, tenant_id::text AS tenant_id, "
        "workspace_client_id, pages, source FROM ocr_history "
        "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid AND user_id = %s::uuid "
        f"ORDER BY id{history_lock}",
        (ids, tenant_id, actor_id),
    )
    rows = {str(row["id"]): row for row in cur.fetchall() or []}
    if len(rows) != len(ids):
        raise HTTPException(404, detail="history.not_found")

    requested_workspace = int(workspace_client_id)
    for history_id in ids:
        row = rows[history_id]
        if str(row.get("tenant_id")) != str(tenant_id) or str(row.get("user_id")) != str(actor_id):
            raise HTTPException(404, detail="history.not_found")
        try:
            actual_workspace = int(row.get("workspace_client_id"))
        except (TypeError, ValueError):
            raise HTTPException(404, detail="history.not_found") from None
        if actual_workspace != requested_workspace:
            raise HTTPException(
                409,
                detail={"code": "erp.workspace_mismatch", "history_ids": ids},
            )

    directions = []
    directions_by_id = {}
    unresolved = {}
    own_tax_id = str(workspace.get("tax_id") or "").strip()
    for history_id in ids:
        direction = convert_svc.resolve_history_direction(rows[history_id], own_tax_id=own_tax_id)
        if direction not in _DIRECTION_PERMISSIONS:
            unresolved[history_id] = "no_direction"
            continue
        directions.append(direction)
        directions_by_id[history_id] = direction
    if unresolved:
        raise HTTPException(
            409,
            detail={"code": "erp.declaration_required", "histories": unresolved},
        )

    unique_directions = tuple(sorted(set(directions)))
    permissions = tuple(
        code for direction in unique_directions for code in _DIRECTION_PERMISSIONS[direction]
    )
    return ConfirmationPreflight(
        directions=unique_directions,
        required_permissions=permissions,
        history_directions=tuple((history_id, directions_by_id[history_id]) for history_id in ids),
    )

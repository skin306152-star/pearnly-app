# -*- coding: utf-8 -*-
"""Pre-write access contract for ERP formal-document confirmation."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException

from core import db
from core import workspace_context as wc
from services.auth.entrance import ERP, require_erp_portal
from services.authz.deps import check_workspace_scope, require_perm
from services.intake_bridge import convert as convert_svc

_DIRECTION_PERMISSIONS = {
    "purchase": ("purchase.doc.create", "purchase.doc.approve"),
    "sales": ("sales.doc.create", "sales.doc.approve"),
}


@dataclass(frozen=True)
class ConfirmationPreflight:
    directions: tuple[str, ...]
    required_permissions: tuple[str, ...]
    history_directions: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ConfirmationGroup:
    workspace_client_id: int
    history_ids: tuple[str, ...]
    preflight: ConfirmationPreflight


@dataclass(frozen=True)
class ConfirmationBatch:
    groups: tuple[ConfirmationGroup, ...]


def require_formal_conversion_entry(user: dict) -> None:
    if user.get("entry") != ERP:
        raise HTTPException(403, detail="authz.entrance_scope")


def is_shared_confirmation_context(user: dict, tenant_id: str) -> bool:
    """Only the ERP entrance creates formal documents, grouped by stored workspace."""
    del tenant_id
    return user.get("entry") == ERP


def guard_confirmation(
    cur,
    request,
    user,
    tenant_id,
    workspace_client_id,
    history_ids,
    *,
    shared_context: bool | None = None,
):
    """Keep the legacy gate outside shared contexts; otherwise preflight the full batch."""
    shared = (
        is_shared_confirmation_context(user, tenant_id)
        if shared_context is None
        else shared_context
    )
    if not shared:
        wc.assert_workspace_in_tenant(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        return None
    require_erp_portal(user)
    return _shared_batch_preflight(cur, request, user, tenant_id, history_ids)


def commit_shared_confirmation(request, user, tenant_id, history_ids) -> int | None:
    """Atomically validate and finish shared formal confirmations."""
    if not is_shared_confirmation_context(user, tenant_id):
        return None
    require_erp_portal(user)
    actor_id = str(user["id"])
    ids = _history_ids(history_ids)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        batch = _shared_batch_preflight(
            cur,
            request,
            user,
            tenant_id,
            ids,
        )
        for group in batch.groups:
            _require_formal_conversion(
                cur,
                preflight=group.preflight,
                tenant_id=tenant_id,
                actor_id=actor_id,
                workspace_client_id=group.workspace_client_id,
                history_ids=list(group.history_ids),
            )
        committed = 0
        for group in batch.groups:
            cur.execute(
                "UPDATE ocr_history SET staged = FALSE, updated_at = NOW() "
                "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
                "AND user_id = %s::uuid AND workspace_client_id = %s AND staged = TRUE",
                (list(group.history_ids), tenant_id, actor_id, group.workspace_client_id),
            )
            committed += int(cur.rowcount or 0)
        return committed


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


def _shared_batch_preflight(
    cur,
    request,
    user,
    tenant_id,
    history_ids,
    *,
    lock_histories: bool = True,
) -> ConfirmationBatch:
    actor_id = str(user["id"])
    groups = _snapshot_history_groups(
        cur,
        tenant_id=tenant_id,
        actor_id=actor_id,
        history_ids=history_ids,
        lock_histories=False,
    )
    checked = []
    for workspace_client_id, group_ids in groups:
        preflight = _shared_preflight(
            cur,
            request,
            user,
            tenant_id,
            workspace_client_id,
            list(group_ids),
            lock_histories=lock_histories,
        )
        checked.append(
            ConfirmationGroup(
                workspace_client_id=workspace_client_id,
                history_ids=group_ids,
                preflight=preflight,
            )
        )
    return ConfirmationBatch(groups=tuple(checked))


def confirmation_status(cur, request, user, tenant_id, workspace_client_id, history_ids) -> dict:
    """Read the canonical formal-document state without replaying confirmation writes."""
    require_erp_portal(user)
    ids = _history_ids(history_ids)
    if is_shared_confirmation_context(user, tenant_id):
        batch = _shared_batch_preflight(
            cur,
            request,
            user,
            tenant_id,
            ids,
            lock_histories=False,
        )
    else:
        preflight = _shared_preflight(
            cur,
            request,
            user,
            tenant_id,
            workspace_client_id,
            ids,
            lock_histories=False,
        )
        batch = ConfirmationBatch(
            groups=(
                ConfirmationGroup(
                    workspace_client_id=int(workspace_client_id),
                    history_ids=tuple(ids),
                    preflight=preflight,
                ),
            )
        )
    resolved_set = set()
    for group in batch.groups:
        converted = _formal_history_ids_by_direction(
            cur,
            tenant_id=tenant_id,
            actor_id=str(user["id"]),
            workspace_client_id=group.workspace_client_id,
            history_ids=list(group.history_ids),
        )
        directions = dict(group.preflight.history_directions)
        resolved_set.update(
            history_id
            for history_id in group.history_ids
            if history_id in converted[directions[history_id]]
        )
    resolved = [history_id for history_id in ids if history_id in resolved_set]
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
    if isinstance(preflight, ConfirmationBatch):
        requested = {str(history_id) for history_id in history_ids}
        known = {history_id for group in preflight.groups for history_id in group.history_ids}
        if not requested.issubset(known):
            raise HTTPException(404, detail="history.not_found")
        pending = []
        for group in preflight.groups:
            group_ids = [history_id for history_id in group.history_ids if history_id in requested]
            if group_ids:
                pending.append((group, group_ids))
        for group, group_ids in pending:
            _require_formal_conversion(
                cur,
                preflight=group.preflight,
                tenant_id=tenant_id,
                actor_id=actor_id,
                workspace_client_id=group.workspace_client_id,
                history_ids=group_ids,
            )
        for group, group_ids in pending:
            cur.execute(
                "UPDATE ocr_history SET staged = FALSE, updated_at = NOW() "
                "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
                "AND user_id = %s::uuid AND workspace_client_id = %s",
                (group_ids, tenant_id, actor_id, group.workspace_client_id),
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


def _snapshot_history_groups(
    cur,
    *,
    tenant_id: str,
    actor_id: str,
    history_ids: list[str],
    lock_histories: bool = False,
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    """Read actor-owned histories and group them by their persisted workspace."""
    ids = _history_ids(history_ids)
    history_lock = " FOR UPDATE" if lock_histories else ""
    cur.execute(
        "SELECT id::text AS id, workspace_client_id FROM ocr_history "
        "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid AND user_id = %s::uuid "
        f"ORDER BY id{history_lock}",
        (ids, tenant_id, actor_id),
    )
    rows = cur.fetchall() or []
    by_id = {str(row["id"]): row for row in rows}
    if len(by_id) != len(ids):
        raise HTTPException(404, detail="history.not_found")
    grouped: dict[int, list[str]] = {}
    for history_id in ids:
        try:
            workspace_id = int(by_id[history_id].get("workspace_client_id"))
        except (TypeError, ValueError):
            raise HTTPException(404, detail="history.not_found") from None
        grouped.setdefault(workspace_id, []).append(history_id)
    return tuple((workspace_id, tuple(grouped[workspace_id])) for workspace_id in sorted(grouped))


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

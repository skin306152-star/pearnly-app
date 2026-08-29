# -*- coding: utf-8 -*-
"""Atomic access gates for history payload changes in shared ERP confirmation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from core import db
from services.auth.entrance import require_erp_portal
from services.authz.deps import check_workspace_scope
from services.intake_bridge import erp_confirmation_access as confirmation_access
from services.ocr_history import mutations as history_mutations
from services.purchase.field_clean import clean_tax_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SharedPostingUpdate:
    ok: bool
    workspace_client_id: int | None = None
    seller_tax: str = ""


def update_history_pages(request, user, tenant_id, history_id, pages) -> bool | None:
    """Update a shared-confirmation payload under the same row lock as the formal check."""
    actor_id = _shared_actor(user, tenant_id)
    if actor_id is None:
        return None
    summary = history_mutations._extract_summary_fields(pages)
    archive_name, category_tag = _archive_values(actor_id, pages)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        record_id, workspace_client_id, _row = _lock_mutable_history(
            cur, request, user, tenant_id, actor_id, history_id
        )
        cur.execute(
            "UPDATE ocr_history SET pages = %s::jsonb, invoice_no = %s, invoice_date = %s, "
            "seller_name = %s, total_amount = %s, archive_name = COALESCE(%s, archive_name), "
            "category_tag = COALESCE(%s, category_tag), "
            "archived_at = CASE WHEN %s IS NOT NULL THEN NOW() ELSE archived_at END, "
            "fields_edited_at = NOW(), edit_count = edit_count + 1, updated_at = NOW() "
            "WHERE id = %s::uuid AND tenant_id = %s::uuid AND user_id = %s::uuid "
            "AND workspace_client_id = %s",
            (
                json.dumps(pages, ensure_ascii=False),
                summary["invoice_no"],
                summary["invoice_date"],
                summary["seller_name"],
                summary["total_amount"],
                archive_name,
                category_tag,
                archive_name,
                record_id,
                tenant_id,
                actor_id,
                workspace_client_id,
            ),
        )
        updated = cur.rowcount > 0
    if updated:
        _record_edit_feedback(actor_id, tenant_id, record_id, pages)
    return updated


def update_history_posting(
    request, user, tenant_id, history_id, changes: dict[str, Any]
) -> SharedPostingUpdate | None:
    """Apply manual posting verdicts only while the actor-owned history is still mutable."""
    actor_id = _shared_actor(user, tenant_id)
    if actor_id is None:
        return None
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        record_id, workspace_client_id, row = _lock_mutable_history(
            cur, request, user, tenant_id, actor_id, history_id
        )
        pages = list(row.get("pages") or [])
        if not pages:
            return SharedPostingUpdate(False)
        index = _primary_page_index(pages)
        page = dict(pages[index]) if isinstance(pages[index], dict) else {}
        fields = dict(page.get("fields") or {})
        _apply_posting_changes(fields, changes)
        seller_tax = clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id"))
        page["fields"] = fields
        pages[index] = page
        cur.execute(
            "UPDATE ocr_history SET pages = %s::jsonb, updated_at = NOW() "
            "WHERE id = %s::uuid AND tenant_id = %s::uuid AND user_id = %s::uuid "
            "AND workspace_client_id = %s",
            (
                json.dumps(pages, ensure_ascii=False),
                record_id,
                tenant_id,
                actor_id,
                workspace_client_id,
            ),
        )
        return SharedPostingUpdate(cur.rowcount > 0, workspace_client_id, seller_tax)


def assign_workspace(
    request, user, tenant_id, history_id, target_workspace_client_id
) -> bool | None:
    """Move an actor-owned unconverted history to another active assigned workspace."""
    actor_id = _shared_actor(user, tenant_id)
    if actor_id is None:
        return None
    target = int(target_workspace_client_id)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        record_id, current_workspace, _row = _lock_mutable_history(
            cur,
            request,
            user,
            tenant_id,
            actor_id,
            history_id,
            additional_workspace_ids=(target,),
        )
        cur.execute(
            "UPDATE ocr_history SET workspace_client_id = %s, updated_at = NOW() "
            "WHERE id = %s::uuid AND tenant_id = %s::uuid AND user_id = %s::uuid "
            "AND workspace_client_id = %s",
            (target, record_id, tenant_id, actor_id, current_workspace),
        )
        return cur.rowcount > 0


def assign_client(request, user, tenant_id, history_id, client_id) -> bool | None:
    """Change counterparty assignment without allowing cross-actor history mutation."""
    actor_id = _shared_actor(user, tenant_id)
    if actor_id is None:
        return None
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        record_id, workspace_client_id, _row = _lock_mutable_history(
            cur, request, user, tenant_id, actor_id, history_id
        )
        if client_id is not None:
            cur.execute(
                "SELECT id FROM clients WHERE id = %s "
                "AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid) FOR SHARE",
                (int(client_id), tenant_id),
            )
            if cur.fetchone() is None:
                return False
        cur.execute(
            "UPDATE ocr_history SET client_id = %s "
            "WHERE id = %s::uuid AND tenant_id = %s::uuid AND user_id = %s::uuid "
            "AND workspace_client_id = %s",
            (client_id, record_id, tenant_id, actor_id, workspace_client_id),
        )
        return cur.rowcount > 0


def delete_histories(request, user, tenant_id, history_ids) -> tuple[int, list[str]] | None:
    """Delete a complete actor-owned batch only when no source has a formal document."""
    actor_id = _shared_actor(user, tenant_id)
    if actor_id is None:
        return None
    ids = confirmation_access._history_ids(history_ids)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        _lock_mutable_histories(cur, request, user, tenant_id, actor_id, ids)
        cur.execute(
            "DELETE FROM ocr_history WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
            "AND user_id = %s::uuid RETURNING pdf_storage_path",
            (ids, tenant_id, actor_id),
        )
        deleted_rows = cur.fetchall() or []
        paths = [row["pdf_storage_path"] for row in deleted_rows if row.get("pdf_storage_path")]
        return len(deleted_rows), paths


def _shared_actor(user: dict, tenant_id: str) -> str | None:
    if not confirmation_access.is_shared_confirmation_context(user, tenant_id):
        return None
    require_erp_portal(user)
    return str(user["id"])


def _lock_mutable_history(
    cur, request, user, tenant_id, actor_id, history_id, *, additional_workspace_ids=()
):
    record_id = confirmation_access._history_ids([history_id])[0]
    rows = _lock_mutable_histories(
        cur,
        request,
        user,
        tenant_id,
        actor_id,
        [record_id],
        additional_workspace_ids=additional_workspace_ids,
    )
    row = rows[record_id]
    return record_id, int(row["workspace_client_id"]), row


def _lock_mutable_histories(
    cur, request, user, tenant_id, actor_id, history_ids, *, additional_workspace_ids=()
):
    cur.execute(
        "SELECT id::text AS id, workspace_client_id FROM ocr_history "
        "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid AND user_id = %s::uuid "
        "ORDER BY id",
        (history_ids, tenant_id, actor_id),
    )
    snapshot = {str(row["id"]): row for row in cur.fetchall() or []}
    if len(snapshot) != len(history_ids):
        raise HTTPException(404, detail="history.not_found")
    try:
        source_workspaces = {int(row["workspace_client_id"]) for row in snapshot.values()}
        workspaces = source_workspaces | {int(value) for value in additional_workspace_ids}
    except (TypeError, ValueError):
        raise HTTPException(404, detail="history.not_found") from None
    ordered_workspaces = sorted(workspaces)
    cur.execute(
        "SELECT id FROM workspace_clients WHERE id = ANY(%s::bigint[]) "
        "AND tenant_id = %s::uuid AND is_active = TRUE ORDER BY id FOR SHARE",
        (ordered_workspaces, tenant_id),
    )
    active_workspaces = {int(row["id"]) for row in cur.fetchall() or []}
    if active_workspaces != workspaces:
        raise HTTPException(404, detail="authz.not_found")
    for workspace_client_id in ordered_workspaces:
        check_workspace_scope(request, user, workspace_client_id)
    cur.execute(
        "SELECT id::text AS id, workspace_client_id, pages FROM ocr_history "
        "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid AND user_id = %s::uuid "
        "ORDER BY id FOR UPDATE",
        (history_ids, tenant_id, actor_id),
    )
    rows = {str(row["id"]): row for row in cur.fetchall() or []}
    if len(rows) != len(history_ids):
        raise HTTPException(404, detail="history.not_found")
    for history_id in history_ids:
        try:
            actual_workspace = int(rows[history_id].get("workspace_client_id"))
            expected_workspace = int(snapshot[history_id].get("workspace_client_id"))
        except (TypeError, ValueError):
            raise HTTPException(404, detail="history.not_found") from None
        if actual_workspace != expected_workspace:
            raise HTTPException(404, detail="history.not_found")
    _raise_if_formal(cur, tenant_id, history_ids)
    return rows


def _raise_if_formal(cur, tenant_id, history_ids) -> None:
    queries = (
        "SELECT ocr_history_id::text AS history_id FROM purchase_docs "
        "WHERE tenant_id = %s::uuid AND ocr_history_id = ANY(%s::uuid[]) FOR SHARE",
        "SELECT ocr_history_id::text AS history_id FROM sales_documents "
        "WHERE tenant_id = %s::uuid AND ocr_history_id = ANY(%s::uuid[]) FOR SHARE",
    )
    locked = set()
    for sql in queries:
        cur.execute(sql, (tenant_id, history_ids))
        locked.update(str(row["history_id"]) for row in cur.fetchall() or [])
    if locked:
        raise HTTPException(
            409,
            detail={"code": "erp.formal_document_locked", "history_ids": sorted(locked)},
        )


def _archive_values(user_id: str, pages: list) -> tuple[str | None, str | None]:
    try:
        from services.archive import archive

        fields = next(
            (
                page.get("fields") or {}
                for page in pages or []
                if not page.get("is_duplicate") and not page.get("is_copy")
            ),
            {},
        )
        template = db.get_archive_template(user_id) or archive.DEFAULT_TEMPLATE
        return (
            archive.preview_name(fields, template),
            (fields.get("category") or "").strip() or None,
        )
    except Exception as exc:
        logger.warning("Failed to recompute archive name: %s", exc)
        return None, None


def _record_edit_feedback(user_id: str, tenant_id: str, history_id: str, pages: list) -> None:
    try:
        from services.ocr.feedback import store

        store.record_correction_from_edit(user_id, tenant_id, history_id, pages)
    except Exception as exc:
        logger.warning("Skipped OCR edit feedback for %s: %s", history_id, exc)


def _primary_page_index(pages: list) -> int:
    for index, page in enumerate(pages):
        if isinstance(page, dict) and not page.get("is_duplicate") and not page.get("is_copy"):
            return index
    return 0


def _apply_posting_changes(fields: dict, changes: dict[str, Any]) -> None:
    keys = {"payment": "posting_payment_manual", "item_type": "posting_item_type_manual"}
    for source, target in keys.items():
        if source not in changes:
            continue
        value = changes[source]
        if value is None:
            fields.pop(target, None)
        else:
            fields[target] = value

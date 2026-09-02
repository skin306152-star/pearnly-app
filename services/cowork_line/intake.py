"""Scoped Cowork LINE draft review, commit, and discard operations."""

from __future__ import annotations

from core import db
from services.cowork_line import intake_targets, session_store
from services.cowork_line.review_fields import (
    pages_with_direction as _pages_with_direction,
    selection_from_payload as _selection,
)
from services.erp import selected_account_refresh
from services.ocr_history.mutations import update_ocr_history_pages
from services.ocr_history.queries import get_history_pdf_info, get_ocr_history_detail
from services.ocr_history.staged import discard_staged_ocr_history_with_pdf_paths

CoworkLineIntakeError = intake_targets.CoworkLineIntakeError
get_target = intake_targets.get_target


def _ids(payload: dict) -> list[str]:
    return [str(value) for value in payload.get("history_ids") or [] if value]


def require_draft(identity: dict, draft_id: str) -> tuple[dict, dict]:
    session = session_store.get_session(
        tenant_id=str(identity["tenant_id"]), line_user_id=str(identity["line_user_id"])
    )
    payload = dict((session or {}).get("payload") or {})
    history_ids = _ids(payload)
    if (
        not session
        or session.get("state") not in {"draft", "editing", "review"}
        or not payload.get("nonce")
        or str(draft_id) not in history_ids
    ):
        raise CoworkLineIntakeError("draft_expired")
    return session, payload


def _assert_owned_staged(identity: dict, history_ids: list[str]) -> None:
    if not history_ids:
        raise CoworkLineIntakeError("draft_empty")
    with db.get_cursor_rls(
        tenant_id=str(identity["tenant_id"]), user_id=str(identity["user_id"])
    ) as cur:
        cur.execute(
            "SELECT id FROM ocr_history WHERE id = ANY(%s::uuid[]) "
            "AND tenant_id = %s::uuid AND user_id = %s::uuid AND staged = TRUE",
            (history_ids, str(identity["tenant_id"]), str(identity["user_id"])),
        )
        found = {str(row["id"]) for row in cur.fetchall() or []}
    if found != set(history_ids):
        raise CoworkLineIntakeError("draft_forbidden", 403)


def _preview_urls(draft_id: str, history_id: str, pages: list) -> list[str]:
    numbers: list[int] = []
    for index, page in enumerate(pages or []):
        raw = page.get("page_number") if isinstance(page, dict) else None
        try:
            page_number = max(0, int(raw or index + 1) - 1)
        except (TypeError, ValueError):
            page_number = index
        if page_number not in numbers:
            numbers.append(page_number)
    return [
        f"/api/cowork-line/intake/draft/{draft_id}/records/{history_id}/page/{number}.png"
        for number in (numbers or [0])
    ]


def _records(identity: dict, draft_id: str, history_ids: list[str]) -> list[dict]:
    records = []
    for history_id in history_ids:
        detail = get_ocr_history_detail(
            str(identity["user_id"]), history_id, tenant_id=str(identity["tenant_id"])
        )
        if detail is None:
            raise CoworkLineIntakeError("draft_forbidden", 403)
        urls = _preview_urls(draft_id, history_id, detail.get("pages") or [])
        detail["preview_urls"] = urls
        detail["preview_url"] = urls[0]
        records.append(detail)
    return records


def get_draft(identity: dict, draft_id: str) -> dict:
    _, payload = require_draft(identity, draft_id)
    history_ids = _ids(payload)
    _assert_owned_staged(identity, history_ids)
    return {
        "draft_id": str(draft_id),
        "records": _records(identity, str(draft_id), history_ids),
        "targets": intake_targets.list_targets(
            identity,
            refresh=False,
            include_account_catalog=False,
        ),
        "selection": _selection(payload),
    }


def _update_scope(identity: dict, history_ids: list[str], selection: dict) -> None:
    with db.get_cursor_rls(
        tenant_id=str(identity["tenant_id"]), user_id=str(identity["user_id"]), commit=True
    ) as cur:
        cur.execute(
            "UPDATE ocr_history SET workspace_client_id = %s, posting_kind = %s, updated_at = NOW() "
            "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
            "AND user_id = %s::uuid AND staged = TRUE",
            (
                selection["workspace_client_id"],
                selection.get("posting_kind"),
                history_ids,
                str(identity["tenant_id"]),
                str(identity["user_id"]),
            ),
        )
        if cur.rowcount != len(set(history_ids)):
            raise CoworkLineIntakeError("draft_save_failed")


def save_draft(identity: dict, draft_id: str, records: list[dict], selection: dict) -> dict:
    _, payload = require_draft(identity, draft_id)
    selection = dict(selection)
    if selection.get("connection_workspace_client_id") is None:
        selection["connection_workspace_client_id"] = (
            payload.get("connection_workspace_client_id")
            if "connection_workspace_client_id" in payload
            else selection.get("workspace_client_id")
        )
    history_ids = _ids(payload)
    submitted_ids = [str(row.get("id") or row.get("history_id") or "") for row in records]
    if submitted_ids != history_ids:
        raise CoworkLineIntakeError("records_incomplete")
    _assert_owned_staged(identity, history_ids)
    target, normalized = intake_targets.validated_selection(identity, selection)
    for record in records:
        history_id = str(record.get("id") or record.get("history_id") or "")
        pages = record.get("pages")
        if not isinstance(pages, list) or not pages:
            raise CoworkLineIntakeError("pages_required", 422)
        pages = _pages_with_direction(pages, normalized["direction"])
        if not update_ocr_history_pages(
            str(identity["user_id"]),
            history_id,
            pages,
            tenant_id=str(identity["tenant_id"]),
        ):
            raise CoworkLineIntakeError("draft_save_failed")
    target = intake_targets.resolve_history_workspace(
        identity,
        target,
        history_ids,
        normalized["direction"],
        provisional_history_assignment=True,
    )
    normalized = intake_targets.normalize_selection(target, normalized)
    if normalized["workspace_client_id"] is None:
        raise CoworkLineIntakeError("workspace_required", 409)
    _update_scope(identity, history_ids, normalized)
    if normalized.get("payment"):
        from services.ocr_history.posting_manual import update_history_posting_manual

        for history_id in history_ids:
            result = update_history_posting_manual(
                str(identity["user_id"]),
                history_id,
                str(identity["tenant_id"]),
                payment=normalized["payment"],
            )
            if not result.ok:
                raise CoworkLineIntakeError("draft_save_failed")
    target = intake_targets.preflight_target(identity, target, history_ids, normalized)
    try:
        master_refresh = selected_account_refresh.ensure_for_editor(
            identity,
            target,
            normalized["account_set"],
            previous_request_id=payload.get("master_refresh_request_id"),
        )
    except Exception as exc:
        raise CoworkLineIntakeError("master_refresh_failed") from exc
    next_payload = {
        **payload,
        **normalized,
        "history_ids": history_ids,
        "posting_mode": normalized.get("posting_kind") or normalized.get("payment"),
    }
    for key in (
        "master_refresh_request_id",
        "master_refresh_status",
        "master_refresh_account_set",
    ):
        next_payload.pop(key, None)
    if master_refresh:
        next_payload.update(
            {
                "master_refresh_request_id": master_refresh["request_id"],
                "master_refresh_status": master_refresh["status"],
                "master_refresh_account_set": master_refresh["account_set_key"],
            }
        )
    session_store.set_session(
        tenant_id=str(identity["tenant_id"]),
        line_user_id=str(identity["line_user_id"]),
        state="editing",
        payload=next_payload,
    )
    return {
        "draft_id": str(draft_id),
        "records": _records(identity, str(draft_id), history_ids),
        "targets": intake_targets.replace_target(intake_targets.list_targets(identity), target),
        "selection": _selection(next_payload),
        "master_refresh": master_refresh,
    }


async def _dispatch_confirmed(
    identity: dict, history_ids: list[str], target: dict, selection: dict
) -> dict:
    from services.cowork_line.push import dispatch_confirmed

    return await dispatch_confirmed(identity, history_ids, target, selection)


async def confirm_and_push(identity: dict, draft: str | dict) -> dict:
    supplied = draft if isinstance(draft, dict) else None
    supplied_ids = _ids(supplied or {})
    draft_id = supplied_ids[0] if supplied_ids else str(draft)
    _, payload = require_draft(identity, draft_id)
    history_ids = _ids(payload)
    if supplied is not None and supplied_ids != history_ids:
        raise CoworkLineIntakeError("records_incomplete")
    target, normalized = intake_targets.validated_selection(
        identity,
        _selection(payload),
        refresh_probe=True,
    )
    try:
        master_refresh = selected_account_refresh.ensure_for_editor(
            identity,
            target,
            normalized["account_set"],
            previous_request_id=payload.get("master_refresh_request_id"),
        )
    except Exception as exc:
        raise CoworkLineIntakeError("master_refresh_failed") from exc
    refresh_status = str((master_refresh or {}).get("status") or "")
    if master_refresh and refresh_status != "succeeded":
        code = "master_refresh_failed" if refresh_status == "failed" else "master_refresh_pending"
        raise CoworkLineIntakeError(code)
    from services.line_platform.draft_validation import batch_issues

    records = _records(identity, draft_id, history_ids)
    if batch_issues(records, normalized["direction"], require_posting_kind=False):
        raise CoworkLineIntakeError("document_not_ready", 422)
    target = intake_targets.preflight_target(identity, target, history_ids, normalized)
    if not target["selectable"]:
        raise CoworkLineIntakeError(str(target.get("block_reason") or "document_not_ready"))
    result = await _dispatch_confirmed(identity, history_ids, target, normalized)
    committed = int(result.get("committed") or 0)
    if committed == len(set(history_ids)):
        session_store.clear_session(
            tenant_id=str(identity["tenant_id"]), line_user_id=str(identity["line_user_id"])
        )
    if "push_ok" not in result:
        result["push_ok"] = str(result.get("status") or "") in {
            "success",
            "pending",
            "queued",
            "retrying",
            "skipped_dup",
        }
    return {"saved": committed == len(set(history_ids)), **result, "committed": committed}


def cleanup_staged(identity: dict, history_ids: list[str]) -> dict:
    history_ids = [str(value) for value in history_ids if value]
    _assert_owned_staged(identity, history_ids)
    deleted, paths = discard_staged_ocr_history_with_pdf_paths(
        str(identity["user_id"]), history_ids, tenant_id=str(identity["tenant_id"])
    )
    if deleted != len(set(history_ids)):
        raise CoworkLineIntakeError("discard_incomplete")
    from services.ocr import pdf_storage

    for path in set(paths or []):
        with db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (path,))
            still_used = cur.fetchone() is not None
        if not still_used:
            pdf_storage.delete_pdf(path)
    return {"discarded": deleted, "history_ids": history_ids}


def discard_draft(identity: dict, draft_id: str) -> dict:
    _, payload = require_draft(identity, draft_id)
    result = cleanup_staged(identity, _ids(payload))
    session_store.clear_session(
        tenant_id=str(identity["tenant_id"]), line_user_id=str(identity["line_user_id"])
    )
    return result


def pdf_info(identity: dict, draft_id: str, history_id: str) -> dict:
    _, payload = require_draft(identity, draft_id)
    if str(history_id) not in _ids(payload):
        raise CoworkLineIntakeError("draft_forbidden", 403)
    info = get_history_pdf_info(
        str(identity["user_id"]), str(history_id), tenant_id=str(identity["tenant_id"])
    )
    if not info:
        raise CoworkLineIntakeError("pdf_not_found", 404)
    return info


def draft_records(
    identity: dict, draft_id: str, history_ids: list[str] | None = None
) -> list[dict]:
    _, payload = require_draft(identity, draft_id)
    expected = _ids(payload)
    supplied = [str(value) for value in (history_ids or expected)]
    if supplied != expected:
        raise CoworkLineIntakeError("records_incomplete")
    _assert_owned_staged(identity, expected)
    return _records(identity, draft_id, expected)


def apply_posting_mode(identity: dict, history_ids: list[str], *, payment: str) -> None:
    ids = [str(value) for value in history_ids if value]
    _assert_owned_staged(identity, ids)
    from services.ocr_history.posting_manual import update_history_posting_manual

    for history_id in ids:
        result = update_history_posting_manual(
            str(identity["user_id"]),
            history_id,
            str(identity["tenant_id"]),
            payment=payment,
        )
        if not result.ok:
            raise CoworkLineIntakeError("draft_save_failed")


def discard(identity: dict, history_ids: list[str]) -> dict:
    ids = [str(value) for value in history_ids if value]
    if not ids:
        raise CoworkLineIntakeError("draft_empty")
    result = discard_draft(identity, ids[0])
    return {"ok": True, **result}


def generate_and_save_pdf(
    content: bytes,
    pages: list,
    history_ids: list[str],
    user_id: str,
    tenant_id: str | None = None,
) -> dict:
    from services.line_erp.intake import generate_and_save_pdf as save_pdf

    return save_pdf(content, pages, history_ids, user_id, tenant_id)

"""Scoped Cowork LINE draft review, commit, and discard operations."""

from __future__ import annotations

from typing import Any

from core import db
from services.cowork_line import session_store
from services.ocr_history.mutations import update_ocr_history_pages
from services.ocr_history.queries import get_history_pdf_info, get_ocr_history_detail
from services.ocr_history.staged import discard_staged_ocr_history_with_pdf_paths


class CoworkLineIntakeError(Exception):
    def __init__(self, code: str, status_code: int = 409):
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def _targets_service():
    from services.cowork_line import erp_targets

    return erp_targets


def _target_error(exc: Exception) -> CoworkLineIntakeError:
    code = str(getattr(exc, "code", "target_not_ready"))
    status = (
        403 if code in {"forbidden", "identity_inactive", "workspace_manage_forbidden"} else 409
    )
    return CoworkLineIntakeError(code, status)


def _list_targets(identity: dict, *, refresh: bool = False) -> list[dict]:
    try:
        return _targets_service().list_targets(identity, refresh=refresh)
    except Exception as exc:
        if exc.__class__.__name__ != "CoworkLineErpTargetError":
            raise
        raise _target_error(exc) from exc


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


def _selection(payload: dict) -> dict[str, Any]:
    adapter = str(payload.get("adapter") or "").lower()
    posting_mode = payload.get("posting_mode")
    return {
        "endpoint_id": payload.get("endpoint_id"),
        "workspace_client_id": payload.get("workspace_client_id"),
        "adapter": payload.get("adapter"),
        "target_label": payload.get("target_label"),
        "account_root": payload.get("account_root"),
        "account_set": payload.get("account_set"),
        "direction": payload.get("direction"),
        "posting_kind": payload.get("posting_kind")
        or (posting_mode if adapter == "express" else None),
        "payment": payload.get("payment") or (posting_mode if adapter == "mrerp" else None),
    }


def get_draft(identity: dict, draft_id: str) -> dict:
    _, payload = require_draft(identity, draft_id)
    history_ids = _ids(payload)
    _assert_owned_staged(identity, history_ids)
    return {
        "draft_id": str(draft_id),
        "records": _records(identity, str(draft_id), history_ids),
        "targets": _list_targets(identity, refresh=True),
        "selection": _selection(payload),
    }


def _normalize_selection(target: dict, selection: dict) -> dict:
    adapter = str(target.get("adapter") or "").lower()
    direction = str(selection.get("direction") or "").lower()
    if direction not in {"purchase", "sales"}:
        raise CoworkLineIntakeError("direction_required", 422)
    mode_key = "posting_kind" if adapter == "express" else "payment"
    mode = str(selection.get(mode_key) or "").lower()
    allowed = {str(value).lower() for value in target.get("mode_options") or []}
    if not mode or (allowed and mode not in allowed):
        raise CoworkLineIntakeError("mode_required", 422)
    account_key = str(
        selection.get("account_set") or target.get("selected_account_key") or ""
    ).strip()
    account = next(
        (
            row
            for row in target.get("account_choices") or []
            if isinstance(row, dict) and str(row.get("key") or "").strip() == account_key
        ),
        None,
    )
    if not account or account.get("writable") is False:
        raise CoworkLineIntakeError("account_set_required", 422)
    workspace_client_id = target.get("workspace_client_id")
    return {
        "endpoint_id": str(target["endpoint_id"]),
        "workspace_client_id": (
            int(workspace_client_id) if workspace_client_id is not None else None
        ),
        "adapter": adapter,
        "target_label": target.get("label") or "",
        "account_root": str(account.get("root_key") or "").strip() or None,
        "account_set": account_key,
        "account_config": {
            key: account.get(key)
            for key in (
                "comidyear",
                "seldb",
                "account_set",
                "account_dir",
                "account_company",
                "account_set_row",
                "root_key",
                "mapping",
            )
            if account.get(key) not in (None, "")
        },
        "direction": direction,
        "posting_kind": mode if adapter == "express" else None,
        "payment": mode if adapter != "express" else None,
    }


def _validated_selection(
    identity: dict,
    selection: dict,
    *,
    refresh_probe: bool = False,
) -> tuple[dict, dict]:
    endpoint_id = str(selection.get("endpoint_id") or "").strip()
    workspace_client_id = selection.get("workspace_client_id")
    if not endpoint_id:
        raise CoworkLineIntakeError("target_required", 422)
    try:
        target_kwargs = {"workspace_client_id": workspace_client_id}
        if refresh_probe:
            target_kwargs["refresh_probe"] = True
        target = _targets_service().require_target(identity, endpoint_id, **target_kwargs)
    except Exception as exc:
        if exc.__class__.__name__ != "CoworkLineErpTargetError":
            raise
        raise _target_error(exc) from exc
    return target, _normalize_selection(target, selection)


def _pages_with_direction(pages: list, direction: str) -> list:
    updated = []
    for page in pages:
        current = dict(page) if isinstance(page, dict) else {}
        fields = dict(current.get("fields") or {})
        fields["direction"] = direction
        current["fields"] = fields
        updated.append(current)
    return updated


def _preflight_target(
    identity: dict, target: dict, history_ids: list[str], selection: dict
) -> dict:
    missing = list(target.get("missing") or [])
    for history_id in history_ids:
        result = _targets_service().preflight_document(
            identity,
            target,
            history_id,
            selection["direction"],
            posting_kind=selection.get("posting_kind"),
            payment=selection.get("payment"),
            account_config=selection.get("account_config"),
        )
        for code in result.get("missing") or []:
            if code not in missing:
                missing.append(code)
    projected = dict(target)
    checks = dict(projected.get("ready_checks") or {})
    checks["document_preflight"] = not missing
    projected.update(
        {
            "ready_checks": checks,
            "missing": missing,
            "block_reason": missing[0] if missing else None,
            "selectable": bool(projected.get("selectable", True)) and not missing,
        }
    )
    return projected


def _replace_target(targets: list[dict], selected: dict) -> list[dict]:
    return [
        (
            selected
            if (
                str(target.get("endpoint_id")) == str(selected.get("endpoint_id"))
                and target.get("workspace_client_id") == selected.get("workspace_client_id")
            )
            else target
        )
        for target in targets
    ]


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
    history_ids = _ids(payload)
    submitted_ids = [str(row.get("id") or row.get("history_id") or "") for row in records]
    if submitted_ids != history_ids:
        raise CoworkLineIntakeError("records_incomplete")
    _assert_owned_staged(identity, history_ids)
    target, normalized = _validated_selection(identity, selection)
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
    try:
        target = _targets_service().resolve_history_workspace(
            identity,
            target,
            history_ids,
            normalized["direction"],
            provisional_history_assignment=True,
        )
    except Exception as exc:
        if exc.__class__.__name__ != "CoworkLineErpTargetError":
            raise
        raise _target_error(exc) from exc
    normalized = _normalize_selection(target, normalized)
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
    target = _preflight_target(identity, target, history_ids, normalized)
    next_payload = {
        **payload,
        **normalized,
        "history_ids": history_ids,
        "posting_mode": normalized.get("posting_kind") or normalized.get("payment"),
    }
    session_store.set_session(
        tenant_id=str(identity["tenant_id"]),
        line_user_id=str(identity["line_user_id"]),
        state="editing",
        payload=next_payload,
    )
    return {
        "draft_id": str(draft_id),
        "records": _records(identity, str(draft_id), history_ids),
        "targets": _replace_target(_list_targets(identity), target),
        "selection": _selection(next_payload),
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
    target, normalized = _validated_selection(
        identity,
        _selection(payload),
        refresh_probe=True,
    )
    from services.line_platform.draft_validation import batch_issues

    records = _records(identity, draft_id, history_ids)
    if batch_issues(records, normalized["direction"], require_posting_kind=False):
        raise CoworkLineIntakeError("document_not_ready", 422)
    target = _preflight_target(identity, target, history_ids, normalized)
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

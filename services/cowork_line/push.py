"""Dispatch Cowork recognition records through transactionally reserved ERP intents."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from core import db
from services.cowork_line.push_recovery import mark_legacy_intent_unknown
from services.cowork_line.push_reservation import (
    confirmed_batch_result,
    finalize_legacy_intent,
    reserve_legacy_batch,
    reserve_managed_batch,
)
from services.erp import erp_push


class CoworkLinePushError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _error_code(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if code:
        return str(code)
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            return str(detail.get("code") or detail.get("reason") or "target_not_ready")
        if isinstance(detail, str):
            return detail
    return type(exc).__name__


def _push_legacy_intent(
    identity: dict[str, Any],
    endpoint: dict[str, Any],
    intent: dict[str, Any],
    *,
    posting_kind: str | None,
) -> dict[str, Any]:
    if not intent.get("dispatch"):
        return {key: value for key, value in intent.items() if key not in {"history", "dispatch"}}
    try:
        result = erp_push.push_to_endpoint(
            endpoint,
            intent["history"],
            posting_kind=posting_kind,
        )
    except Exception as exc:
        result = {
            "success": False,
            "http_status": None,
            "request_body": None,
            "response_body": None,
            "error_msg": type(exc).__name__,
            "elapsed_ms": 0,
        }
    if not finalize_legacy_intent(identity, endpoint, intent, result):
        mark_legacy_intent_unknown(identity, endpoint, intent)
        return {
            "history_id": intent["history_id"],
            "log_id": intent["log_id"],
            "status": "manual",
            "accepted": False,
            "error_msg": "push_result_unknown",
        }
    return {key: value for key, value in intent.items() if key not in {"history", "dispatch"}}


def _failure_log(
    identity: dict[str, Any],
    target: dict[str, Any],
    history_id: str,
    code: str,
) -> dict[str, Any]:
    adapter = str(target.get("adapter") or "").lower()
    user_id = str(identity["user_id"])
    tenant_id = str(identity["tenant_id"])
    endpoint_id = str(target.get("endpoint_id") or "")
    history = db.get_ocr_history_detail(user_id, history_id, tenant_id=tenant_id) or {}
    request_body = {
        "adapter": adapter,
        "source": "cowork_line",
        "preflight_failure": code[:200],
    }
    if adapter == "express" and target.get("managed"):
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_push_logs "
                "(user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,status,"
                "http_status,request_body,error_msg,attempt,elapsed_ms,trigger,tenant_id,"
                "workspace_client_id) VALUES (%s,%s,%s,%s,%s,%s,'manual',409,%s::jsonb,%s,"
                "1,0,'manual',%s,%s) RETURNING id::text AS id",
                (
                    user_id,
                    endpoint_id,
                    history_id,
                    history.get("invoice_no"),
                    history.get("seller_name"),
                    history.get("total_amount"),
                    json.dumps(request_body, ensure_ascii=False),
                    code[:500],
                    tenant_id,
                    int(target["workspace_client_id"]),
                ),
            )
            row = cur.fetchone()
            log_id = str(row["id"]) if row else None
    else:
        log_id = db.insert_push_log(
            user_id=user_id,
            endpoint_id=endpoint_id,
            history_id=history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status="failed",
            http_status=409,
            request_body=request_body,
            response_body=None,
            error_msg=code[:500],
            attempt=1,
            elapsed_ms=0,
            trigger="manual",
        )
    if not log_id:
        raise CoworkLinePushError("push_log_failed")
    return {
        "history_id": history_id,
        "log_id": log_id,
        "status": "manual" if adapter == "express" else "failed",
        "accepted": False,
        "error_msg": code,
    }


async def dispatch_confirmed(
    identity: dict[str, Any],
    history_ids: list[str],
    target: dict[str, Any],
    selection: dict[str, Any],
) -> dict[str, Any]:
    """Atomically confirm recognition rows and create one push log for every row."""
    adapter = str(target.get("adapter") or "").lower()
    error_code: str | None = None
    if adapter == "express" and target.get("workspace_client_id") is not None:
        try:
            results = reserve_managed_batch(
                identity,
                history_ids,
                target,
                posting_kind=selection.get("posting_kind"),
            )
            committed = len(results)
        except Exception as exc:
            code = _error_code(exc)
            if code == "cowork_line_intake.draft_changed":
                results = confirmed_batch_result(identity, history_ids, target) or []
                committed = len(results)
                error_code = None if results else code
            else:
                results = [
                    _failure_log(identity, target, history_id, code) for history_id in history_ids
                ]
                committed = 0
    else:
        try:
            endpoint, intents = reserve_legacy_batch(identity, history_ids, target)
            committed = len(intents)
        except Exception as exc:
            code = _error_code(exc)
            if code == "cowork_line_intake.draft_changed":
                results = confirmed_batch_result(identity, history_ids, target) or []
                committed = len(results)
                error_code = None if results else code
            else:
                results = [
                    _failure_log(identity, target, history_id, code) for history_id in history_ids
                ]
                committed = 0
        else:
            results = [
                _push_legacy_intent(
                    identity,
                    endpoint,
                    intent,
                    posting_kind=selection.get("posting_kind"),
                )
                for intent in intents
            ]
    statuses = {str(row["status"]) for row in results}
    response = {
        "results": results,
        "push_ok": bool(results) and all(row["accepted"] for row in results),
        "status": (
            next(iter(statuses)) if len(statuses) == 1 else ("mixed" if results else "failed")
        ),
        "committed": committed,
    }
    if error_code:
        response["error_code"] = error_code
    return response


__all__ = ["CoworkLinePushError", "dispatch_confirmed"]

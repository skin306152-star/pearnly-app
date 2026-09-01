"""Push one confirmed ERP history through the configured endpoint."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from fastapi import HTTPException, Request

from core import db
from core.route_helpers import _tid
from services.erp import erp_push, shared_express_push, team_access
from services.intake_bridge import convert as convert_svc

logger = logging.getLogger("mr-pilot")


def _request_source(user: dict[str, Any]) -> str:
    return {
        "cowork": "cowork_line",
        "erp": "line_erp",
    }.get(str(user.get("entry") or ""), "main")


async def dispatch_confirmed_history(
    *,
    user: dict[str, Any],
    history_id: str,
    endpoint_id: Optional[str] = None,
    posting_kind: Optional[str] = None,
    request: Optional[Request] = None,
    workspace_client_id: Optional[int] = None,
    account_config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Reuse the web push path from LINE without exposing endpoint selection."""
    assigned_endpoint = team_access.assigned_endpoint_for_request(user, endpoint_id)
    effective_endpoint_id = (
        str(assigned_endpoint["id"]) if assigned_endpoint is not None else endpoint_id
    )
    creator_scope = (
        team_access.record_creator_scope(request, user)
        if request is not None
        else (str(user["id"]) if assigned_endpoint is not None else None)
    )
    member_history = None
    if creator_scope:
        member_history = db.get_ocr_history_detail(user["id"], history_id)
        if not member_history:
            raise HTTPException(404, detail="erp.history_not_found")

    if request is not None:
        managed = await shared_express_push.maybe_reserve_manual_push(
            user=user,
            request=request,
            history_id=history_id,
            endpoint_id=effective_endpoint_id,
            posting_kind=posting_kind,
        )
    else:
        managed = await asyncio.to_thread(
            shared_express_push.reserve_managed_manual_push,
            user=user,
            history_id=history_id,
            endpoint_id=effective_endpoint_id,
            requested_workspace_id=workspace_client_id,
            posting_kind=posting_kind,
        )
    if managed is not None:
        return managed

    history = member_history or db.get_ocr_history_detail(
        user["id"], history_id, tenant_id=_tid(user)
    )
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")
    if user.get("entry") == "erp" and not convert_svc.history_is_converted(
        tenant_id=_tid(user), history_id=history_id
    ):
        raise HTTPException(409, detail="erp.history_not_converted")

    if effective_endpoint_id:
        endpoint = assigned_endpoint or db.get_erp_endpoint(user["id"], effective_endpoint_id)
        if not endpoint:
            raise HTTPException(404, detail="erp.endpoint_not_found")
    else:
        endpoint = assigned_endpoint or db.get_default_erp_endpoint(user["id"])
        if not endpoint:
            raise HTTPException(400, detail="erp.no_default_endpoint")
    if not endpoint.get("enabled", True):
        raise HTTPException(400, detail="erp.endpoint_disabled")

    from services.erp.line_target_choice import endpoint_with_account_choice

    endpoint = endpoint_with_account_choice(endpoint, account_config)
    endpoint_config = endpoint.get("config") or {}
    if str(endpoint.get("adapter") or "").lower() == "mrerp":
        selected_account = (
            f"{endpoint_config.get('comidyear') or '6'}:{endpoint_config.get('seldb') or '1'}"
        )
    else:
        selected_account = str(endpoint_config.get("account_set") or "").strip()

    existing = db.has_recent_successful_push(
        history_id,
        endpoint["id"],
        user["id"],
        account_set=selected_account or None,
    )
    if existing:
        log_args = {
            "endpoint_id": str(endpoint["id"]),
            "history_id": history_id,
            "invoice_no": history.get("invoice_no"),
            "seller_name": history.get("seller_name"),
            "total_amount": history.get("total_amount"),
            "status": "skipped_dup",
            "http_status": 200,
            "request_body": {
                "adapter": endpoint.get("adapter"),
                "skipped_reason": "already_success",
                "prior_log_id": str(existing.get("id")),
            },
            "response_body": existing.get("response_body"),
            "error_msg": None,
            "attempt": 1,
            "elapsed_ms": 0,
            "trigger": "manual",
        }
        log_id = (
            team_access.insert_assigned_push_log(user=user, **log_args)
            if assigned_endpoint
            else db.insert_push_log(user_id=user["id"], **log_args)
        )
        logger.info(
            "[push-dedup] skipped manual push · history=%s endpoint=%s prior=%s",
            history_id[:8],
            str(endpoint["id"])[:8],
            str(existing.get("id"))[:8],
        )
        if not log_id:
            logger.warning(
                "[push-dedup] skipped_dup log not persisted · history=%s", history_id[:8]
            )
        return {
            "ok": True,
            "log_id": log_id,
            "log_write_failed": not log_id,
            "http_status": 200,
            "skipped_dup": True,
            "prior_log_id": str(existing.get("id")),
            "endpoint_name": endpoint.get("name"),
        }

    result = await asyncio.to_thread(
        erp_push.push_to_endpoint,
        endpoint,
        history,
        posting_kind=posting_kind,
    )
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    request_body = result.get("request_body")
    request_body = dict(request_body) if isinstance(request_body, dict) else {}
    request_body["source"] = _request_source(user)
    log_args = {
        "endpoint_id": str(endpoint["id"]),
        "history_id": history_id,
        "invoice_no": history.get("invoice_no"),
        "seller_name": history.get("seller_name"),
        "total_amount": history.get("total_amount"),
        "status": final_status,
        "http_status": result.get("http_status"),
        "request_body": request_body,
        "response_body": result.get("response_body"),
        "error_msg": result.get("error_msg"),
        "attempt": 1,
        "elapsed_ms": result.get("elapsed_ms", 0),
    }
    log_id = (
        team_access.insert_assigned_push_log(user=user, **log_args)
        if assigned_endpoint
        else db.insert_push_log(user_id=user["id"], **log_args)
    )
    db.update_endpoint_stats(endpoint["id"], db.counts_as_endpoint_success(final_status))
    db.update_history_push_status(history_id, final_status)

    retry_scheduled = False
    if final_status == "failed" and log_id and not db.is_user_data_error(result.get("error_msg")):
        first_delay = db.get_erp_retry_delay_sec(0)
        if first_delay is not None:
            retry_scheduled = bool(db.schedule_log_retry(str(log_id), first_delay))

    if final_status == "success" and log_id:
        from services.erp.line_push_notification import notify_success

        await asyncio.to_thread(notify_success, str(log_id))

    presented_status = "retrying" if retry_scheduled else final_status

    return {
        "ok": bool(result["success"] or final_status == "skipped_dup" or retry_scheduled),
        "log_id": log_id,
        "status": presented_status,
        "skipped_dup": final_status == "skipped_dup",
        "http_status": result.get("http_status"),
        "error_msg": result.get("error_msg"),
        "elapsed_ms": result.get("elapsed_ms"),
        "endpoint_name": endpoint.get("name"),
    }


__all__ = ["dispatch_confirmed_history"]

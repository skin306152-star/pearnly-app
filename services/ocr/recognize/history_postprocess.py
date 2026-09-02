"""Run OCR history side effects only after the whole batch is stored."""

from __future__ import annotations

import logging
from typing import Any

from core import db
from core.route_helpers import _tid
from services.exceptions.exception_checks import _async_run_exception_checks

logger = logging.getLogger("mr-pilot")


def charge_batch(
    user: dict,
    billing: dict,
    charge_kind: str,
    charge_units: int,
    filename: str,
    history_id: str,
) -> None:
    if billing.get("is_exempt") or charge_units <= 0:
        return
    args = (
        str(user.get("id")),
        _tid(user),
        charge_kind,
        charge_units,
        str(history_id),
        f"OCR {charge_kind} · {filename} · {str(history_id)[:8]}",
    )
    try:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            loop.create_task(asyncio.to_thread(db.charge_ocr_async, *args))
        else:
            db.charge_ocr_async(*args)
    except Exception as exc:
        logger.warning("OCR charge dispatch skipped: %s", exc)


def _resolve_buyer(
    user: dict,
    client_id: Any,
    history_id: str,
    fields: dict,
    pages: list[dict],
) -> None:
    existing_client = int(client_id) if client_id and str(client_id).strip().isdigit() else None
    if existing_client:
        return
    buyer_name = fields.get("buyer_name")
    buyer_tax = fields.get("buyer_tax")
    candidates = [(page.get("fields") or {}).get("buyer_name") for page in pages]
    decision = db.resolve_or_create_buyer_client(
        buyer_name=buyer_name,
        buyer_tax=buyer_tax,
        user_id=str(user["id"]),
        tenant_id=_tid(user),
        buyer_candidates=candidates,
    )
    action = decision.get("action")
    resolved_id = decision.get("client_id")
    if action in {"assigned", "created"} and resolved_id:
        db.update_history_client_id(history_id, resolved_id, str(user["id"]), tenant_id=_tid(user))
        logger.info(
            "[buyer-resolve] %s history=%s client_id=%s name=%r conf=%.2f source=%s",
            action,
            history_id[:8],
            resolved_id,
            decision.get("client_name"),
            decision.get("confidence", 0.0),
            decision.get("match_source"),
        )
        return
    if action == "suggest" and resolved_id:
        suggested_pages = [dict(page) for page in pages]
        if suggested_pages:
            first_fields = dict(suggested_pages[0].get("fields") or {})
            first_fields["_suggested_client_id"] = resolved_id
            first_fields["_suggested_client_name"] = decision.get("client_name")
            first_fields["_suggested_client_confidence"] = decision.get("confidence")
            suggested_pages[0] = {**suggested_pages[0], "fields": first_fields}
            db.update_ocr_history_pages(
                str(user["id"]), history_id, suggested_pages, tenant_id=_tid(user)
            )
        return
    logger.info(
        "[buyer-resolve] %s history=%s buyer=%r reason=%s",
        action,
        history_id[:8],
        str(buyer_name or "")[:40],
        decision.get("reason"),
    )


def process_history(
    *,
    user: dict,
    client_id: Any,
    history_id: str,
    fields: dict,
    pages: list[dict],
    confidence: str,
    duplicate_warning: dict | None,
) -> None:
    try:
        _resolve_buyer(user, client_id, history_id, fields, pages)
    except Exception as exc:
        logger.warning("buyer-resolve client_id failed (history=%s): %s", history_id[:8], exc)

    try:
        import asyncio

        total_amount = None
        raw_total = fields.get("total_amount")
        if raw_total:
            try:
                total_amount = float(str(raw_total).replace(",", "").strip())
            except (TypeError, ValueError):
                logger.warning("[exc_check] total_amount parse failed: %r", raw_total)
        asyncio.create_task(
            _async_run_exception_checks(
                history_id=str(history_id),
                user_id=str(user["id"]),
                tenant_id=_tid(user),
                seller_name=fields.get("seller_name"),
                invoice_no=fields.get("invoice_number"),
                total_amount=total_amount,
                confidence=confidence,
                duplicate=duplicate_warning,
                fields=fields,
            )
        )
    except Exception as exc:
        logger.warning("exception check enqueue failed: %s", exc)


__all__ = ["charge_batch", "process_history"]

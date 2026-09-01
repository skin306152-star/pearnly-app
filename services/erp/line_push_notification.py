"""Send a concise LINE receipt after an ERP push reaches a verified success state."""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from core import db
from services.erp.external_ref import derive_external_ref, request_payload
from services.line_platform import client as line_client

logger = logging.getLogger("mr-pilot")


def _object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _recipient(cur, row: dict[str, Any], source: str) -> tuple[str, str] | None:
    if source == "cowork_line":
        cur.execute(
            "SELECT line_user_id FROM cowork_line_identities "
            "WHERE user_id = %s AND tenant_id = %s AND revoked_at IS NULL LIMIT 1",
            (str(row["user_id"]), str(row["tenant_id"])),
        )
        channel = "cowork"
    elif source == "line_erp":
        cur.execute(
            "SELECT line_user_id FROM line_erp_bindings "
            "WHERE user_id = %s AND tenant_id = %s LIMIT 1",
            (str(row["user_id"]), str(row["tenant_id"])),
        )
        channel = "erp"
    else:
        return None
    binding = cur.fetchone()
    return (str(binding["line_user_id"]), channel) if binding else None


def _amount(value: Any) -> str:
    try:
        return f"฿{Decimal(str(value)):,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return "-"


def _account_label(row: dict[str, Any], request: dict[str, Any]) -> str:
    payload = request_payload(request)
    config = _object(row.get("endpoint_config"))
    for candidate in (
        payload.get("account_set"),
        payload.get("account_dir"),
        request.get("account_set"),
        row.get("bound_account_set"),
        config.get("account_set"),
    ):
        label = str(candidate or "").strip()
        if label:
            return label
    comidyear = payload.get("comidyear") or config.get("comidyear")
    seldb = payload.get("seldb") or config.get("seldb")
    return f"{comidyear}:{seldb}" if comidyear and seldb else "-"


def _message(row: dict[str, Any], request: dict[str, Any]) -> str:
    adapter = str(row.get("adapter") or "ERP").strip()
    reference = derive_external_ref(adapter, row.get("response_body"), "success")
    lines = [
        "บันทึกเข้า ERP สำเร็จ",
        f"เอกสาร: {row.get('invoice_no') or '-'}",
        f"ERP: {row.get('endpoint_name') or adapter.upper()}",
        f"ชุดบัญชี: {_account_label(row, request)}",
    ]
    if reference["external_doc_no"]:
        lines.append(f"เลขที่ใน ERP: {reference['external_doc_no']}")
    lines.append(f"ยอดรวม: {_amount(row.get('total_amount'))}")
    return "\n".join(lines)


def notify_success(log_id: str) -> bool:
    """Notify only LINE-origin pushes; notification failure never changes ERP status."""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT l.user_id,COALESCE(l.tenant_id,u.tenant_id) AS tenant_id,"
                "l.invoice_no,l.total_amount,l.request_body,"
                "l.response_body,e.name AS endpoint_name,e.adapter,e.config AS endpoint_config,"
                "e.bound_account_set FROM erp_push_logs l "
                "JOIN erp_endpoints e ON e.id = l.endpoint_id "
                "JOIN users u ON u.id = l.user_id "
                "WHERE l.id = %s AND l.status = 'success' LIMIT 1",
                (str(log_id),),
            )
            found = cur.fetchone()
            if not found:
                return False
            row = dict(found)
            request = _object(row.get("request_body"))
            recipient = _recipient(cur, row, str(request.get("source") or ""))
        if not recipient:
            return False
        line_user_id, channel = recipient
        sent = line_client.push_text(line_user_id, _message(row, request), channel=channel)
        if not sent:
            logger.warning("ERP LINE success receipt failed · log=%s channel=%s", log_id, channel)
        return sent
    except Exception:
        logger.exception("ERP LINE success receipt crashed · log=%s", log_id)
        return False


__all__ = ["notify_success"]

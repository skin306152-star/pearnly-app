"""Resolve a document-owned managed endpoint and record a safe unavailable state."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Optional

WORKSPACE_ENDPOINT_REQUIRED = "erp.workspace_endpoint_required"


def resolve_document_endpoint(
    cur,
    *,
    endpoint_id: Optional[str],
    tenant_id: str,
    workspace_client_id: int,
    lookup: Callable[..., Optional[str]],
) -> tuple[Optional[str], bool]:
    exact = lookup(
        cur,
        endpoint_id=endpoint_id,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
    )
    if exact is not None or endpoint_id is None:
        return exact, False
    fallback = lookup(
        cur,
        endpoint_id=None,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
    )
    return fallback, fallback is not None


def insert_workspace_endpoint_required(
    cur,
    *,
    actor_id: str,
    tenant_id: str,
    workspace_client_id: int,
    history_id: str,
    history: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    request_body = {
        "adapter": "express",
        "source": source,
        "preflight_failure": WORKSPACE_ENDPOINT_REQUIRED,
    }
    cur.execute(
        "INSERT INTO erp_push_logs "
        "(user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,status,http_status,"
        "request_body,response_body,error_msg,attempt,elapsed_ms,trigger,tenant_id,workspace_client_id) "
        "VALUES (%s,NULL,%s,%s,%s,%s,'manual',409,%s::jsonb,NULL,%s,1,0,'manual',%s,%s) "
        "RETURNING id::text AS id,status",
        (
            actor_id,
            history_id,
            history.get("invoice_no"),
            history.get("seller_name"),
            history.get("total_amount"),
            json.dumps(request_body, ensure_ascii=False),
            WORKSPACE_ENDPOINT_REQUIRED,
            tenant_id,
            workspace_client_id,
        ),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("managed Express manual log insert returned no row")
    return {
        "history_id": history_id,
        "log_id": str(row["id"]),
        "status": "manual",
        "accepted": False,
        "error_msg": WORKSPACE_ENDPOINT_REQUIRED,
    }


def reserve_confirmed_without_endpoint(
    cur,
    *,
    actor_id: str,
    tenant_id: str,
    workspace_client_id: int,
    history_id: str,
    history: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    item = insert_workspace_endpoint_required(
        cur,
        actor_id=actor_id,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        history_id=history_id,
        history=history,
        source=source,
    )
    cur.execute(
        "UPDATE ocr_history SET last_push_status = 'manual', "
        "last_pushed_at = clock_timestamp() "
        "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
        (history_id, tenant_id, workspace_client_id),
    )
    if cur.rowcount != 1:
        raise RuntimeError("managed Express manual history mirror rowcount mismatch")
    return {
        "ok": False,
        "queued": False,
        **item,
        "endpoint_id": None,
        "endpoint_name": None,
        "http_status": 409,
        "reused": False,
    }


__all__ = [
    "WORKSPACE_ENDPOINT_REQUIRED",
    "insert_workspace_endpoint_required",
    "reserve_confirmed_without_endpoint",
    "resolve_document_endpoint",
]

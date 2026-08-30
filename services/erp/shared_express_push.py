"""Atomic manual reservation for tenant-managed shared Express endpoints."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import HTTPException, Request

from core import db
from services.authz.resolver import resolve
from services.erp.express_push.enqueue import QUEUED_SENTINEL, enqueue_express
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for
from services.erp.shared_express_live import _profile_is_fresh
from services.erp.shared_express_schema import enable_shared_express_select
from services.ocr_history.queries import _DETAIL_COLUMNS, _detail_row

_WEB_ENTRIES = frozenset({"main", "cowork", "erp"})
_DIRECTION_PERMISSIONS = {
    "purchase": ("purchase.doc.create", "purchase.doc.approve"),
    "sales": ("sales.doc.create", "sales.doc.approve"),
}


def _uuid(value: object, detail: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise HTTPException(404, detail=detail) from exc


def _workspace_id(raw: object) -> Optional[int]:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value.isdigit() or int(value) <= 0:
        raise HTTPException(400, detail="workspace.required")
    return int(value)


def _row_dict(row: Any) -> Dict[str, Any]:
    return dict(row) if row and hasattr(row, "keys") else {}


def _default_workspace(cur, tenant_id: str) -> int:
    cur.execute(
        "SELECT id FROM workspace_clients WHERE tenant_id = %s AND is_active = TRUE "
        "ORDER BY created_at, id LIMIT 1",
        (tenant_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(400, detail="workspace.required")
    return int(row["id"])


def _legacy_selected(cur, actor_id: str, endpoint_id: Optional[str]) -> bool:
    if endpoint_id:
        cur.execute(
            "SELECT binding_generation FROM erp_endpoints WHERE id = %s LIMIT 1",
            (endpoint_id,),
        )
    else:
        cur.execute(
            "SELECT binding_generation FROM erp_endpoints "
            "WHERE user_id = %s AND enabled = TRUE AND binding_generation = 0 "
            "ORDER BY is_default DESC, created_at LIMIT 1",
            (actor_id,),
        )
    row = cur.fetchone()
    return row is not None and int(row.get("binding_generation") or 0) == 0


def _managed_endpoint_id(
    cur, *, endpoint_id: Optional[str], tenant_id: str, workspace_client_id: int
) -> Optional[str]:
    where_id = "AND id = %s" if endpoint_id else ""
    params = [tenant_id, workspace_client_id]
    if endpoint_id:
        params.append(endpoint_id)
    cur.execute(
        "SELECT id::text AS id FROM erp_endpoints "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND adapter = 'express' AND binding_generation > 0 "
        "AND enabled = TRUE AND shared_scope = TRUE "
        f"AND revoked_at IS NULL {where_id} ORDER BY created_at, id LIMIT 2",
        tuple(params),
    )
    rows = cur.fetchall() or []
    if len(rows) > 1:
        raise HTTPException(409, detail="erp.shared_endpoint_conflict")
    return str(rows[0]["id"]) if rows else None


def _lock_actor_and_workspace(
    cur, *, actor_id: str, tenant_id: str, workspace_client_id: int, endpoint_id: str
) -> None:
    cur.execute(
        "SELECT id FROM users WHERE id = %s AND tenant_id = %s AND is_active = TRUE FOR UPDATE",
        (actor_id, tenant_id),
    )
    if not cur.fetchone():
        raise HTTPException(404, detail="authz.not_found")
    cur.execute(
        "SELECT id, erp_endpoint_id FROM workspace_clients "
        "WHERE id = %s AND tenant_id = %s AND is_active = TRUE FOR UPDATE",
        (workspace_client_id, tenant_id),
    )
    workspace = cur.fetchone()
    if not workspace or str(workspace.get("erp_endpoint_id") or "") != endpoint_id:
        raise HTTPException(404, detail="authz.not_found")


def _endpoint_after_lock(
    cur, *, endpoint_id: str, tenant_id: str, workspace_client_id: int
) -> Dict[str, Any]:
    cur.execute(
        "SELECT id, user_id, name, adapter, config, enabled, shared_scope, tenant_id, "
        "workspace_client_id, binding_generation, bound_account_set, bound_profile_key, "
        "live_account_set, live_profile_key, agent_last_seen_at, revoked_at, "
        "clock_timestamp() AS db_now FROM erp_endpoints "
        "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s LIMIT 1",
        (endpoint_id, tenant_id, workspace_client_id),
    )
    endpoint = _row_dict(cur.fetchone())
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    if (
        str(endpoint.get("adapter") or "").lower() != "express"
        or int(endpoint.get("binding_generation") or 0) < 1
        or endpoint.get("enabled") is not True
        or endpoint.get("shared_scope") is not True
        or endpoint.get("revoked_at") is not None
    ):
        raise HTTPException(409, detail="erp.endpoint_not_ready")
    bound = (endpoint.get("bound_account_set"), endpoint.get("bound_profile_key"))
    live = (endpoint.get("live_account_set"), endpoint.get("live_profile_key"))
    if None in bound or bound != live:
        raise HTTPException(409, detail="erp.profile_not_ready")
    if not _profile_is_fresh(endpoint.get("agent_last_seen_at"), endpoint.get("db_now")):
        raise HTTPException(409, detail="erp.agent_offline")
    return endpoint


def _locked_history(
    cur, *, history_id: str, tenant_id: str, workspace_client_id: int
) -> Dict[str, Any]:
    cur.execute(
        f"SELECT {_DETAIL_COLUMNS}, user_id::text AS owner_id "
        "FROM ocr_history WHERE id = %s AND tenant_id = %s "
        "AND workspace_client_id = %s AND staged = FALSE FOR UPDATE",
        (history_id, tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, detail="erp.history_not_found")
    return _detail_row(row)


def _formal_direction(cur, *, history_id: str, tenant_id: str, workspace_client_id: int) -> str:
    cur.execute(
        "SELECT id FROM purchase_docs WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND ocr_history_id = %s AND status = 'posted' LIMIT 1 FOR SHARE",
        (tenant_id, workspace_client_id, history_id),
    )
    purchase = cur.fetchone() is not None
    cur.execute(
        "SELECT id FROM sales_documents WHERE tenant_id = %s "
        "AND seller_workspace_client_id = %s AND ocr_history_id = %s "
        "AND status = 'issued' LIMIT 1 FOR SHARE",
        (tenant_id, workspace_client_id, history_id),
    )
    sales = cur.fetchone() is not None
    if purchase == sales:
        raise HTTPException(409, detail="erp.formal_document_required")
    return "purchase" if purchase else "sales"


def _existing_log(
    cur, *, tenant_id: str, workspace_client_id: int, endpoint_id: str, history_id: str
) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    scope = "tenant_id = %s AND workspace_client_id = %s AND endpoint_id = %s AND history_id = %s"
    params = (tenant_id, workspace_client_id, endpoint_id, history_id)
    cur.execute(
        "SELECT id::text AS id,status,http_status,response_body,created_at "
        f"FROM erp_push_logs WHERE {scope} "
        "AND (status IN ('pending','retrying') OR lease_owner IS NOT NULL) "
        "ORDER BY created_at DESC,id DESC LIMIT 1",
        params,
    )
    active = _row_dict(cur.fetchone()) or None
    cur.execute(
        "SELECT id::text AS id,status,http_status,response_body,created_at "
        f"FROM erp_push_logs WHERE {scope} AND status = 'success' "
        "ORDER BY created_at DESC,id DESC LIMIT 1",
        params,
    )
    success = _row_dict(cur.fetchone()) or None
    return active, success


def _queued_response(row: Dict[str, Any], endpoint: Dict[str, Any], *, reused: bool) -> dict:
    return {
        "ok": True,
        "queued": True,
        "status": str(row.get("status") or "pending"),
        "log_id": str(row["id"]),
        "endpoint_id": str(endpoint["id"]),
        "endpoint_name": endpoint.get("name"),
        "http_status": 202,
        "reused": reused,
    }


def reserve_managed_manual_push(
    *,
    user: Dict[str, Any],
    history_id: str,
    endpoint_id: Optional[str],
    requested_workspace_id: Optional[int],
    posting_kind: Optional[str],
) -> Optional[dict]:
    tenant_id = str(user.get("tenant_id") or "").strip()
    actor_id = str(user.get("id") or "").strip()
    if user.get("entry") not in _WEB_ENTRIES or not erp_shared_express_endpoint_enabled_for(
        tenant_id
    ):
        return None
    if not tenant_id or not actor_id:
        raise HTTPException(404, detail="authz.not_found")
    history_id = _uuid(history_id, "erp.history_not_found")
    endpoint_id = _uuid(endpoint_id, "erp.endpoint_not_found") if endpoint_id else None

    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        if _legacy_selected(cur, actor_id, endpoint_id):
            return None
        workspace_client_id = requested_workspace_id or _default_workspace(cur, tenant_id)
        cur.execute("SET LOCAL app.current_workspace_id = %s", (str(workspace_client_id),))
        if not enable_shared_express_select(cur, tenant_id, workspace_client_id):
            raise HTTPException(503, detail="erp.shared_endpoint_unavailable")
        managed_endpoint_id = _managed_endpoint_id(
            cur,
            endpoint_id=endpoint_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
        )
        if managed_endpoint_id is None:
            return None

        lock_endpoint_binding(cur, managed_endpoint_id)
        authz = resolve(user, cur=cur, lock=True)
        if (
            authz.membership_id is None
            or not authz.has("erp.push.operate")
            or not authz.allows_workspace(workspace_client_id)
        ):
            raise HTTPException(403, detail="authz.forbidden")
        _lock_actor_and_workspace(
            cur,
            actor_id=actor_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            endpoint_id=managed_endpoint_id,
        )
        endpoint = _endpoint_after_lock(
            cur,
            endpoint_id=managed_endpoint_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
        )
        history = _locked_history(
            cur,
            history_id=history_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
        )
        direction = _formal_direction(
            cur,
            history_id=history_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
        )
        if any(not authz.has(code) for code in _DIRECTION_PERMISSIONS[direction]):
            raise HTTPException(403, detail="authz.forbidden")

        active, success = _existing_log(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            endpoint_id=managed_endpoint_id,
            history_id=history_id,
        )
        if success:
            return {
                "ok": True,
                "queued": False,
                "status": "skipped_dup",
                "skipped_dup": True,
                "log_id": str(success["id"]),
                "prior_log_id": str(success["id"]),
                "endpoint_id": managed_endpoint_id,
                "endpoint_name": endpoint.get("name"),
                "http_status": 200,
                "reused": True,
            }
        if active:
            return _queued_response(active, endpoint, reused=True)

        endpoint_for_payload = dict(endpoint)
        config = dict(endpoint.get("config") or {})
        config["account_set"] = endpoint["bound_account_set"]
        endpoint_for_payload.update({"config": config, "user_id": actor_id})
        result = enqueue_express(endpoint_for_payload, history, posting_kind=posting_kind)
        payload = result.get("request_body")
        if result.get("error_msg") != QUEUED_SENTINEL or not isinstance(payload, dict):
            raise HTTPException(
                409,
                detail={
                    "code": "erp.push_not_queueable",
                    "reason": str(result.get("error_msg") or "preflight_failed")[:200],
                },
            )
        if payload.get("direction") != direction:
            raise HTTPException(409, detail="erp.formal_direction_mismatch")
        request_body = dict(payload)
        request_body["managed_generation"] = int(endpoint["binding_generation"])
        cur.execute(
            "INSERT INTO erp_push_logs "
            "(user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,status,http_status,"
            "request_body,response_body,error_msg,attempt,elapsed_ms,trigger,tenant_id,workspace_client_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,'pending',202,%s::jsonb,%s,%s,1,%s,'manual',%s,%s) "
            "RETURNING id::text AS id,status",
            (
                actor_id,
                managed_endpoint_id,
                history_id,
                history.get("invoice_no"),
                history.get("seller_name"),
                history.get("total_amount"),
                json.dumps(request_body, ensure_ascii=False),
                result.get("response_body"),
                QUEUED_SENTINEL,
                int(result.get("elapsed_ms") or 0),
                tenant_id,
                workspace_client_id,
            ),
        )
        inserted = _row_dict(cur.fetchone())
        if not inserted:
            raise RuntimeError("managed Express reservation insert returned no row")
        cur.execute(
            "UPDATE ocr_history SET last_push_status = 'pending', "
            "last_pushed_at = clock_timestamp() "
            "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
            (history_id, tenant_id, workspace_client_id),
        )
        if cur.rowcount != 1:
            raise RuntimeError("managed Express history mirror rowcount mismatch")
        return _queued_response(inserted, endpoint, reused=False)


async def maybe_reserve_manual_push(
    *,
    user: Dict[str, Any],
    request: Request,
    history_id: str,
    endpoint_id: Optional[str],
    posting_kind: Optional[str],
) -> Optional[dict]:
    raw_workspace = request.headers.get("X-Workspace-Client-Id")

    def run() -> Optional[dict]:
        requested_workspace_id = None
        tenant_id = str(user.get("tenant_id") or "").strip()
        if user.get("entry") in _WEB_ENTRIES and erp_shared_express_endpoint_enabled_for(tenant_id):
            requested_workspace_id = _workspace_id(raw_workspace)
        return reserve_managed_manual_push(
            user=user,
            history_id=history_id,
            endpoint_id=endpoint_id,
            requested_workspace_id=requested_workspace_id,
            posting_kind=posting_kind,
        )

    return await asyncio.to_thread(run)


__all__ = ["maybe_reserve_manual_push", "reserve_managed_manual_push"]

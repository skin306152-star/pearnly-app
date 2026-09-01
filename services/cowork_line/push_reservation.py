"""Atomic Cowork recognition confirmation and ERP push-intent reservation."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from core import db
from services.authz.resolver import resolve
from services.cowork_line.push_recovery import (
    LEGACY_RESERVATION_LEASE,
    settle_stale_legacy,
)
from services.erp.express_push.enqueue import QUEUED_SENTINEL, enqueue_express
from services.erp.legacy_generation import lock_endpoint_binding, lock_legacy_endpoint
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for
from services.erp.shared_express_push import (
    _confirmed_direction,
    _endpoint_after_lock,
    _existing_log,
    _legacy_selected,
    _lock_actor_and_workspace,
    _managed_endpoint_id,
    _queued_response,
)
from services.erp.shared_express_schema import enable_shared_express_select
from services.ocr_history.queries import _DETAIL_COLUMNS, _detail_row

_ACCEPTED_STATUSES = {"success", "pending", "retrying", "skipped_dup"}


def _uuid(value: object, code: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise HTTPException(404, detail=code) from exc


def _identity(identity: dict[str, Any]) -> tuple[str, str]:
    tenant_id = str(identity.get("tenant_id") or "").strip()
    actor_id = str(identity.get("user_id") or "").strip()
    if not tenant_id or not actor_id:
        raise HTTPException(404, detail="authz.not_found")
    return tenant_id, actor_id


def _active_actor(cur, identity: dict[str, Any], workspace_id: int):
    membership_id = str(identity.get("membership_id") or "").strip()
    tenant_id = str(identity.get("tenant_id") or "").strip()
    actor_id = str(identity.get("user_id") or "").strip()
    line_user_id = str(identity.get("line_user_id") or "").strip()
    if not membership_id or not tenant_id or not actor_id or not line_user_id:
        raise HTTPException(403, detail="authz.forbidden")
    cur.execute(
        "SELECT u.role,u.invited_by FROM cowork_line_identities identity "
        "JOIN memberships membership ON membership.id = identity.membership_id "
        "AND membership.user_id = identity.user_id "
        "AND membership.tenant_id = identity.tenant_id "
        "JOIN users u ON u.id = identity.user_id AND u.tenant_id = identity.tenant_id "
        "WHERE identity.membership_id = %s AND identity.tenant_id = %s "
        "AND identity.user_id = %s AND identity.line_user_id = %s "
        "AND identity.revoked_at IS NULL AND membership.status = 'active' "
        "AND u.is_active = TRUE FOR SHARE OF identity,membership,u",
        (membership_id, tenant_id, actor_id, line_user_id),
    )
    actor = cur.fetchone()
    if not actor:
        raise HTTPException(403, detail="authz.forbidden")
    authz = resolve(
        {
            "id": actor_id,
            "tenant_id": tenant_id,
            "role": actor.get("role"),
            "invited_by": actor.get("invited_by"),
            "entry": "cowork",
        },
        cur=cur,
        lock=True,
    )
    if (
        str(authz.membership_id or "") != membership_id
        or not authz.has("erp.endpoint.view")
        or not authz.has("erp.push.operate")
        or not authz.allows_workspace(workspace_id)
    ):
        raise HTTPException(403, detail="authz.forbidden")
    return authz


def confirmed_batch_result(
    identity: dict[str, Any], history_ids: list[str], target: dict[str, Any]
) -> list[dict[str, Any]] | None:
    """Return the already-reserved canonical result for an idempotent confirm retry."""
    tenant_id, actor_id = _identity(identity)
    endpoint_id = _uuid(target.get("endpoint_id"), "erp.endpoint_not_found")
    workspace_id = int(target.get("workspace_client_id") or 0)
    ids = [_uuid(value, "erp.history_not_found") for value in history_ids]
    if not workspace_id or not ids:
        return None
    results: list[dict[str, Any]] = []
    with db.get_cursor_rls(
        tenant_id=tenant_id,
        user_id=actor_id,
        workspace_client_id=workspace_id,
        commit=True,
    ) as cur:
        _active_actor(cur, identity, workspace_id)
        settle_stale_legacy(cur, tenant_id, actor_id)
        for history_id in ids:
            cur.execute(
                "SELECT id FROM ocr_history WHERE id = %s AND tenant_id = %s "
                "AND user_id = %s AND workspace_client_id = %s AND staged = FALSE FOR SHARE",
                (history_id, tenant_id, actor_id, workspace_id),
            )
            if not cur.fetchone():
                return None
            cur.execute(
                "SELECT id::text AS id,status,error_msg FROM erp_push_logs "
                "WHERE tenant_id = %s AND workspace_client_id = %s AND endpoint_id = %s "
                "AND history_id = %s AND user_id = %s ORDER BY created_at DESC,id DESC LIMIT 1",
                (tenant_id, workspace_id, endpoint_id, history_id, actor_id),
            )
            log = cur.fetchone()
            if not log:
                return None
            status = str(log["status"])
            results.append(
                {
                    "history_id": history_id,
                    "log_id": str(log["id"]),
                    "status": status,
                    "accepted": status in _ACCEPTED_STATUSES,
                    "error_msg": log.get("error_msg"),
                }
            )
    return results


def _staged_history(cur, history_id: str, tenant_id: str, actor_id: str, workspace_id: int):
    cur.execute(
        f"SELECT {_DETAIL_COLUMNS} FROM ocr_history "
        "WHERE id = %s AND tenant_id = %s AND user_id = %s "
        "AND workspace_client_id = %s AND staged = TRUE FOR UPDATE",
        (history_id, tenant_id, actor_id, workspace_id),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(409, detail="cowork_line_intake.draft_changed")
    return _detail_row(row)


def reserve_managed_batch(
    identity: dict[str, Any],
    history_ids: list[str],
    target: dict[str, Any],
    *,
    posting_kind: str | None,
) -> list[dict[str, Any]]:
    """Confirm all staged rows and enqueue all Express intents in one transaction."""
    tenant_id, actor_id = _identity(identity)
    endpoint_id = _uuid(target.get("endpoint_id"), "erp.endpoint_not_found")
    workspace_id = int(target.get("workspace_client_id") or 0)
    ids = [_uuid(value, "erp.history_not_found") for value in history_ids]
    if not workspace_id or not ids:
        raise HTTPException(409, detail="workspace.required")
    if not erp_shared_express_endpoint_enabled_for(tenant_id):
        raise HTTPException(409, detail="erp.shared_endpoint_unavailable")

    results: list[dict[str, Any]] = []
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        if _legacy_selected(cur, actor_id, endpoint_id):
            raise HTTPException(409, detail="erp.endpoint_changed")
        cur.execute("SET LOCAL app.current_workspace_id = %s", (str(workspace_id),))
        if not enable_shared_express_select(cur, tenant_id, workspace_id):
            raise HTTPException(503, detail="erp.shared_endpoint_unavailable")
        managed_id = _managed_endpoint_id(
            cur,
            endpoint_id=endpoint_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_id,
        )
        if managed_id is None:
            raise HTTPException(409, detail="erp.endpoint_changed")
        lock_endpoint_binding(cur, managed_id)
        _active_actor(cur, identity, workspace_id)
        _lock_actor_and_workspace(
            cur,
            actor_id=actor_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_id,
            endpoint_id=managed_id,
        )
        endpoint = _endpoint_after_lock(
            cur,
            endpoint_id=managed_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_id,
        )
        endpoint_for_payload = dict(endpoint)
        config = dict(endpoint.get("config") or {})
        config["account_set"] = endpoint["bound_account_set"]
        endpoint_for_payload.update({"config": config, "user_id": actor_id})

        for history_id in ids:
            history = _staged_history(cur, history_id, tenant_id, actor_id, workspace_id)
            direction = _confirmed_direction(
                cur,
                history_id=history_id,
                tenant_id=tenant_id,
                workspace_client_id=workspace_id,
                history=history,
                entry="cowork",
            )
            active, success = _existing_log(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_id,
                endpoint_id=managed_id,
                history_id=history_id,
            )
            if success:
                item = {
                    "history_id": history_id,
                    "log_id": str(success["id"]),
                    "status": "skipped_dup",
                    "accepted": True,
                }
            elif active:
                queued = _queued_response(active, endpoint, reused=True)
                item = {
                    "history_id": history_id,
                    "log_id": queued["log_id"],
                    "status": queued["status"],
                    "accepted": True,
                }
            else:
                prepared = enqueue_express(endpoint_for_payload, history, posting_kind=posting_kind)
                payload = prepared.get("request_body")
                if prepared.get("error_msg") != QUEUED_SENTINEL or not isinstance(payload, dict):
                    raise HTTPException(
                        409,
                        detail={
                            "code": "erp.push_not_queueable",
                            "reason": str(prepared.get("error_msg") or "preflight_failed")[:200],
                        },
                    )
                if payload.get("direction") != direction:
                    raise HTTPException(409, detail="erp.formal_direction_mismatch")
                request_body = dict(payload)
                request_body["managed_generation"] = int(endpoint["binding_generation"])
                cur.execute(
                    "INSERT INTO erp_push_logs "
                    "(user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,status,"
                    "http_status,request_body,response_body,error_msg,attempt,elapsed_ms,trigger,"
                    "tenant_id,workspace_client_id) "
                    "VALUES (%s,%s,%s,%s,%s,%s,'pending',202,%s::jsonb,%s,%s,1,%s,'manual',%s,%s) "
                    "RETURNING id::text AS id,status",
                    (
                        actor_id,
                        managed_id,
                        history_id,
                        history.get("invoice_no"),
                        history.get("seller_name"),
                        history.get("total_amount"),
                        json.dumps(request_body, ensure_ascii=False),
                        prepared.get("response_body"),
                        QUEUED_SENTINEL,
                        int(prepared.get("elapsed_ms") or 0),
                        tenant_id,
                        workspace_id,
                    ),
                )
                inserted = cur.fetchone()
                if not inserted:
                    raise RuntimeError("managed Express reservation insert returned no row")
                item = {
                    "history_id": history_id,
                    "log_id": str(inserted["id"]),
                    "status": str(inserted["status"]),
                    "accepted": True,
                }
            cur.execute(
                "UPDATE ocr_history SET staged = FALSE,last_push_status = %s,"
                "last_pushed_at = clock_timestamp(),updated_at = clock_timestamp() "
                "WHERE id = %s AND tenant_id = %s AND user_id = %s AND staged = TRUE",
                (item["status"], history_id, tenant_id, actor_id),
            )
            if cur.rowcount != 1:
                raise RuntimeError("managed Express confirmation rowcount mismatch")
            results.append(item)
    return results


def _prior_success(cur, endpoint_id: str, actor_id: str, history: dict[str, Any]):
    cur.execute(
        "SELECT id::text AS id,response_body FROM erp_push_logs "
        "WHERE endpoint_id = %s AND user_id = %s AND status = 'success' "
        "AND (history_id = %s OR (invoice_no = %s AND COALESCE(seller_name,'') = COALESCE(%s,''))) "
        "ORDER BY created_at DESC,id DESC LIMIT 1",
        (
            endpoint_id,
            actor_id,
            history["id"],
            history.get("invoice_no"),
            history.get("seller_name"),
        ),
    )
    return cur.fetchone()


def reserve_legacy_batch(
    identity: dict[str, Any], history_ids: list[str], target: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Confirm Cowork rows and reserve legacy ERP outbox rows before external I/O."""
    tenant_id, actor_id = _identity(identity)
    endpoint_id = _uuid(target.get("endpoint_id"), "erp.endpoint_not_found")
    workspace_id = int(target.get("workspace_client_id") or 0)
    ids = [_uuid(value, "erp.history_not_found") for value in history_ids]
    if not workspace_id or not ids:
        raise HTTPException(409, detail="workspace.required")
    intents: list[dict[str, Any]] = []
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
        lock_endpoint_binding(cur, endpoint_id)
        if not lock_legacy_endpoint(cur, endpoint_id, actor_id):
            raise HTTPException(409, detail="erp.endpoint_changed")
        _active_actor(cur, identity, workspace_id)
        cur.execute(
            "SELECT id,user_id,name,adapter,config,is_default,auto_push,enabled,"
            "last_used_at,last_status,success_count,failure_count "
            "FROM erp_endpoints WHERE id = %s AND user_id = %s "
            "AND binding_generation = 0 AND enabled = TRUE FOR SHARE",
            (endpoint_id, actor_id),
        )
        endpoint = cur.fetchone()
        adapter = str((endpoint or {}).get("adapter") or "").lower()
        if not endpoint or adapter not in {"mrerp", "express"}:
            raise HTTPException(409, detail="erp.endpoint_not_ready")
        cur.execute(
            "SELECT id FROM workspace_clients WHERE id = %s AND tenant_id = %s "
            "AND erp_endpoint_id = %s AND is_active = TRUE FOR SHARE",
            (workspace_id, tenant_id, endpoint_id),
        )
        if not cur.fetchone():
            raise HTTPException(409, detail="erp.workspace_binding_changed")

        for history_id in ids:
            history = _staged_history(cur, history_id, tenant_id, actor_id, workspace_id)
            prior = _prior_success(cur, endpoint_id, actor_id, history)
            if prior:
                status = "skipped_dup"
                request_body = {
                    "adapter": adapter,
                    "source": "cowork_line",
                    "skipped_reason": "already_success",
                    "prior_log_id": str(prior["id"]),
                }
                response_body = prior.get("response_body")
                error_msg = None
                lease_owner = None
            else:
                status = "retrying"
                request_body = {
                    "adapter": adapter,
                    "source": "cowork_line",
                    "reservation": "confirmed_pending_dispatch",
                }
                response_body = None
                error_msg = "COWORK_LEGACY_ERP_DISPATCH_RESERVED"
                lease_owner = LEGACY_RESERVATION_LEASE
            cur.execute(
                "INSERT INTO erp_push_logs "
                "(user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,status,"
                "http_status,request_body,response_body,error_msg,attempt,elapsed_ms,trigger,"
                "tenant_id,workspace_client_id,lease_owner,lease_expires_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,1,0,'manual',%s,%s,%s,"
                "CASE WHEN %s IS NULL THEN NULL ELSE clock_timestamp() + interval '10 minutes' END) "
                "RETURNING id::text AS id",
                (
                    actor_id,
                    endpoint_id,
                    history_id,
                    history.get("invoice_no"),
                    history.get("seller_name"),
                    history.get("total_amount"),
                    status,
                    200 if status == "skipped_dup" else 102,
                    json.dumps(request_body, ensure_ascii=False),
                    response_body,
                    error_msg,
                    tenant_id,
                    workspace_id,
                    lease_owner,
                    lease_owner,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("legacy ERP reservation insert returned no row")
            cur.execute(
                "UPDATE ocr_history SET staged = FALSE,last_push_status = %s,"
                "last_pushed_at = clock_timestamp(),updated_at = clock_timestamp() "
                "WHERE id = %s AND tenant_id = %s AND user_id = %s AND staged = TRUE",
                (status, history_id, tenant_id, actor_id),
            )
            if cur.rowcount != 1:
                raise RuntimeError("legacy ERP confirmation rowcount mismatch")
            intents.append(
                {
                    "history": history,
                    "history_id": history_id,
                    "log_id": str(row["id"]),
                    "status": status,
                    "accepted": status == "skipped_dup",
                    "dispatch": status == "retrying",
                }
            )
    return dict(endpoint), intents


def finalize_legacy_intent(
    identity: dict[str, Any],
    endpoint: dict[str, Any],
    intent: dict[str, Any],
    result: dict[str, Any],
) -> bool:
    """Finalize the reserved MR.ERP row; return False when the outcome is unknown."""
    tenant_id, actor_id = _identity(identity)
    endpoint_id = str(endpoint["id"])
    status = db.classify_push_status(bool(result.get("success")), result.get("error_msg"))
    request_body = result.get("request_body")
    response_body = result.get("response_body")
    if response_body is not None and not isinstance(response_body, str):
        response_body = json.dumps(response_body, ensure_ascii=False)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
            lock_endpoint_binding(cur, endpoint_id)
            if not lock_legacy_endpoint(cur, endpoint_id, actor_id):
                return False
            cur.execute(
                "UPDATE erp_push_logs SET status = %s,http_status = %s,request_body = %s::jsonb,"
                "response_body = %s,error_msg = %s,elapsed_ms = %s,lease_owner = NULL,"
                "lease_expires_at = NULL WHERE id = %s AND endpoint_id = %s AND user_id = %s "
                "AND status = 'retrying' AND lease_owner = %s",
                (
                    status,
                    result.get("http_status"),
                    json.dumps(request_body, ensure_ascii=False) if request_body else None,
                    response_body,
                    result.get("error_msg"),
                    int(result.get("elapsed_ms") or 0),
                    intent["log_id"],
                    endpoint_id,
                    actor_id,
                    LEGACY_RESERVATION_LEASE,
                ),
            )
            if cur.rowcount != 1:
                return False
            cur.execute(
                "UPDATE ocr_history SET last_push_status = %s,last_pushed_at = clock_timestamp() "
                "WHERE id = %s AND tenant_id = %s",
                (status, intent["history_id"], tenant_id),
            )
            if cur.rowcount != 1:
                raise RuntimeError("MR.ERP history mirror rowcount mismatch")
            counter = "success_count" if db.counts_as_endpoint_success(status) else "failure_count"
            cur.execute(
                f"UPDATE erp_endpoints SET {counter} = {counter} + 1,last_used_at = NOW(),"
                "last_status = %s WHERE id = %s AND binding_generation = 0",
                ("success" if counter == "success_count" else "failed", endpoint_id),
            )
        if status == "failed" and not db.is_user_data_error(result.get("error_msg")):
            delay = db.get_erp_retry_delay_sec(0)
            if delay is not None:
                db.schedule_log_retry(intent["log_id"], delay)
        intent.update(
            {
                "status": status,
                "accepted": status in {"success", "pending", "skipped_dup"},
                "error_msg": result.get("error_msg"),
            }
        )
        return True
    except Exception:
        return False


__all__ = [
    "confirmed_batch_result",
    "finalize_legacy_intent",
    "reserve_legacy_batch",
    "reserve_managed_batch",
]

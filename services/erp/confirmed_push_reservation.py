"""Durable reservation for one catalog-selected legacy ERP push."""

from __future__ import annotations

import copy
import json
from typing import Any

from fastapi import HTTPException

from core import db
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp.line_target_choice import endpoint_with_account_choice
from services.erp.selected_account import require_catalog_evidence, resolve_account_choice

LEASE_OWNER = "confirmed:legacy"
_LEASE_SECONDS = 600
_RESERVED_ERROR = "ERP_CONFIRMED_PUSH_RESERVED"
_UNKNOWN_ERROR = "ERP_CONFIRMED_PUSH_RESULT_UNKNOWN"
_ADAPTERS = frozenset({"mrerp", "express"})


def _workspace_id(value: object) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _endpoint_row(cur, *, user: dict[str, Any], endpoint_id: str, assigned: bool):
    tenant_id = str(user.get("tenant_id") or "").strip()
    actor_id = str(user.get("id") or "").strip()
    columns = (
        "ep.id,ep.user_id,ep.name,ep.adapter,ep.config,ep.is_default,ep.auto_push,"
        "ep.enabled,ep.last_used_at,ep.last_status,ep.success_count,ep.failure_count,"
        "ep.created_at,ep.updated_at,ep.tenant_id,ep.workspace_client_id,"
        "ep.shared_scope,ep.binding_generation,ep.bound_account_set,"
        "ep.bound_profile_key,ep.live_account_set,ep.live_profile_key,"
        "ep.agent_last_seen_at,ep.agent_version,ep.revoked_at"
    )
    if assigned:
        cur.execute(
            f"SELECT {columns} FROM erp_team_members etm "
            "JOIN memberships membership ON membership.user_id = etm.user_id "
            "AND membership.tenant_id = etm.tenant_id "
            "JOIN users actor ON actor.id = etm.user_id AND actor.tenant_id = etm.tenant_id "
            "JOIN users owner_user ON owner_user.id = etm.invited_by "
            "AND owner_user.tenant_id = etm.tenant_id "
            "JOIN erp_endpoints ep ON ep.id = etm.erp_endpoint_id "
            "WHERE etm.tenant_id = %s AND etm.user_id = %s AND ep.id = %s "
            "AND etm.is_active = TRUE AND membership.status = 'active' "
            "AND actor.is_active = TRUE AND owner_user.is_active = TRUE "
            "AND ep.user_id = etm.invited_by AND ep.adapter = etm.erp_system "
            "AND ep.binding_generation = 0 AND ep.enabled = TRUE "
            "FOR SHARE OF ep,etm,membership,actor,owner_user",
            (tenant_id, actor_id, endpoint_id),
        )
    else:
        cur.execute(
            f"SELECT {columns} FROM erp_endpoints ep "
            "JOIN users owner_user ON owner_user.id = ep.user_id "
            "WHERE ep.id = %s AND ep.user_id = %s AND owner_user.tenant_id = %s "
            "AND owner_user.is_active = TRUE AND ep.binding_generation = 0 "
            "AND ep.enabled = TRUE FOR SHARE OF ep,owner_user",
            (endpoint_id, actor_id, tenant_id),
        )
    row = cur.fetchone()
    endpoint = dict(row) if row else {}
    if str(endpoint.get("adapter") or "").strip().lower() not in _ADAPTERS:
        raise HTTPException(409, detail="erp.endpoint_changed")
    return endpoint


def _selected_account(endpoint: dict[str, Any]) -> str:
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    if str(endpoint.get("adapter") or "").strip().lower() == "mrerp":
        return f"{str(config.get('comidyear') or '6').strip()}:{str(config.get('seldb') or '1').strip()}"
    return str(config.get("account_set") or config.get("account_dir") or "").strip()


def _account_filter() -> str:
    return (
        "lower(btrim(COALESCE(request_body->>'account_set', "
        "request_body->'meta'->>'account_set', "
        "request_body->'target_intent'->>'account_set', ''))) = %s"
    )


def _find_log(
    cur,
    *,
    tenant_id: str,
    endpoint_id: str,
    history_id: str,
    account_set: str,
    predicate: str,
) -> dict[str, Any] | None:
    cur.execute(
        "SELECT id::text AS id,status,http_status,response_body,error_msg,next_retry_at "
        "FROM erp_push_logs WHERE tenant_id = %s AND endpoint_id = %s "
        f"AND history_id = %s AND {_account_filter()} AND {predicate} "
        "ORDER BY created_at DESC,id DESC LIMIT 1",
        (tenant_id, endpoint_id, history_id, account_set.casefold()),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _response(
    row: dict[str, Any], endpoint: dict[str, Any], *, ok: bool, reused: bool
) -> dict[str, Any]:
    stored_status = str(row.get("status") or "manual")
    retry_scheduled = stored_status == "failed" and row.get("next_retry_at") is not None
    status = "retrying" if retry_scheduled else stored_status
    return {
        "ok": ok,
        "log_id": str(row["id"]),
        "status": status,
        "http_status": row.get("http_status"),
        "error_msg": row.get("error_msg"),
        "endpoint_name": endpoint.get("name"),
        "queued": status in {"pending", "retrying"},
        "retry_scheduled": retry_scheduled,
        "reused": reused,
    }


def _insert_skipped(
    cur,
    *,
    user: dict[str, Any],
    endpoint: dict[str, Any],
    history: dict[str, Any],
    account_set: str,
    source: str,
    prior: dict[str, Any],
    workspace_client_id: int | None,
) -> dict[str, Any]:
    request_body = {
        "adapter": str(endpoint.get("adapter") or "").lower(),
        "source": source,
        "account_set": account_set,
        "skipped_reason": "already_success",
        "prior_log_id": str(prior["id"]),
    }
    cur.execute(
        "INSERT INTO erp_push_logs "
        "(user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,status,"
        "http_status,request_body,response_body,error_msg,attempt,elapsed_ms,trigger,"
        "tenant_id,workspace_client_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,'skipped_dup',200,%s::jsonb,%s,NULL,1,0,'manual',%s,%s) "
        "RETURNING id::text AS id,status,http_status,response_body,error_msg",
        (
            str(user["id"]),
            str(endpoint["id"]),
            str(history["id"]),
            history.get("invoice_no"),
            history.get("seller_name"),
            history.get("total_amount"),
            json.dumps(request_body, ensure_ascii=False),
            prior.get("response_body"),
            str(user["tenant_id"]),
            workspace_client_id,
        ),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("legacy ERP duplicate reservation insert returned no row")
    result = _response(dict(row), endpoint, ok=True, reused=False)
    result.update(skipped_dup=True, prior_log_id=str(prior["id"]))
    return result


def reserve_catalog_selected_push(
    *,
    user: dict[str, Any],
    endpoint_id: str,
    history: dict[str, Any],
    assigned: bool,
    account_set_key: str | None,
    account_config: dict[str, Any] | None,
    refresh_request_id: str | None,
    projection_revision: int | None,
    source: str,
    workspace_client_id: int | None,
    posting_kind: str | None,
) -> dict[str, Any]:
    """Validate and persist one target choice while the endpoint is locked."""
    tenant_id = str(user.get("tenant_id") or "").strip()
    actor_id = str(user.get("id") or "").strip()
    if not tenant_id or not actor_id or not endpoint_id or not history.get("id"):
        raise HTTPException(404, detail="erp.endpoint_not_found")
    workspace_id = _workspace_id(workspace_client_id or history.get("workspace_client_id"))

    with db.get_cursor(commit=True) as cur:
        lock_endpoint_binding(cur, endpoint_id)
        endpoint = _endpoint_row(cur, user=user, endpoint_id=endpoint_id, assigned=assigned)
        proof = require_catalog_evidence(
            endpoint,
            tenant_id=tenant_id,
            user_id=actor_id,
            account_set_key=account_set_key,
            trusted_account_config=account_config,
            request_id=refresh_request_id,
            revision=projection_revision,
            cur=cur,
        )
        choice = resolve_account_choice(
            endpoint,
            tenant_id=tenant_id,
            user_id=actor_id,
            account_set_key=account_set_key,
            trusted_account_config=account_config,
            cur=cur,
        )
        endpoint = endpoint_with_account_choice(endpoint, choice)
        account_set = _selected_account(endpoint)
        if not account_set:
            raise HTTPException(409, detail="erp.account_set_unavailable")

        cur.execute(
            "UPDATE erp_push_logs SET status = 'manual',http_status = NULL,error_msg = %s,"
            "next_retry_at = NULL,lease_owner = NULL,lease_expires_at = NULL "
            "WHERE tenant_id = %s AND endpoint_id = %s AND status = 'retrying' "
            "AND lease_owner = %s AND lease_expires_at <= clock_timestamp()",
            (_UNKNOWN_ERROR, tenant_id, endpoint_id, LEASE_OWNER),
        )
        query = {
            "cur": cur,
            "tenant_id": tenant_id,
            "endpoint_id": endpoint_id,
            "history_id": str(history["id"]),
            "account_set": account_set,
        }
        prior = _find_log(**query, predicate="status IN ('success','skipped_dup')")
        if prior:
            return {
                "dispatch": False,
                "response": _insert_skipped(
                    cur,
                    user=user,
                    endpoint=endpoint,
                    history=history,
                    account_set=account_set,
                    source=source,
                    prior=prior,
                    workspace_client_id=workspace_id,
                ),
            }
        active = _find_log(
            **query,
            predicate=(
                "(status IN ('pending','retrying') OR lease_owner IS NOT NULL "
                "OR (status = 'failed' AND next_retry_at IS NOT NULL))"
            ),
        )
        if active:
            return {
                "dispatch": False,
                "response": _response(active, endpoint, ok=True, reused=True),
            }
        unknown = _find_log(
            **query,
            predicate=f"status = 'manual' AND error_msg = '{_UNKNOWN_ERROR}'",
        )
        if unknown:
            return {
                "dispatch": False,
                "response": _response(unknown, endpoint, ok=False, reused=True),
            }

        target_intent = {
            "endpoint_id": endpoint_id,
            "binding_generation": 0,
            "account_set": account_set,
            "root_key": (proof or {}).get("root_key"),
            "catalog_refresh_request_id": (proof or {}).get("request_id"),
            "catalog_projection_revision": (proof or {}).get("revision"),
        }
        request_body = {
            "adapter": str(endpoint.get("adapter") or "").lower(),
            "source": source,
            "account_set": account_set,
            "posting_kind": posting_kind,
            "reservation": "confirmed_pending_dispatch",
            "target_intent": target_intent,
        }
        cur.execute(
            "INSERT INTO erp_push_logs "
            "(user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,status,"
            "http_status,request_body,response_body,error_msg,attempt,elapsed_ms,trigger,"
            "tenant_id,workspace_client_id,lease_owner,lease_expires_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,'retrying',102,%s::jsonb,NULL,%s,1,0,'manual',"
            "%s,%s,%s,clock_timestamp() + (%s * interval '1 second')) "
            "RETURNING id::text AS id",
            (
                actor_id,
                endpoint_id,
                str(history["id"]),
                history.get("invoice_no"),
                history.get("seller_name"),
                history.get("total_amount"),
                json.dumps(request_body, ensure_ascii=False),
                _RESERVED_ERROR,
                tenant_id,
                workspace_id,
                LEASE_OWNER,
                _LEASE_SECONDS,
            ),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("legacy ERP push reservation insert returned no row")
        return {
            "dispatch": True,
            "endpoint": copy.deepcopy(endpoint),
            "history": copy.deepcopy(history),
            "log_id": str(row["id"]),
            "history_id": str(history["id"]),
            "user_id": actor_id,
            "tenant_id": tenant_id,
            "workspace_client_id": workspace_id,
            "account_set": account_set,
            "source": source,
            "target_intent": target_intent,
        }


def _final_request_body(reservation: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    raw = result.get("request_body")
    body = dict(raw) if isinstance(raw, dict) else {}
    body["source"] = reservation["source"]
    body["account_set"] = reservation["account_set"]
    body["target_intent"] = copy.deepcopy(reservation["target_intent"])
    return body


def finalize_reserved_push(
    reservation: dict[str, Any],
    result: dict[str, Any],
    *,
    retry_delay_sec: int | None = None,
) -> str | None:
    """CAS the outbound result onto its reservation; return the final status."""
    status = db.classify_push_status(bool(result.get("success")), result.get("error_msg"))
    retry_delay = (
        max(0, int(retry_delay_sec)) if status == "failed" and retry_delay_sec is not None else None
    )
    response_body = result.get("response_body")
    if response_body is not None and not isinstance(response_body, str):
        response_body = json.dumps(response_body, ensure_ascii=False)
    request_body = _final_request_body(reservation, result)
    try:
        with db.get_cursor_rls(
            tenant_id=reservation["tenant_id"],
            user_id=reservation["user_id"],
            workspace_client_id=reservation.get("workspace_client_id"),
            commit=True,
        ) as cur:
            cur.execute(
                "UPDATE erp_push_logs SET status = %s,http_status = %s,request_body = %s::jsonb,"
                "response_body = %s,error_msg = %s,elapsed_ms = %s,lease_owner = NULL,"
                "lease_expires_at = NULL,next_retry_at = CASE WHEN %s::integer IS NULL THEN NULL "
                "ELSE clock_timestamp() + (%s::integer * interval '1 second') END "
                "WHERE id = %s AND user_id = %s AND history_id = %s "
                "AND status = 'retrying' AND lease_owner = %s",
                (
                    status,
                    result.get("http_status"),
                    json.dumps(request_body, ensure_ascii=False),
                    response_body,
                    result.get("error_msg"),
                    int(result.get("elapsed_ms") or 0),
                    retry_delay,
                    retry_delay,
                    reservation["log_id"],
                    reservation["user_id"],
                    reservation["history_id"],
                    LEASE_OWNER,
                ),
            )
            return status if cur.rowcount == 1 else None
    except Exception:
        return None


def _unknown_response_body(result: dict[str, Any] | None) -> str | None:
    if result is None:
        return None
    return json.dumps(
        {
            "outcome": "unknown",
            "adapter_error": result.get("error_msg"),
            "adapter_response": result.get("response_body"),
        },
        ensure_ascii=False,
        default=str,
    )


def mark_reserved_push_unknown(
    reservation: dict[str, Any], result: dict[str, Any] | None = None
) -> bool:
    """Keep one ambiguous external outcome manual and never replay it automatically."""
    request_body = _final_request_body(reservation, result) if result is not None else None
    try:
        with db.get_cursor_rls(
            tenant_id=reservation["tenant_id"],
            user_id=reservation["user_id"],
            workspace_client_id=reservation.get("workspace_client_id"),
            commit=True,
        ) as cur:
            cur.execute(
                "UPDATE erp_push_logs SET status = 'manual',http_status = %s,"
                "request_body = COALESCE(%s::jsonb,request_body),"
                "response_body = COALESCE(%s,response_body),error_msg = %s,"
                "next_retry_at = NULL,lease_owner = NULL,lease_expires_at = NULL "
                "WHERE id = %s AND user_id = %s AND history_id = %s "
                "AND status = 'retrying' AND lease_owner = %s",
                (
                    result.get("http_status") if result is not None else None,
                    json.dumps(request_body, ensure_ascii=False) if request_body else None,
                    _unknown_response_body(result),
                    _UNKNOWN_ERROR,
                    reservation["log_id"],
                    reservation["user_id"],
                    reservation["history_id"],
                    LEASE_OWNER,
                ),
            )
            return cur.rowcount == 1
    except Exception:
        return False


def read_reserved_push_result(reservation: dict[str, Any]) -> dict[str, Any] | None:
    """Read back a reservation after an uncertain finalize commit."""
    try:
        with db.get_cursor_rls(
            tenant_id=reservation["tenant_id"],
            user_id=reservation["user_id"],
            workspace_client_id=reservation.get("workspace_client_id"),
            commit=False,
        ) as cur:
            cur.execute(
                "SELECT status,http_status,error_msg,next_retry_at,lease_owner "
                "FROM erp_push_logs WHERE id = %s AND tenant_id = %s "
                "AND endpoint_id = %s AND history_id = %s",
                (
                    reservation["log_id"],
                    reservation["tenant_id"],
                    reservation["endpoint"]["id"],
                    reservation["history_id"],
                ),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


__all__ = [
    "finalize_reserved_push",
    "mark_reserved_push_unknown",
    "read_reserved_push_result",
    "reserve_catalog_selected_push",
]

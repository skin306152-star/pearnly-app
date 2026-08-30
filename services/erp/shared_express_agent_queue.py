"""Managed Express queue over the Companion 1.1.64 lease/ACK wire."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import struct
import uuid
from typing import Any, Dict, List, Optional

from core import db
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp.shared_express_agent_auth import (
    parse_managed_agent_token,
    stored_token_matches,
)
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for

_LEASE_SECONDS = 120
_MAX_ATTEMPTS = 3
_AGENT_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_HANDLE_PREFIX = "m1_"
_HANDLE_VERSION = 1
_HANDLE_SIGNATURE_BYTES = 16
_CONFIRMED = (
    "lower(coalesce(request_body->>'duplicate_confirmed', 'false')) "
    "NOT IN ('false', '0', '', 'null', 'no', 'off')"
)


class ManagedAgentQueueError(Exception):
    def __init__(self, code: str, status: int):
        super().__init__(code)
        self.code = code
        self.status = status


def _agent_id(value: object) -> str:
    owner = value.strip() if isinstance(value, str) else ""
    if not _AGENT_ID.fullmatch(owner):
        raise ManagedAgentQueueError("erp.agent_id_invalid", 422)
    return owner


def _token_key(token_digest: str) -> bytes:
    try:
        key = bytes.fromhex(token_digest)
    except (TypeError, ValueError) as exc:
        raise ManagedAgentQueueError("erp.agent_unauthorized", 401) from exc
    if len(key) != hashlib.sha256().digest_size:
        raise ManagedAgentQueueError("erp.agent_unauthorized", 401)
    return key


def _encode_handle(endpoint_id: str, log_id: object, attempt: int, token_digest: str) -> str:
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    body = bytes([_HANDLE_VERSION]) + uuid.UUID(str(log_id)).bytes + struct.pack(">Q", attempt)
    subject = uuid.UUID(str(endpoint_id)).bytes + body
    signature = hmac.new(_token_key(token_digest), subject, hashlib.sha256).digest()[
        :_HANDLE_SIGNATURE_BYTES
    ]
    return _HANDLE_PREFIX + base64.urlsafe_b64encode(body + signature).decode("ascii").rstrip("=")


def _decode_handle(
    handle: object, endpoint_id: str, token_digest: str
) -> Optional[tuple[str, int]]:
    if not isinstance(handle, str) or not handle.startswith(_HANDLE_PREFIX) or len(handle) > 128:
        return None
    encoded = handle[len(_HANDLE_PREFIX) :]
    try:
        raw = base64.b64decode(encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
    except (ValueError, TypeError):
        return None
    body_length = 1 + 16 + 8
    if len(raw) != body_length + _HANDLE_SIGNATURE_BYTES or raw[0] != _HANDLE_VERSION:
        return None
    body, signature = raw[:body_length], raw[body_length:]
    try:
        endpoint_bytes = uuid.UUID(str(endpoint_id)).bytes
        expected = hmac.new(
            _token_key(token_digest), endpoint_bytes + body, hashlib.sha256
        ).digest()[:_HANDLE_SIGNATURE_BYTES]
    except (ValueError, ManagedAgentQueueError):
        return None
    if not hmac.compare_digest(signature, expected):
        return None
    return str(uuid.UUID(bytes=body[1:17])), struct.unpack(">Q", body[17:25])[0]


def _authenticate_managed(cur, token: str) -> tuple[Dict[str, Any], str]:
    parsed = parse_managed_agent_token(token)
    if parsed is None:
        raise ManagedAgentQueueError("erp.agent_unauthorized", 401)
    endpoint_id = parsed.endpoint_id
    lock_endpoint_binding(cur, endpoint_id)
    cur.execute(
        """
        SELECT endpoint.id, endpoint.tenant_id, endpoint.workspace_client_id,
               endpoint.enabled, endpoint.shared_scope, endpoint.binding_generation,
               endpoint.bound_account_set, endpoint.bound_profile_key,
               endpoint.live_account_set, endpoint.live_profile_key,
               endpoint.agent_last_seen_at,
               endpoint.config ->> 'agent_token_hash' AS token_hash,
               clock_timestamp() AS db_now
        FROM erp_endpoints endpoint
        JOIN tenants tenant
          ON tenant.id = endpoint.tenant_id AND tenant.status IN ('active', 'warning')
        JOIN workspace_clients workspace
          ON workspace.id = endpoint.workspace_client_id
         AND workspace.tenant_id = endpoint.tenant_id AND workspace.is_active = TRUE
        WHERE endpoint.id = %s AND endpoint.adapter = 'express'
          AND endpoint.binding_generation > 0 AND endpoint.revoked_at IS NULL
        FOR UPDATE OF endpoint
        """,
        (endpoint_id,),
    )
    row = cur.fetchone()
    endpoint = dict(row) if row else None
    if not endpoint or not stored_token_matches(
        str(endpoint.get("token_hash") or ""), parsed.token_digest
    ):
        raise ManagedAgentQueueError("erp.agent_unauthorized", 401)
    if not endpoint.get("enabled"):
        raise ManagedAgentQueueError("erp.endpoint_disabled", 403)
    if (
        not endpoint.get("shared_scope")
        or endpoint.get("tenant_id") is None
        or endpoint.get("workspace_client_id") is None
    ):
        raise ManagedAgentQueueError("erp.agent_unauthorized", 401)
    bound = (endpoint.get("bound_account_set"), endpoint.get("bound_profile_key"))
    live = (endpoint.get("live_account_set"), endpoint.get("live_profile_key"))
    if None in bound or bound != live:
        raise ManagedAgentQueueError("erp.agent_profile_not_ready", 409)
    seen, now = endpoint.get("agent_last_seen_at"), endpoint.get("db_now")
    if seen is None or now is None:
        raise ManagedAgentQueueError("erp.agent_offline", 409)
    age = (now - seen).total_seconds()
    if age < -5 or age >= 180:
        raise ManagedAgentQueueError("erp.agent_offline", 409)
    account_set = str(endpoint.get("bound_account_set") or "").strip().casefold()
    if not account_set:
        raise ManagedAgentQueueError("erp.agent_profile_not_ready", 409)
    endpoint["account_set"] = account_set
    return endpoint, parsed.token_digest


def _payload_generation(payload: object) -> Optional[int]:
    if not isinstance(payload, dict):
        return None
    meta = payload.get("meta")
    candidates = (
        meta.get("managed_generation") if isinstance(meta, dict) else None,
        payload.get("managed_generation"),
    )
    for value in candidates:
        try:
            generation = int(value)
        except (TypeError, ValueError):
            continue
        if generation > 0:
            return generation
    return None


def _payload_account_set(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    meta = payload.get("meta")
    value = payload.get("account_set")
    if value is None and isinstance(meta, dict):
        value = meta.get("account_set")
    return str(value or "").strip().casefold()


def lease_managed(token: str, agent_id: object, max_n: int) -> Dict[str, Any]:
    owner = _agent_id(agent_id)
    limit = max(1, min(int(max_n or 1), 50))
    try:
        with db.get_cursor(commit=True) as cur:
            endpoint, token_digest = _authenticate_managed(cur, token)
            if not erp_shared_express_endpoint_enabled_for(endpoint.get("tenant_id")):
                return {"ok": True, "lease_seconds": _LEASE_SECONDS, "jobs": []}
            endpoint_id = str(endpoint["id"])
            generation = int(endpoint["binding_generation"])
            account_set = endpoint["account_set"]
            cur.execute(
                f"""
                WITH due AS (
                    SELECT id
                    FROM erp_push_logs
                    WHERE endpoint_id = %s AND status = 'pending'
                      AND COALESCE(
                            request_body->'meta'->>'managed_generation',
                            request_body->>'managed_generation'
                          ) = %s
                      AND lower(btrim(COALESCE(
                            request_body->>'account_set',
                            request_body->'meta'->>'account_set', ''
                          ))) = %s
                      AND (
                            lease_owner IS NULL
                            OR (NOT ({_CONFIRMED})
                                AND (lease_expires_at IS NULL
                                     OR lease_expires_at < clock_timestamp()))
                          )
                    ORDER BY created_at, id
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE erp_push_logs log
                SET attempt = log.attempt + CASE WHEN log.lease_owner IS NULL THEN 0 ELSE 1 END,
                    lease_owner = %s,
                    lease_expires_at = clock_timestamp() + (%s * INTERVAL '1 second')
                FROM due
                WHERE log.id = due.id
                RETURNING log.id, log.history_id, log.invoice_no, log.request_body,
                          log.attempt, log.lease_expires_at
                """,
                (endpoint_id, str(generation), account_set, limit, owner, _LEASE_SECONDS),
            )
            rows = [dict(row) for row in (cur.fetchall() or [])]
            jobs: List[Dict[str, Any]] = []
            for row in rows:
                payload = row.get("request_body") or {}
                if (
                    _payload_generation(payload) != generation
                    or _payload_account_set(payload) != account_set
                ):
                    raise RuntimeError("managed lease payload contract changed after selection")
                jobs.append(
                    {
                        "log_id": _encode_handle(
                            endpoint_id, row["id"], int(row.get("attempt") or 0), token_digest
                        ),
                        "history_id": str(row.get("history_id") or ""),
                        "invoice_no": row.get("invoice_no"),
                        "payload": payload,
                    }
                )
            return {"ok": True, "lease_seconds": _LEASE_SECONDS, "jobs": jobs}
    except ManagedAgentQueueError:
        raise
    except Exception as exc:
        raise ManagedAgentQueueError("erp.shared_endpoint_unavailable", 503) from exc


def _response_body(
    *, ok: bool, stage: str, express_docnum: object, line_modes: object, meta: object
) -> str:
    from services.erp.express_push import common

    clean_meta = common.sanitize_push_meta(meta)
    clean_meta.setdefault("stage", stage)
    body: Dict[str, Any] = {"ok": ok, "express_docnum": express_docnum, "meta": clean_meta}
    if isinstance(line_modes, list) and line_modes:
        body["line_modes"] = line_modes
    return json.dumps(body, ensure_ascii=False)


def _mirror_history(cur, history_id: object, status: str) -> None:
    if history_id is None:
        return
    cur.execute(
        "UPDATE ocr_history SET last_push_status = %s, last_pushed_at = clock_timestamp() "
        "WHERE id = %s",
        (status, history_id),
    )
    if cur.rowcount != 1:
        raise RuntimeError("managed ACK history mirror missed")


def ack_managed(
    token: str,
    handle: object,
    agent_id: object,
    *,
    success: bool,
    express_docnum: object = None,
    error: object = None,
    line_modes: object = None,
    outcome: object = None,
    meta: object = None,
) -> Dict[str, Any]:
    from services.erp.express_push import common

    owner = _agent_id(agent_id)
    stage = (
        outcome
        if outcome in common.ACK_OUTCOMES
        else (common.STAGE_SUCCESS if success else common.STAGE_FAILED)
    )
    try:
        with db.get_cursor(commit=True) as cur:
            endpoint, token_digest = _authenticate_managed(cur, token)
            endpoint_id = str(endpoint["id"])
            generation = int(endpoint["binding_generation"])
            decoded = _decode_handle(handle, endpoint_id, token_digest)
            if decoded is None:
                return {"ok": False, "stale": True}
            log_id, attempt = decoded
            cur.execute(
                """
                SELECT id, history_id, attempt, request_body
                FROM erp_push_logs
                WHERE id = %s AND endpoint_id = %s AND status = 'pending'
                  AND lease_owner = %s AND attempt = %s
                  AND COALESCE(
                        request_body->'meta'->>'managed_generation',
                        request_body->>'managed_generation'
                      ) = %s
                FOR UPDATE
                """,
                (log_id, endpoint_id, owner, attempt, str(generation)),
            )
            row = cur.fetchone()
            log = dict(row) if row else None
            if not log or _payload_generation(log.get("request_body")) != generation:
                return {"ok": False, "stale": True}

            if stage == common.STAGE_SUCCESS:
                body = _response_body(
                    ok=True,
                    stage=stage,
                    express_docnum=express_docnum,
                    line_modes=line_modes,
                    meta=meta,
                )
                values = ("success", 200, body, None, attempt, log_id, endpoint_id, owner, attempt)
                status = "success"
            elif stage == common.STAGE_WAITING_LOCK:
                body = _response_body(
                    ok=False, stage=stage, express_docnum=None, line_modes=None, meta=meta
                )
                values = (
                    "pending",
                    None,
                    body,
                    None,
                    attempt + 1,
                    log_id,
                    endpoint_id,
                    owner,
                    attempt,
                )
                status = "pending"
            elif stage in (common.STAGE_NEEDS_MAPPING, common.STAGE_NEEDS_REVIEW):
                body = _response_body(
                    ok=False, stage=stage, express_docnum=None, line_modes=None, meta=meta
                )
                values = (
                    "manual",
                    None,
                    body,
                    str(error or stage)[:500],
                    attempt,
                    log_id,
                    endpoint_id,
                    owner,
                    attempt,
                )
                status = "manual"
            else:
                body = _response_body(
                    ok=False, stage=stage, express_docnum=None, line_modes=None, meta=meta
                )
                status = "manual" if attempt >= _MAX_ATTEMPTS else "pending"
                values = (
                    status,
                    None,
                    body,
                    str(error or "agent_failed")[:500],
                    attempt + 1,
                    log_id,
                    endpoint_id,
                    owner,
                    attempt,
                )
            cur.execute(
                """
                UPDATE erp_push_logs
                SET status = %s, http_status = %s, response_body = %s, error_msg = %s,
                    attempt = %s, lease_owner = NULL, lease_expires_at = NULL
                WHERE id = %s AND endpoint_id = %s AND status = 'pending'
                  AND lease_owner = %s AND attempt = %s
                """,
                values,
            )
            if cur.rowcount != 1:
                return {"ok": False, "stale": True}
            if status in ("success", "manual"):
                _mirror_history(cur, log.get("history_id"), status)
            if status == "success":
                return {"ok": True, "status": status, "express_docnum": express_docnum}
            result: Dict[str, Any] = {"ok": True, "status": status, "stage": stage}
            if status == "pending":
                result["retry"] = True
                result["attempt"] = attempt + 1
            return result
    except ManagedAgentQueueError:
        raise
    except Exception as exc:
        raise ManagedAgentQueueError("erp.shared_endpoint_unavailable", 503) from exc


__all__ = ["ManagedAgentQueueError", "ack_managed", "lease_managed"]

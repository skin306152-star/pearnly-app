"""Binding-scoped conversation reads and atomic state transitions.

Session rows are keyed by ``(tenant_id, channel_key, line_user_id)``: the same person can hold a
binding on a different OA under the same tenant, and their conversations must never merge. The OA
is resolved from the binding in scope unless the caller passes one explicitly.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _channel(channel_key: Optional[str]) -> str:
    from services.line_dms import binding_guard
    from services.line_platform import channels

    if channel_key is None:
        return binding_guard.current_channel()
    key = channels.resolve(channel_key)
    if key is None:
        # Unknown non-empty key must never touch the legacy OA's rows (callers fail closed).
        raise ValueError("dms_channel.unknown_channel")
    return key


def set_session(
    tenant_id,
    line_user_id: str,
    state: str,
    payload=None,
    ttl_minutes: Optional[int] = None,
    channel_key: Optional[str] = None,
):
    """存/覆盖会话态(upsert)。ttl_minutes 缺省按 state 查表(见 _STATE_TTL_MINUTES)。

    哨兵用 None 不用 0:0 是「立刻过期」这个合法值(测试与强制失效都在用)。
    """
    from core import db
    from services.line_dms.store import _with_heal, state_ttl_minutes
    from services.line_dms import binding_state

    ttl = state_ttl_minutes(state) if ttl_minutes is None else int(ttl_minutes)
    key = _channel(channel_key)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            binding_state.lock_scope(cur, line_user_id, key)
            cur.execute(
                "INSERT INTO dms_line_sessions "
                "(tenant_id, channel_key, line_user_id, state, payload, expires_at) "
                "VALUES (%s, %s, %s, %s, %s::jsonb, now() + make_interval(mins => %s)) "
                "ON CONFLICT (tenant_id, channel_key, line_user_id) DO UPDATE SET "
                "  state = EXCLUDED.state, payload = EXCLUDED.payload, "
                "  expires_at = EXCLUDED.expires_at",
                (
                    str(tenant_id),
                    key,
                    str(line_user_id),
                    state,
                    json.dumps(payload or {}, ensure_ascii=False),
                    ttl,
                ),
            )

    try:
        _with_heal(_run)
    except Exception as e:
        logger.warning(f"[line_dms] set_session failed: {e}")


def get_session(tenant_id, line_user_id: str, channel_key: Optional[str] = None) -> Optional[dict]:
    """读未过期会话态(过期视为无)。返回 {state, payload} 或 None。"""
    from core import db
    from services.line_dms.store import _with_heal
    from services.line_dms import binding_state

    key = _channel(channel_key)

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            binding_state.lock_scope(cur, line_user_id, key)
            cur.execute(
                "SELECT state, payload FROM dms_line_sessions "
                "WHERE tenant_id = %s AND channel_key = %s AND line_user_id = %s "
                "AND expires_at > now()",
                (str(tenant_id), key, str(line_user_id)),
            )
            return cur.fetchone()

    try:
        row = _with_heal(_run)
    except Exception:
        logger.warning("[line_dms] get_session failed; treat as none", exc_info=True)
        return None
    if not row:
        return None
    payload = row.get("payload")
    return {
        "state": row.get("state"),
        "payload": payload if isinstance(payload, dict) else json.loads(payload or "{}"),
    }


def clear_session(tenant_id, line_user_id: str, channel_key: Optional[str] = None) -> None:
    """删会话态(会话结束/取消)。"""
    from core import db
    from services.line_dms.store import _with_heal
    from services.line_dms import binding_state

    key = _channel(channel_key)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            binding_state.lock_scope(cur, line_user_id, key)
            cur.execute(
                "DELETE FROM dms_line_sessions "
                "WHERE tenant_id = %s AND channel_key = %s AND line_user_id = %s",
                (str(tenant_id), key, str(line_user_id)),
            )

    try:
        _with_heal(_run)
    except Exception as e:
        logger.warning(f"[line_dms] clear_session failed: {e}")


def consume_nonce(
    tenant_id, line_user_id: str, expect_state: str, nonce: str, channel_key: Optional[str] = None
) -> Optional[dict]:
    """One UPDATE claims the nonce; concurrent confirmations cannot both execute."""
    from core import db
    from services.line_dms.store import _dal
    from services.line_dms import binding_state

    if not nonce:
        return None
    key = _channel(channel_key)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            binding_state.lock_scope(cur, line_user_id, key)
            cur.execute(
                "UPDATE dms_line_sessions SET payload = payload || '{\"nonce\":null}'::jsonb "
                "WHERE tenant_id=%s AND channel_key=%s AND line_user_id=%s AND state=%s "
                "AND expires_at>now() AND payload->>'nonce'=%s RETURNING payload",
                (str(tenant_id), key, line_user_id, expect_state, nonce),
            )
            row = cur.fetchone()
            return {**dict(row["payload"]), "nonce": nonce} if row else None

    return _dal("consume_nonce", None)(_run)


def replace_review_payload(
    tenant_id,
    line_user_id: str,
    expected_nonce: str,
    payload: dict,
    channel_key: Optional[str] = None,
) -> bool:
    """Replace one booking review draft and rotate its nonce in one guarded write."""
    from core import db
    from services.line_dms.store import _with_heal, state_ttl_minutes
    from services.line_dms import binding_state

    if not expected_nonce or not payload.get("nonce"):
        return False
    key = _channel(channel_key)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            binding_state.lock_scope(cur, line_user_id, key)
            cur.execute(
                "UPDATE dms_line_sessions SET payload = %s::jsonb, "
                "expires_at = now() + make_interval(mins => %s) "
                "WHERE tenant_id = %s AND channel_key = %s AND line_user_id = %s "
                "AND state = 'booking_review' AND expires_at > now() "
                "AND payload->>'nonce' = %s",
                (
                    json.dumps(payload, ensure_ascii=False),
                    state_ttl_minutes("booking_review"),
                    str(tenant_id),
                    key,
                    str(line_user_id),
                    expected_nonce,
                ),
            )
            return cur.rowcount == 1

    try:
        return bool(_with_heal(_run))
    except Exception:
        logger.warning("[line_dms] replace review failed", exc_info=True)
        return False

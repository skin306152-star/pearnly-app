"""Short-lived, single-use authorization tokens for confirm-first actions."""

from __future__ import annotations

import secrets

DEFAULT_TTL_HOURS = 72

_TABLE = """
CREATE TABLE IF NOT EXISTS action_nonces (
    token text PRIMARY KEY,
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    user_id text NOT NULL DEFAULT '',
    action_ref text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz
)
"""

_INDEX = "CREATE INDEX IF NOT EXISTS ix_action_nonces_expires " "ON action_nonces (expires_at)"


def ensure_table() -> None:
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_INDEX)
        apply_tenant_rls(cur, "action_nonces")


def mint(
    cur,
    *,
    tenant_id,
    workspace_client_id,
    action_ref,
    user_id="",
    ttl_hours=DEFAULT_TTL_HOURS,
    ttl_minutes=None,
) -> str:
    if not action_ref:
        return ""
    unit, ttl = ("mins", ttl_minutes) if ttl_minutes is not None else ("hours", ttl_hours)
    token = secrets.token_urlsafe(18)
    cur.execute(
        "INSERT INTO action_nonces "
        "(token, tenant_id, workspace_client_id, user_id, action_ref, expires_at) "
        f"VALUES (%s, %s, %s, %s, %s, now() + make_interval({unit} => %s))",
        (
            token,
            tenant_id,
            workspace_client_id,
            str(user_id or ""),
            str(action_ref),
            int(ttl),
        ),
    )
    return token


def consume(cur, *, tenant_id, token, ref_kind=None) -> dict:
    if not token:
        return {"status": "missing"}
    kind_sql = " AND action_ref LIKE %s" if ref_kind else ""
    kind_params = (f'{{"kind": "{ref_kind}"%',) if ref_kind else ()
    cur.execute(
        "UPDATE action_nonces SET consumed_at = now() "
        "WHERE token = %s AND tenant_id = %s AND consumed_at IS NULL AND expires_at > now() "
        f"{kind_sql} RETURNING action_ref, workspace_client_id, user_id",
        (token, tenant_id) + kind_params,
    )
    row = cur.fetchone()
    if row:
        return {
            "status": "ok",
            "action_ref": row["action_ref"],
            "workspace_client_id": row["workspace_client_id"],
            "user_id": row["user_id"],
        }
    cur.execute(
        "SELECT consumed_at, action_ref, workspace_client_id, "
        "(expires_at <= now()) AS expired FROM action_nonces "
        f"WHERE token = %s AND tenant_id = %s{kind_sql}",
        (token, tenant_id) + kind_params,
    )
    info = cur.fetchone()
    if info is None:
        return {"status": "missing"}
    if info["consumed_at"] is not None:
        return {
            "status": "used",
            "action_ref": info["action_ref"],
            "workspace_client_id": info["workspace_client_id"],
        }
    return {"status": "expired"}


def latest_pending(cur, *, tenant_id, user_id, kind, within_minutes=15):
    cur.execute(
        "SELECT token FROM action_nonces "
        "WHERE tenant_id = %s AND user_id = %s AND consumed_at IS NULL "
        "  AND expires_at > now() AND created_at > now() - make_interval(mins => %s) "
        "  AND action_ref LIKE %s "
        "ORDER BY created_at DESC LIMIT 1",
        (tenant_id, str(user_id or ""), int(within_minutes), f'%"kind": "{kind}"%'),
    )
    row = cur.fetchone()
    return row["token"] if row else None

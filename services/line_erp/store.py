from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone

_TABLES = ("line_erp_bindings", "line_erp_binding_codes", "erp_line_sessions")
_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_line_erp_bindings_user ON line_erp_bindings(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_line_erp_codes_expiry ON line_erp_binding_codes(expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_erp_line_sessions_expiry ON erp_line_sessions(expires_at)",
)


def ensure_tables() -> None:
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS line_erp_bindings (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(), line_user_id text UNIQUE NOT NULL,
            tenant_id uuid NOT NULL, user_id uuid NOT NULL, workspace_client_id bigint,
            display_name text, bound_at timestamptz DEFAULT now(), last_active_at timestamptz)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS line_erp_binding_codes (
            code text PRIMARY KEY, tenant_id uuid NOT NULL, user_id uuid NOT NULL,
            workspace_client_id bigint, expires_at timestamptz NOT NULL, used_at timestamptz)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS erp_line_sessions (
            tenant_id uuid NOT NULL, line_user_id text NOT NULL, state text NOT NULL,
            payload jsonb NOT NULL DEFAULT '{}', expires_at timestamptz NOT NULL,
            PRIMARY KEY (tenant_id, line_user_id))""")
        for statement in _INDEXES:
            cur.execute(statement)
        apply_tenant_rls(cur, *_TABLES)


def ensure_table() -> None:
    """启动器统一调用名；ERP 三表一次性建立。"""
    ensure_tables()


def new_code(tenant_id, user_id, workspace_client_id=None) -> dict:
    from core import db

    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    for _ in range(5):
        code = f"{secrets.randbelow(900000) + 100000}"
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE line_erp_binding_codes SET used_at=now() WHERE user_id=%s AND used_at IS NULL",
                    (str(user_id),),
                )
                cur.execute(
                    "INSERT INTO line_erp_binding_codes(code,tenant_id,user_id,workspace_client_id,expires_at) VALUES(%s,%s,%s,%s,%s)",
                    (code, tenant_id, user_id, workspace_client_id, expires),
                )
            return {"code": code, "expires_at": expires.isoformat()}
        except Exception as exc:
            if (
                getattr(exc, "sqlstate", None) != "23505"
                and getattr(exc, "pgcode", None) != "23505"
            ):
                raise
    raise RuntimeError("ERP binding code generation exhausted")


def get_binding(line_user_id: str):
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT tenant_id,user_id,workspace_client_id,display_name FROM line_erp_bindings WHERE line_user_id=%s",
            (line_user_id,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def get_binding_by_user(user_id: str):
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT tenant_id,user_id,workspace_client_id,display_name,line_user_id,bound_at FROM line_erp_bindings WHERE user_id=%s",
            (str(user_id),),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def consume_code(code: str):
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE line_erp_binding_codes SET used_at=now() WHERE code=%s AND used_at IS NULL AND expires_at>now() RETURNING tenant_id,user_id,workspace_client_id",
            (str(code).strip(),),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def bind(ident: dict, line_user_id: str, display_name: str = "") -> bool:
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute("SELECT user_id FROM line_erp_bindings WHERE line_user_id=%s", (line_user_id,))
        row = cur.fetchone()
        if row and str(row["user_id"]) != str(ident["user_id"]):
            return False
        cur.execute(
            "DELETE FROM line_erp_bindings WHERE user_id=%s AND line_user_id<>%s",
            (str(ident["user_id"]), line_user_id),
        )
        cur.execute(
            """INSERT INTO line_erp_bindings(line_user_id,tenant_id,user_id,workspace_client_id,display_name,last_active_at)
            VALUES(%s,%s,%s,%s,%s,now()) ON CONFLICT(line_user_id) DO UPDATE SET
            tenant_id=EXCLUDED.tenant_id,user_id=EXCLUDED.user_id,workspace_client_id=EXCLUDED.workspace_client_id,
            display_name=EXCLUDED.display_name,last_active_at=now()""",
            (
                line_user_id,
                ident["tenant_id"],
                ident["user_id"],
                ident.get("workspace_client_id"),
                display_name,
            ),
        )
    return True


def get_session(tenant_id, line_user_id):
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT state,payload,expires_at FROM erp_line_sessions WHERE tenant_id=%s AND line_user_id=%s AND expires_at>now()",
            (tenant_id, line_user_id),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def claim_processing(tenant_id, line_user_id, message_id, ttl_minutes=15):
    """Atomically reserve a receiving session before one billable OCR run."""
    from core import db

    expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """UPDATE erp_line_sessions SET
            state='ocr_processing',
            payload=jsonb_build_object('mode', payload->>'mode', 'message_id', %s),
            expires_at=%s
            WHERE tenant_id=%s AND line_user_id=%s AND state='receiving'
              AND expires_at>now() AND payload->>'mode' IN ('purchase','sales')
            RETURNING payload->>'mode' AS mode""",
            (str(message_id or ""), expires, tenant_id, line_user_id),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def clear_session(tenant_id, line_user_id):
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM erp_line_sessions WHERE tenant_id=%s AND line_user_id=%s",
            (tenant_id, line_user_id),
        )


def unbind_by_user(user_id) -> bool:
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT tenant_id,line_user_id FROM line_erp_bindings WHERE user_id=%s", (str(user_id),)
        )
        bindings = cur.fetchall() or []
        cur.execute(
            "DELETE FROM line_erp_binding_codes WHERE user_id=%s AND used_at IS NULL",
            (str(user_id),),
        )
        for binding in bindings:
            cur.execute(
                "DELETE FROM erp_line_sessions WHERE tenant_id=%s AND line_user_id=%s",
                (binding["tenant_id"], binding["line_user_id"]),
            )
        cur.execute("DELETE FROM line_erp_bindings WHERE user_id=%s", (str(user_id),))
    return True


def set_session(tenant_id, line_user_id, state, payload=None, ttl_minutes=30):
    from core import db

    expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO erp_line_sessions(tenant_id,line_user_id,state,payload,expires_at)
            VALUES(%s,%s,%s,%s::jsonb,%s) ON CONFLICT(tenant_id,line_user_id) DO UPDATE SET
            state=EXCLUDED.state,payload=EXCLUDED.payload,expires_at=EXCLUDED.expires_at""",
            (tenant_id, line_user_id, state, json.dumps(payload or {}), expires),
        )

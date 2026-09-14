"""Independent, locked LINE work conversations and native-operation receipts."""

from __future__ import annotations

import json
from contextlib import contextmanager

from core import db

TABLE = """
CREATE TABLE IF NOT EXISTS cowork_line_work_sessions (
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    membership_id uuid NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
    payload jsonb NOT NULL DEFAULT '{}',
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, membership_id)
)
"""


def migrate_schema():
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        from services.cowork_line.work_notifications import TABLE as NOTIFICATIONS

        cur.execute(TABLE)
        apply_tenant_rls(cur, "cowork_line_work_sessions")
        cur.execute(NOTIFICATIONS)
        apply_tenant_rls(cur, "cowork_line_work_notifications")


@contextmanager
def conversation(identity):
    with db.get_cursor_rls(identity["tenant_id"], commit=True) as cur:
        cur.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            ("line-work:" + identity["membership_id"],),
        )
        cur.execute(
            "SELECT payload FROM cowork_line_work_sessions "
            "WHERE tenant_id=%s AND membership_id=%s",
            (identity["tenant_id"], identity["membership_id"]),
        )
        row = cur.fetchone()
        payload = dict(row["payload"]) if row else {}
        yield payload
        cur.execute(
            "INSERT INTO cowork_line_work_sessions (tenant_id, membership_id, payload) "
            "VALUES (%s, %s, %s::jsonb) ON CONFLICT (tenant_id, membership_id) "
            "DO UPDATE SET payload=EXCLUDED.payload, updated_at=now()",
            (identity["tenant_id"], identity["membership_id"], json.dumps(payload)),
        )

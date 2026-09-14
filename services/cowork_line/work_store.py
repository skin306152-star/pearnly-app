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

BOARDS = """
CREATE TABLE IF NOT EXISTS cowork_line_work_boards (
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    board_id text NOT NULL,
    mapping jsonb NOT NULL,
    updated_by uuid NOT NULL REFERENCES users(id),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, board_id)
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
        cur.execute(BOARDS)
        apply_tenant_rls(cur, "cowork_line_work_boards")


def publish_mapping(identity, board_id, mapping):
    with db.get_cursor_rls(identity["tenant_id"], commit=True) as cur:
        cur.execute(
            "INSERT INTO cowork_line_work_boards (tenant_id,board_id,mapping,updated_by) "
            "VALUES (%s,%s,%s::jsonb,%s) ON CONFLICT (tenant_id,board_id) "
            "DO UPDATE SET mapping=EXCLUDED.mapping,updated_by=EXCLUDED.updated_by,updated_at=now()",
            (identity["tenant_id"], board_id, json.dumps(mapping), identity["user_id"]),
        )


def board_mapping(identity, board_id):
    with db.get_cursor_rls(identity["tenant_id"]) as cur:
        cur.execute(
            "SELECT mapping FROM cowork_line_work_boards WHERE tenant_id=%s AND board_id=%s",
            (identity["tenant_id"], board_id),
        )
        row = cur.fetchone()
    return row["mapping"] if row else {}


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

"""Delivery receipts; business status remains in the existing domain tables."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal
import uuid

from core.db import get_cursor

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS cloud_task_deliveries (
    id UUID PRIMARY KEY,
    handler TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'uncertain')),
    lease_until TIMESTAMPTZ,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


INTERNAL_ACL = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
        REVOKE ALL ON cloud_task_deliveries, cloud_task_locks FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
        REVOKE ALL ON cloud_task_deliveries, cloud_task_locks FROM authenticated;
    END IF;
END $$
"""


def ensure_table():
    if os.environ.get("PEARNLY_RUNTIME_ROLE") in {"web", "worker"}:
        raise RuntimeError("cloud_task_schema_requires_release_job")
    with get_cursor(commit=True) as cur:
        cur.execute(DDL)
        cur.execute(
            "CREATE TABLE IF NOT EXISTS cloud_task_locks ("
            "name TEXT PRIMARY KEY, owner UUID NOT NULL, lease_until TIMESTAMPTZ NOT NULL)"
        )
        cur.execute("ALTER TABLE cloud_task_locks ENABLE ROW LEVEL SECURITY")
        cur.execute("REVOKE ALL ON cloud_task_locks FROM PUBLIC")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS cloud_task_pending "
            "ON cloud_task_deliveries(status, created_at)"
        )
        # Internal transport is not a tenant-facing API. Never grant client access.
        cur.execute("ALTER TABLE cloud_task_deliveries ENABLE ROW LEVEL SECURITY")
        cur.execute("REVOKE ALL ON cloud_task_deliveries FROM PUBLIC")
        cur.execute(INTERNAL_ACL)


def _json_value(value):
    if isinstance(value, (uuid.UUID, Decimal)):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"unsupported_task_payload:{type(value).__name__}")


def insert(handler: str, payload: dict) -> str:
    task_id = str(uuid.uuid4())
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False, default=_json_value)
    if len(encoded.encode()) > 2_000_000:
        raise ValueError("cloud_task_payload_too_large")
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO cloud_task_deliveries(id, handler, payload) "
            "VALUES (%s::uuid, %s, %s::jsonb)",
            (task_id, handler, encoded),
        )
    return task_id


def claim(task_id: str):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE cloud_task_deliveries SET status='running', "
            "lease_until=now()+interval '35 minutes', updated_at=now() "
            "WHERE id=%s::uuid AND status='pending' RETURNING *",
            (task_id,),
        )
        row = cur.fetchone()
        if row:
            return dict(row)
        cur.execute("SELECT status FROM cloud_task_deliveries WHERE id=%s::uuid", (task_id,))
        existing = cur.fetchone()
        return dict(existing) if existing else None


def finish(task_id: str, status: str, error_code: str | None = None):
    if status not in {"succeeded", "failed", "uncertain"}:
        raise ValueError("invalid_delivery_status")
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE cloud_task_deliveries SET status=%s, error_code=%s, "
            "updated_at=now() WHERE id=%s::uuid AND status='running'",
            (status, error_code, task_id),
        )


def recoverable(limit: int = 100):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE cloud_task_deliveries SET payload='{}'::jsonb "
            "WHERE status='succeeded' AND updated_at < now()-interval '7 days' "
            "AND payload <> '{}'::jsonb"
        )
        # A process can die after an external write. Do not guess that it is safe to replay.
        cur.execute(
            "UPDATE cloud_task_deliveries SET status='uncertain', "
            "error_code='execution_lease_expired', updated_at=now() "
            "WHERE status='running' AND lease_until < now() RETURNING id, handler"
        )
        expired = list(cur.fetchall())
        cur.execute(
            "SELECT id FROM cloud_task_deliveries WHERE status='pending' "
            "ORDER BY created_at LIMIT %s",
            (limit,),
        )
        pending = [str(row["id"]) for row in cur.fetchall()]
    for row in expired:
        logger.error("cloud_task_uncertain id=%s handler=%s", row["id"], row["handler"])
    return pending


def acquire_maintenance():
    owner = str(uuid.uuid4())
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO cloud_task_locks(name, owner, lease_until) "
            "VALUES ('maintenance', %s::uuid, now()+interval '35 minutes') "
            "ON CONFLICT(name) DO UPDATE SET owner=EXCLUDED.owner, "
            "lease_until=EXCLUDED.lease_until "
            "WHERE cloud_task_locks.lease_until < now() RETURNING owner",
            (owner,),
        )
        row = cur.fetchone()
        return owner if row else None


def release_maintenance(owner: str):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM cloud_task_locks WHERE name='maintenance' AND owner=%s::uuid", (owner,)
        )

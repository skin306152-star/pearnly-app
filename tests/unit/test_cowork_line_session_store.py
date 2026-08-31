from __future__ import annotations

import json
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import patch

from services.cowork_line import schema, session_store


class FakeCursor:
    def __init__(self, rows=None, *, rowcount=0):
        self.rows = list(rows or [])
        self.rowcount = rowcount
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append((statement, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


def rls_context(cursor, tenants):
    @contextmanager
    def get_cursor_rls(tenant_id, *, commit=False):
        tenants.append((tenant_id, commit))
        yield cursor

    return get_cursor_rls


class CoworkLineSessionStoreTests(unittest.TestCase):
    def test_schema_adds_isolated_session_table_and_rls(self):
        ddl = " ".join(schema.DDL).lower()
        self.assertIn("create table if not exists cowork_line_sessions", ddl)
        self.assertIn("primary key (tenant_id, line_user_id)", ddl)
        cursor = FakeCursor()

        @contextmanager
        def get_cursor(*, commit=False):
            self.assertTrue(commit)
            yield cursor

        with (
            patch.object(schema.db, "get_cursor", get_cursor),
            patch.object(schema, "apply_tenant_rls") as apply_rls,
        ):
            schema.ensure_schema()
        apply_rls.assert_called_once()
        self.assertIn("cowork_line_sessions", apply_rls.call_args.args)

    def test_set_session_accepts_flow_states_without_fixed_enum(self):
        expires_at = datetime(2026, 8, 31, tzinfo=timezone.utc)
        cursor = FakeCursor(
            [
                {
                    "state": "select_direction",
                    "payload": {"erp": "mrerp", "account": "A1"},
                    "expires_at": expires_at,
                }
            ]
        )
        tenants = []
        with patch.object(
            session_store.db,
            "get_cursor_rls",
            rls_context(cursor, tenants),
        ):
            stored = session_store.set_session(
                tenant_id="tenant-1",
                line_user_id="U1",
                state="select_direction",
                payload={"erp": "mrerp", "account": "A1"},
            )
        self.assertEqual(stored["state"], "select_direction")
        self.assertEqual(stored["payload"], {"erp": "mrerp", "account": "A1"})
        self.assertEqual(tenants, [("tenant-1", True)])
        params = cursor.calls[0][1]
        self.assertEqual(json.loads(params[3]), {"erp": "mrerp", "account": "A1"})

    def test_claim_processing_is_atomic_and_preserves_payload(self):
        preserved = {
            "erp": "express",
            "account": "A1",
            "direction": "purchase",
            "mode": "stock",
            "nested": {"scope": ["one", "two"]},
            "message_id": "message-new",
        }
        cursor = FakeCursor(
            [
                {
                    "state": "ocr_processing",
                    "payload": preserved,
                    "expires_at": datetime(2026, 8, 31, tzinfo=timezone.utc),
                }
            ]
        )
        tenants = []
        with patch.object(
            session_store.db,
            "get_cursor_rls",
            rls_context(cursor, tenants),
        ):
            claimed = session_store.claim_processing(
                tenant_id="tenant-1",
                line_user_id="U1",
                message_id="message-new",
            )
        sql, params = cursor.calls[0]
        self.assertIn("UPDATE cowork_line_sessions", sql)
        self.assertIn("jsonb_set", sql)
        self.assertNotIn("jsonb_build_object", sql)
        self.assertIn("AND state = %s", sql)
        self.assertEqual(params[0], "message-new")
        self.assertEqual(params[-1], "receiving")
        self.assertEqual(claimed["payload"], preserved)
        self.assertEqual(tenants, [("tenant-1", True)])

    def test_claim_returns_none_when_state_was_not_receiving(self):
        cursor = FakeCursor()
        with patch.object(
            session_store.db,
            "get_cursor_rls",
            rls_context(cursor, []),
        ):
            self.assertIsNone(
                session_store.claim_processing(
                    tenant_id="tenant-1",
                    line_user_id="U1",
                    message_id="message-2",
                )
            )


if __name__ == "__main__":
    unittest.main()

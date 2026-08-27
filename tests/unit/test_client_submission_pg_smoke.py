# -*- coding: utf-8 -*-
"""ERP 确认快照直达精确 Cowork workspace 的真 PostgreSQL 冒烟。"""

from __future__ import annotations

import contextlib
import unittest
import uuid
from unittest import mock

from core.rls import ensure_rls_app_role
from services.accounting_engagement import lifecycle
from services.accounting_engagement import schema as engagement_schema
from services.client_submission import enqueue, store, worker
from services.client_submission import schema as submission_schema
from services.client_submission.errors import REVISION_CONFLICT, SubmissionError
from services.firm import schema as firm_schema
from services.firm import store as firm_store
from tests.unit._pg_smoke import connect, connect_or_skip

BASE_DDL = """
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    display_name text,
    tenant_type text NOT NULL DEFAULT 'shared_api',
    status text NOT NULL DEFAULT 'active',
    tenant_type_v2 text,
    owner_user_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS display_name text;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS owner_user_id uuid;
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text NOT NULL,
    password_hash text NOT NULL,
    tenant_id uuid
);
CREATE TABLE IF NOT EXISTS tenant_modules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    module_key text NOT NULL,
    enabled boolean NOT NULL DEFAULT false,
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, module_key)
);
CREATE TABLE IF NOT EXISTS workspace_clients (
    id bigserial PRIMARY KEY,
    tenant_id uuid,
    user_id uuid NOT NULL,
    name text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ocr_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    tenant_id uuid,
    filename text NOT NULL,
    page_count integer NOT NULL DEFAULT 1,
    file_hash text,
    pages jsonb NOT NULL,
    confidence text,
    elapsed_ms integer,
    invoice_no text,
    invoice_date date,
    seller_name text,
    total_amount numeric(14,2),
    source text NOT NULL DEFAULT 'manual',
    source_ref text,
    workspace_client_id bigint,
    ai_raw jsonb,
    staged boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS user_id uuid;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS tenant_id uuid;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS filename text;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS page_count integer NOT NULL DEFAULT 1;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS file_hash text;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS pages jsonb;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS confidence text;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS elapsed_ms integer;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS invoice_no text;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS invoice_date date;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS seller_name text;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS total_amount numeric(14,2);
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS source text NOT NULL DEFAULT 'manual';
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS source_ref text;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS workspace_client_id bigint;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS ai_raw jsonb;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS staged boolean NOT NULL DEFAULT false;
"""


class ClientSubmissionPgSmokeTests(unittest.TestCase):
    conn = None

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        @contextlib.contextmanager
        def cursor(*_args, **_kwargs):
            cur = cls.conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cur
                cls.conn.commit()
            except Exception:
                cls.conn.rollback()
                raise
            finally:
                cur.close()

        cls.cursor = cursor
        cls.ids = {
            name: str(uuid.uuid4())
            for name in ("firm", "merchant", "outsider", "firm_user", "merchant_user", "admin")
        }
        with cursor() as cur:
            cur.execute(BASE_DDL)
            for name, layer in (("firm", "f_firm"), ("merchant", None), ("outsider", None)):
                cur.execute(
                    "INSERT INTO tenants (id, name, tenant_type_v2) VALUES (%s, %s, %s)",
                    (cls.ids[name], f"submission-{name}-{cls.ids[name][:8]}", layer),
                )
            cur.execute(
                "INSERT INTO users (id, username, password_hash, tenant_id) VALUES "
                "(%s, %s, 'test-only', %s), (%s, %s, 'test-only', %s), "
                "(%s, %s, 'test-only', NULL)",
                (
                    cls.ids["firm_user"],
                    f"submission-firm-{cls.ids['firm_user'][:8]}",
                    cls.ids["firm"],
                    cls.ids["merchant_user"],
                    f"submission-merchant-{cls.ids['merchant_user'][:8]}",
                    cls.ids["merchant"],
                    cls.ids["admin"],
                    f"submission-admin-{cls.ids['admin'][:8]}",
                ),
            )
            cur.execute(
                "UPDATE tenants SET owner_user_id = CASE "
                "WHEN id = %s THEN %s::uuid WHEN id = %s THEN %s::uuid END "
                "WHERE id IN (%s, %s)",
                (
                    cls.ids["firm"],
                    cls.ids["firm_user"],
                    cls.ids["merchant"],
                    cls.ids["merchant_user"],
                    cls.ids["firm"],
                    cls.ids["merchant"],
                ),
            )
            for tenant_name, user_name in (
                ("firm", "firm_user"),
                ("merchant", "merchant_user"),
                ("outsider", "merchant_user"),
            ):
                cur.execute(
                    "INSERT INTO workspace_clients (tenant_id, user_id, name) "
                    "VALUES (%s, %s, %s) RETURNING id",
                    (
                        cls.ids[tenant_name],
                        cls.ids[user_name],
                        f"submission-ws-{tenant_name}",
                    ),
                )
                cls.ids[f"ws_{tenant_name}"] = cur.fetchone()["id"]

        cls.db_patch = mock.patch("core.db.get_cursor", cursor)
        cls.rls_patch = mock.patch("core.db.get_cursor_rls", cursor)
        cls.db_patch.start()
        cls.rls_patch.start()
        firm_schema.ensure_firm_schema()
        with cursor() as cur:
            firm_store.create_profile(
                cur, tenant_id=cls.ids["firm"], display_name="Submission Firm"
            )
        engagement_schema.ensure_accounting_engagement_schema()
        submission_schema.ensure_client_submission_schema()
        with cursor() as cur:
            ensure_rls_app_role(cur)

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            with cls.cursor() as cur:
                cur.execute(
                    "DELETE FROM client_submissions WHERE source_tenant_id = %s",
                    (cls.ids["merchant"],),
                )
                cur.execute(
                    "DELETE FROM ocr_history WHERE source = 'erp_client_submission' "
                    "AND tenant_id = %s",
                    (cls.ids["firm"],),
                )
                cur.execute(
                    "DELETE FROM accounting_engagements WHERE merchant_tenant_id = %s",
                    (cls.ids["merchant"],),
                )
                cur.execute(
                    "DELETE FROM workspace_clients WHERE id = ANY(%s::bigint[])",
                    ([cls.ids["ws_firm"], cls.ids["ws_merchant"], cls.ids["ws_outsider"]],),
                )
                cur.execute(
                    "DELETE FROM users WHERE id = ANY(%s::uuid[])",
                    ([cls.ids["firm_user"], cls.ids["merchant_user"], cls.ids["admin"]],),
                )
                cur.execute(
                    "DELETE FROM tenants WHERE id = ANY(%s::uuid[])",
                    ([cls.ids["firm"], cls.ids["merchant"], cls.ids["outsider"]],),
                )
        finally:
            cls.rls_patch.stop()
            cls.db_patch.stop()
            cls.conn.close()

    def setUp(self):
        with self.cursor() as cur:
            cur.execute(
                "DELETE FROM client_submissions WHERE source_tenant_id = %s",
                (self.ids["merchant"],),
            )
            cur.execute(
                "DELETE FROM ocr_history WHERE source = 'erp_client_submission' "
                "AND tenant_id = %s",
                (self.ids["firm"],),
            )
            cur.execute(
                "DELETE FROM accounting_engagements WHERE merchant_tenant_id = %s",
                (self.ids["merchant"],),
            )
            invited = lifecycle.invite(
                cur,
                firm_tenant_id=self.ids["firm"],
                merchant_tenant_id=self.ids["merchant"],
                admin_user_id=self.ids["admin"],
            )
            lifecycle.accept_merchant(
                cur,
                engagement_id=invited["id"],
                merchant_tenant_id=self.ids["merchant"],
                workspace_client_id=self.ids["ws_merchant"],
            )
            self.engagement = lifecycle.accept_firm(
                cur,
                engagement_id=invited["id"],
                firm_tenant_id=self.ids["firm"],
                workspace_client_id=self.ids["ws_firm"],
            )

    def snapshot(self, amount="125.50"):
        return {
            "filename": "merchant-invoice.pdf",
            "fields": {
                "invoice_number": "INV-001",
                "date": "2026-08-27",
                "seller_name": "Merchant Vendor",
                "total_amount": amount,
                "items": [{"name": "Paper", "quantity": 1, "unit_price": amount}],
            },
        }

    def enqueue(self, snapshot=None):
        with self.cursor() as cur:
            return enqueue.enqueue_confirmed_document(
                cur,
                merchant_tenant_id=self.ids["merchant"],
                merchant_workspace_client_id=self.ids["ws_merchant"],
                source_document_type="purchase",
                source_document_id="merchant-doc-1",
                source_revision=1,
                snapshot=snapshot or self.snapshot(),
                original_file_ref="merchant/private/invoice.pdf",
            )

    def test_duplicate_confirm_reuses_submission_and_delivers_once(self):
        first = self.enqueue()
        repeated = self.enqueue()
        self.assertEqual(first["id"], repeated["id"])
        self.assertTrue(worker.deliver_one(first["id"]))
        self.assertFalse(worker.deliver_one(first["id"]))

        with self.cursor() as cur:
            cur.execute(
                "SELECT status, cowork_history_id::text AS history_id "
                "FROM client_submissions WHERE id = %s",
                (first["id"],),
            )
            delivered = cur.fetchone()
            self.assertEqual(delivered["status"], "delivered")
            cur.execute(
                "SELECT tenant_id::text, workspace_client_id, source, source_ref, staged, pages "
                "FROM ocr_history WHERE id = %s",
                (delivered["history_id"],),
            )
            history = cur.fetchone()
            self.assertEqual(history["tenant_id"], self.ids["firm"])
            self.assertEqual(history["workspace_client_id"], self.ids["ws_firm"])
            self.assertEqual(history["source"], "erp_client_submission")
            self.assertEqual(history["source_ref"], first["id"])
            self.assertTrue(history["staged"])
            self.assertEqual(history["pages"][0]["fields"]["items"][0]["name"], "Paper")

    def test_same_revision_with_changed_snapshot_is_rejected(self):
        self.enqueue()
        with self.assertRaises(SubmissionError) as error:
            self.enqueue(self.snapshot("999.00"))
        self.assertEqual(error.exception.code, REVISION_CONFLICT)
        with self.cursor() as cur:
            cur.execute(
                "SELECT count(*) AS n FROM client_submissions WHERE source_tenant_id = %s",
                (self.ids["merchant"],),
            )
            self.assertEqual(cur.fetchone()["n"], 1)

    def test_delivered_history_can_follow_cowork_retention_without_losing_audit_status(self):
        pending = self.enqueue()
        self.assertTrue(worker.deliver_one(pending["id"]))
        with self.cursor() as cur:
            cur.execute(
                "SELECT cowork_history_id::text AS history_id "
                "FROM client_submissions WHERE id = %s",
                (pending["id"],),
            )
            history_id = cur.fetchone()["history_id"]
            cur.execute("DELETE FROM ocr_history WHERE id = %s::uuid", (history_id,))
            cur.execute(
                "SELECT status, cowork_history_id, delivered_at "
                "FROM client_submissions WHERE id = %s",
                (pending["id"],),
            )
            submission_row = cur.fetchone()
        self.assertEqual(submission_row["status"], "delivered")
        self.assertIsNone(submission_row["cowork_history_id"])
        self.assertIsNotNone(submission_row["delivered_at"])

    def test_suspended_waits_and_ended_supersedes_without_delivery(self):
        with self.cursor() as cur:
            lifecycle.suspend(
                cur,
                engagement_id=self.engagement["id"],
                tenant_id=self.ids["merchant"],
            )
        pending = self.enqueue()
        tick = worker.run_tick()
        self.assertEqual(tick["due"], 0)

        with self.cursor() as cur:
            lifecycle.end(
                cur,
                engagement_id=self.engagement["id"],
                tenant_id=self.ids["merchant"],
            )
        tick = worker.run_tick()
        self.assertEqual(tick["superseded"], 1)
        with self.cursor() as cur:
            cur.execute("SELECT status FROM client_submissions WHERE id = %s", (pending["id"],))
            self.assertEqual(cur.fetchone()["status"], "superseded")
            cur.execute(
                "SELECT count(*) AS n FROM ocr_history WHERE source_ref = %s", (pending["id"],)
            )
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_source_and_target_can_read_submission_but_outsider_cannot(self):
        self.enqueue()
        for tenant_name, expected in (("merchant", 1), ("firm", 1), ("outsider", 0)):
            conn = connect()
            try:
                cur = conn.cursor()
                cur.execute("SET LOCAL ROLE pearnly_app")
                cur.execute("SET LOCAL app.current_tenant_id = %s", (self.ids[tenant_name],))
                cur.execute(
                    "SELECT count(*) FROM client_submissions WHERE source_tenant_id = %s",
                    (self.ids["merchant"],),
                )
                self.assertEqual(cur.fetchone()[0], expected)
            finally:
                conn.rollback()
                conn.close()

    def test_participants_cannot_mutate_submission_snapshot_or_status(self):
        submission = self.enqueue()
        for tenant_name in ("merchant", "firm", "outsider"):
            conn = connect()
            try:
                cur = conn.cursor()
                cur.execute("SET LOCAL ROLE pearnly_app")
                cur.execute("SET LOCAL app.current_tenant_id = %s", (self.ids[tenant_name],))
                cur.execute(
                    "UPDATE client_submissions "
                    "SET snapshot_json = '{}'::jsonb, status = 'delivered' "
                    "WHERE id = %s::uuid",
                    (submission["id"],),
                )
                self.assertEqual(cur.rowcount, 0)
            finally:
                conn.rollback()
                conn.close()

        with self.cursor() as cur:
            cur.execute(
                "SELECT status, snapshot_json FROM client_submissions WHERE id = %s::uuid",
                (submission["id"],),
            )
            row = cur.fetchone()
            self.assertEqual(row["status"], "pending")
            self.assertEqual(row["snapshot_json"]["fields"]["invoice_number"], "INV-001")

    def test_merchant_app_role_can_insert_only_through_exact_active_relationship(self):
        from psycopg2.extras import RealDictCursor

        conn = connect()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SET LOCAL ROLE pearnly_app")
            cur.execute("SET LOCAL app.current_tenant_id = %s", (self.ids["merchant"],))
            created = store.create_pending(
                cur,
                engagement=self.engagement,
                source_document_type="sales",
                source_document_id="merchant-app-role-doc",
                source_revision=1,
                source_hash="app-role-hash",
                snapshot={"fields": {"invoice_number": "APP-ROLE-1"}},
                original_file_ref=None,
            )
            self.assertEqual(created["source_tenant_id"], self.ids["merchant"])
            self.assertEqual(created["target_tenant_id"], self.ids["firm"])
        finally:
            conn.rollback()
            conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)

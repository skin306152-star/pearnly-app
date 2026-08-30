"""Managed shared-log visibility across actors, backed by disposable PostgreSQL."""

from __future__ import annotations

import uuid
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock, patch

from psycopg2.extras import RealDictCursor

from core import db  # Import the DAL facade before its push-log implementation.
from services.erp import push_log_queries
from services.erp.shared_express_log_access import enable_managed_log_reader
from services.sales import record_enrichment
from tests.unit._pg_smoke import connect_or_skip, require_disposable_db

TENANT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ACTOR_A = "11111111-1111-4111-8111-111111111111"
ACTOR_B = "22222222-2222-4222-8222-222222222222"
WORKSPACE = 101
OTHER_WORKSPACE = 202
MANAGED_ENDPOINT = "33333333-3333-4333-8333-333333333333"
LEGACY_ENDPOINT = "44444444-4444-4444-8444-444444444444"
MANAGED_HISTORY = "55555555-5555-4555-8555-555555555555"
LEGACY_HISTORY = "66666666-6666-4666-8666-666666666666"


class ManagedLogReaderPermissionTests(unittest.TestCase):
    def test_reader_requires_membership_permission_and_workspace_scope(self):
        cur = Mock()
        allowed = SimpleNamespace(
            membership_id="membership",
            has=Mock(return_value=True),
            allows_workspace=Mock(return_value=True),
        )
        with (
            patch("services.authz.resolver.resolve", return_value=allowed),
            patch(
                "services.erp.shared_express_schema.enable_shared_express_select",
                return_value=True,
            ) as enable_select,
        ):
            self.assertTrue(
                enable_managed_log_reader(
                    cur,
                    user_id=ACTOR_B,
                    tenant_id=TENANT,
                    workspace_client_id=WORKSPACE,
                )
            )
        allowed.has.assert_called_once_with("erp.log.view")
        allowed.allows_workspace.assert_called_once_with(WORKSPACE)
        enable_select.assert_called_once_with(cur, TENANT, WORKSPACE)

        denied = SimpleNamespace(
            membership_id="membership",
            has=Mock(return_value=True),
            allows_workspace=Mock(return_value=False),
        )
        with (
            patch("services.authz.resolver.resolve", return_value=denied),
            patch(
                "services.erp.shared_express_schema.enable_shared_express_select"
            ) as enable_select,
        ):
            self.assertFalse(
                enable_managed_log_reader(
                    cur,
                    user_id=ACTOR_B,
                    tenant_id=TENANT,
                    workspace_client_id=OTHER_WORKSPACE,
                )
            )
        enable_select.assert_not_called()


class ManagedLogReaderPgSmokeTests(unittest.TestCase):
    _schema_prefix = "smoke_shared_log_read_"

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.schema = cls._schema_prefix + uuid.uuid4().hex[:12]
        cls.cur.execute(f'CREATE SCHEMA "{cls.schema}"')
        cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
        cls.cur.execute("""
            CREATE TABLE erp_endpoints (
                id UUID PRIMARY KEY, tenant_id UUID, workspace_client_id BIGINT,
                name TEXT, adapter TEXT, config JSONB NOT NULL DEFAULT '{}'::jsonb,
                shared_scope BOOLEAN NOT NULL DEFAULT FALSE,
                binding_generation BIGINT NOT NULL DEFAULT 0
            );
            CREATE TABLE ocr_history (
                id UUID PRIMARY KEY, tenant_id UUID, user_id UUID,
                workspace_client_id BIGINT, client_id BIGINT, pages JSONB,
                source TEXT, posting_kind TEXT
            );
            CREATE TABLE clients (id BIGINT PRIMARY KEY, name TEXT);
            CREATE TABLE workspace_clients (id BIGINT PRIMARY KEY, name TEXT);
            CREATE TABLE erp_push_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(), endpoint_id UUID,
                history_id UUID, user_id UUID NOT NULL, tenant_id UUID,
                workspace_client_id BIGINT, invoice_no TEXT, seller_name TEXT,
                total_amount NUMERIC, status TEXT NOT NULL, http_status INTEGER,
                error_msg TEXT, attempt INTEGER NOT NULL DEFAULT 1,
                elapsed_ms INTEGER, trigger TEXT NOT NULL DEFAULT 'manual',
                created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                next_retry_at TIMESTAMPTZ, response_body JSONB, request_body JSONB
            );
        """)
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            cls.conn.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, cls._schema_prefix)
            cls.cur.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')
            cls.conn.commit()
        finally:
            cls.cur.close()
            cls.conn.close()

    def setUp(self):
        self.conn.rollback()
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute(
            "TRUNCATE erp_push_logs, erp_endpoints, ocr_history, clients, workspace_clients"
        )
        self.cur.execute(
            "INSERT INTO workspace_clients VALUES (%s,'Main'),(%s,'Other')",
            (WORKSPACE, OTHER_WORKSPACE),
        )
        self.cur.execute(
            "INSERT INTO erp_endpoints "
            "(id,tenant_id,workspace_client_id,name,adapter,shared_scope,binding_generation) "
            "VALUES (%s,%s,%s,'Managed','express',TRUE,7),"
            "(%s,%s,%s,'Legacy','express',TRUE,0)",
            (
                MANAGED_ENDPOINT,
                TENANT,
                WORKSPACE,
                LEGACY_ENDPOINT,
                TENANT,
                WORKSPACE,
            ),
        )
        self.cur.execute(
            "INSERT INTO ocr_history "
            "(id,tenant_id,user_id,workspace_client_id,pages,source,posting_kind) "
            "VALUES (%s,%s,%s,%s,'[]','upload','purchase'),"
            "(%s,%s,%s,%s,'[]','upload','purchase')",
            (
                MANAGED_HISTORY,
                TENANT,
                ACTOR_A,
                WORKSPACE,
                LEGACY_HISTORY,
                TENANT,
                ACTOR_A,
                WORKSPACE,
            ),
        )
        self.cur.execute(
            "INSERT INTO erp_push_logs "
            "(endpoint_id,history_id,user_id,tenant_id,workspace_client_id,invoice_no,status,request_body,response_body) "
            "VALUES (%s,%s,%s,%s,%s,'M-1','pending','{}','{}'),"
            "(%s,%s,%s,%s,%s,'L-1','success','{}','{}')",
            (
                MANAGED_ENDPOINT,
                MANAGED_HISTORY,
                ACTOR_A,
                TENANT,
                WORKSPACE,
                LEGACY_ENDPOINT,
                LEGACY_HISTORY,
                ACTOR_A,
                TENANT,
                WORKSPACE,
            ),
        )
        self.conn.commit()

    @contextmanager
    def _cursor(self, **_context):
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        yield self.cur

    @staticmethod
    def _authorized_workspace(*_args, **kwargs):
        return kwargs.get("workspace_client_id") == WORKSPACE

    def test_actor_b_reads_actor_a_managed_log_but_not_gen0_or_other_workspace(self):
        with (
            patch.object(db, "get_cursor_rls", self._cursor),
            patch.object(
                push_log_queries,
                "enable_managed_log_reader",
                side_effect=self._authorized_workspace,
            ),
        ):
            visible = push_log_queries.list_push_logs(
                ACTOR_B, tenant_id=TENANT, workspace_client_id=WORKSPACE
            )
            foreign_workspace = push_log_queries.list_push_logs(
                ACTOR_B, tenant_id=TENANT, workspace_client_id=OTHER_WORKSPACE
            )

        self.assertEqual([item["invoice_no"] for item in visible["items"]], ["M-1"])
        self.assertEqual(visible["total"], 1)
        self.assertEqual(foreign_workspace, {"items": [], "total": 0})

    def test_sales_enrichment_uses_same_managed_status_only_in_scope(self):
        in_scope = [
            {
                "ocr_history_id": MANAGED_HISTORY,
                "seller_workspace_client_id": WORKSPACE,
            }
        ]
        out_of_scope = [
            {
                "ocr_history_id": MANAGED_HISTORY,
                "seller_workspace_client_id": OTHER_WORKSPACE,
            }
        ]
        with patch.object(
            record_enrichment,
            "enable_managed_log_reader",
            side_effect=self._authorized_workspace,
        ):
            record_enrichment.enrich(self.cur, in_scope, tenant_id=TENANT, user_id=ACTOR_B)
            record_enrichment.enrich(self.cur, out_of_scope, tenant_id=TENANT, user_id=ACTOR_B)

        self.assertEqual(in_scope[0]["push_status"], "pending")
        self.assertEqual(in_scope[0]["push_endpoints"], [{"name": "Managed", "status": "pending"}])
        self.assertEqual(out_of_scope[0]["push_status"], "not_pushed")
        self.assertEqual(out_of_scope[0]["push_endpoints"], [])


if __name__ == "__main__":
    unittest.main()

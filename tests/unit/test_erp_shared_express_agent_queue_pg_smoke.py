"""Disposable PostgreSQL proof for managed Companion lease/ACK CAS."""

from __future__ import annotations

import hashlib
import json
import uuid
import unittest
from contextlib import contextmanager
from unittest import mock

from psycopg2.extras import RealDictCursor

from services.erp import shared_express_agent_queue as queue
from tests.unit._pg_smoke import connect_or_skip, require_disposable_db

TENANT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OWNER = "11111111-1111-4111-8111-111111111111"
ENDPOINT = "33333333-3333-4333-8333-333333333333"
OTHER_ENDPOINT = "44444444-4444-4444-8444-444444444444"
WORKSPACE = 101
OTHER_WORKSPACE = 102
HISTORY = "55555555-5555-4555-8555-555555555555"
LOG = "66666666-6666-4666-8666-666666666666"
OTHER_HISTORY = "77777777-7777-4777-8777-777777777777"
OTHER_LOG = "88888888-8888-4888-8888-888888888888"
TOKEN = f"exp_{ENDPOINT}_CompanionSecret_123"
OTHER_TOKEN = f"exp_{OTHER_ENDPOINT}_CompanionSecret_456"


class ManagedAgentQueuePgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.schema = f"smoke_managed_agent_{uuid.uuid4().hex[:10]}"
        cls.cur.execute(f'CREATE SCHEMA "{cls.schema}"')
        cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
        cls.cur.execute("""
            CREATE TABLE tenants (
              id uuid primary key, status text not null
            );
            CREATE TABLE workspace_clients (
              id bigint primary key, tenant_id uuid not null, is_active boolean not null
            );
            CREATE TABLE erp_endpoints (
              id uuid primary key, user_id uuid, adapter text not null, config jsonb not null,
              enabled boolean not null, shared_scope boolean not null, tenant_id uuid,
              workspace_client_id bigint, binding_generation bigint not null,
              bound_account_set text, bound_profile_key text, live_account_set text,
              live_profile_key text, agent_last_seen_at timestamptz, revoked_at timestamptz
            );
            CREATE TABLE ocr_history (
              id uuid primary key, last_push_status text, last_pushed_at timestamptz
            );
            CREATE TABLE erp_push_logs (
              id uuid primary key, user_id uuid not null, endpoint_id uuid,
              history_id uuid, invoice_no text, status text not null,
              http_status integer, request_body jsonb, response_body text, error_msg text,
              attempt integer not null default 1, created_at timestamptz not null default now(),
              lease_owner text, lease_expires_at timestamptz
            );
            """)
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.conn.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, "smoke_managed_agent_")
            cls.cur.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')
            cls.conn.commit()
        finally:
            cls.cur.close()
            cls.conn.close()

    def setUp(self):
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute(
            "TRUNCATE erp_push_logs, ocr_history, erp_endpoints, workspace_clients, tenants"
        )
        self.cur.execute("INSERT INTO tenants VALUES (%s, 'active')", (TENANT,))
        self.cur.execute(
            "INSERT INTO workspace_clients VALUES (%s, %s, TRUE), (%s, %s, TRUE)",
            (WORKSPACE, TENANT, OTHER_WORKSPACE, TENANT),
        )
        endpoint_rows = (
            (
                ENDPOINT,
                OWNER,
                json.dumps({"agent_token_hash": hashlib.sha256(TOKEN.encode()).hexdigest()}),
                TENANT,
                WORKSPACE,
            ),
            (
                OTHER_ENDPOINT,
                OWNER,
                json.dumps({"agent_token_hash": hashlib.sha256(OTHER_TOKEN.encode()).hexdigest()}),
                TENANT,
                OTHER_WORKSPACE,
            ),
        )
        self.cur.executemany(
            """
            INSERT INTO erp_endpoints (
              id,user_id,adapter,config,enabled,shared_scope,tenant_id,workspace_client_id,
              binding_generation,bound_account_set,bound_profile_key,live_account_set,
              live_profile_key,agent_last_seen_at,revoked_at
            ) VALUES (%s,%s,'express',%s::jsonb,TRUE,TRUE,%s,%s,2,
                      'datat','v1:key','datat','v1:key',clock_timestamp(),NULL)
            """,
            endpoint_rows,
        )
        self.cur.execute("INSERT INTO ocr_history VALUES (%s, 'pending', NULL)", (HISTORY,))
        self.cur.execute(
            """
            INSERT INTO erp_push_logs (
              id,user_id,endpoint_id,history_id,invoice_no,status,request_body,attempt
            ) VALUES (%s,%s,%s,%s,'RR-1','pending',%s::jsonb,1)
            """,
            (
                LOG,
                OWNER,
                ENDPOINT,
                HISTORY,
                json.dumps({"account_set": "DATAT", "meta": {"managed_generation": 2}}),
            ),
        )
        self.conn.commit()

    @contextmanager
    def _db_cursor(self, commit=False):
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(f'SET search_path TO "{self.schema}", public')
            yield cur
            if commit:
                self.conn.commit()
            else:
                self.conn.rollback()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def _row(self):
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute(
            "SELECT status,attempt,lease_owner,lease_expires_at FROM erp_push_logs WHERE id=%s",
            (LOG,),
        )
        return self.cur.fetchone()

    def test_lease_ack_stale_and_cross_endpoint(self):
        with mock.patch.object(queue.db, "get_cursor", side_effect=self._db_cursor):
            with mock.patch.object(
                queue, "erp_shared_express_endpoint_enabled_for", return_value=False
            ):
                blocked = queue.lease_managed(TOKEN, "comp-a", 1)
            self.assertEqual(blocked["jobs"], [])
            self.assertIsNone(self._row()["lease_owner"])

            with mock.patch.object(
                queue, "erp_shared_express_endpoint_enabled_for", return_value=True
            ):
                first = queue.lease_managed(TOKEN, "comp-a", 1)
            first_handle = first["jobs"][0]["log_id"]
            self.assertNotEqual(first_handle, LOG)
            self.assertEqual(self._row()["attempt"], 1)

            waiting = queue.ack_managed(
                TOKEN,
                first_handle,
                "comp-a",
                success=False,
                outcome="waiting_lock",
            )
            self.assertEqual((waiting["status"], waiting["attempt"]), ("pending", 2))

            with mock.patch.object(
                queue, "erp_shared_express_endpoint_enabled_for", return_value=True
            ):
                second = queue.lease_managed(TOKEN, "comp-a", 1)
            second_handle = second["jobs"][0]["log_id"]
            self.assertNotEqual(first_handle, second_handle)

            stale = queue.ack_managed(TOKEN, first_handle, "comp-a", success=True)
            self.assertEqual(stale, {"ok": False, "stale": True})
            cross = queue.ack_managed(OTHER_TOKEN, second_handle, "comp-a", success=True)
            self.assertEqual(cross, {"ok": False, "stale": True})
            self.assertEqual(self._row()["status"], "pending")

            with mock.patch.object(
                queue, "erp_shared_express_endpoint_enabled_for", return_value=False
            ) as enabled:
                success = queue.ack_managed(
                    TOKEN,
                    second_handle,
                    "comp-a",
                    success=True,
                    express_docnum="RR581231-002",
                )
            enabled.assert_not_called()
            self.assertEqual(success["status"], "success")

        row = self._row()
        self.assertEqual(row["status"], "success")
        self.assertIsNone(row["lease_owner"])
        self.cur.execute(
            f'SET search_path TO "{self.schema}", public; '
            "SELECT last_push_status FROM ocr_history WHERE id=%s",
            (HISTORY,),
        )
        self.assertEqual(self.cur.fetchone()["last_push_status"], "success")

    def test_same_companion_id_isolates_two_profiles_end_to_end(self):
        self.cur.execute(
            "UPDATE erp_endpoints SET bound_account_set='other', "
            "bound_profile_key='v1:other', live_account_set='other', "
            "live_profile_key='v1:other' WHERE id=%s",
            (OTHER_ENDPOINT,),
        )
        self.cur.execute(
            "INSERT INTO ocr_history VALUES (%s, 'pending', NULL)",
            (OTHER_HISTORY,),
        )
        self.cur.execute(
            """
            INSERT INTO erp_push_logs (
              id,user_id,endpoint_id,history_id,invoice_no,status,request_body,attempt
            ) VALUES (%s,%s,%s,%s,'RR-2','pending',%s::jsonb,1)
            """,
            (
                OTHER_LOG,
                OWNER,
                OTHER_ENDPOINT,
                OTHER_HISTORY,
                json.dumps({"account_set": "OTHER", "meta": {"managed_generation": 2}}),
            ),
        )
        self.conn.commit()

        companion_id = "comp-shared"
        with (
            mock.patch.object(queue.db, "get_cursor", side_effect=self._db_cursor),
            mock.patch.object(queue, "erp_shared_express_endpoint_enabled_for", return_value=True),
        ):
            first = queue.lease_managed(TOKEN, companion_id, 1)
            second = queue.lease_managed(OTHER_TOKEN, companion_id, 1)

            self.assertEqual([job["invoice_no"] for job in first["jobs"]], ["RR-1"])
            self.assertEqual([job["invoice_no"] for job in second["jobs"]], ["RR-2"])
            first_handle = first["jobs"][0]["log_id"]
            second_handle = second["jobs"][0]["log_id"]

            self.cur.execute(
                "SELECT id,status,attempt,lease_owner,lease_expires_at,http_status,"
                "response_body,error_msg FROM erp_push_logs "
                "WHERE id IN (%s,%s) ORDER BY id",
                (LOG, OTHER_LOG),
            )
            before_cross_ack = [dict(row) for row in self.cur.fetchall()]

            self.assertEqual(
                queue.ack_managed(OTHER_TOKEN, first_handle, companion_id, success=True),
                {"ok": False, "stale": True},
            )
            self.assertEqual(
                queue.ack_managed(TOKEN, second_handle, companion_id, success=True),
                {"ok": False, "stale": True},
            )

            self.cur.execute(
                "SELECT id,status,attempt,lease_owner,lease_expires_at,http_status,"
                "response_body,error_msg FROM erp_push_logs "
                "WHERE id IN (%s,%s) ORDER BY id",
                (LOG, OTHER_LOG),
            )
            after_cross_ack = [dict(row) for row in self.cur.fetchall()]
            self.assertEqual(after_cross_ack, before_cross_ack)

            first_ack = queue.ack_managed(
                TOKEN,
                first_handle,
                companion_id,
                success=True,
                express_docnum="RR-A",
            )
            second_ack = queue.ack_managed(
                OTHER_TOKEN,
                second_handle,
                companion_id,
                success=True,
                express_docnum="RR-B",
            )

        self.assertEqual(first_ack["express_docnum"], "RR-A")
        self.assertEqual(second_ack["express_docnum"], "RR-B")
        self.cur.execute(
            "SELECT endpoint_id,status,response_body FROM erp_push_logs "
            "WHERE id IN (%s,%s) ORDER BY endpoint_id",
            (LOG, OTHER_LOG),
        )
        rows = self.cur.fetchall()
        self.assertEqual([row["status"] for row in rows], ["success", "success"])
        self.assertEqual(
            [json.loads(row["response_body"])["express_docnum"] for row in rows],
            ["RR-A", "RR-B"],
        )
        self.cur.execute(
            "SELECT last_push_status FROM ocr_history " "WHERE id IN (%s,%s) ORDER BY id",
            (HISTORY, OTHER_HISTORY),
        )
        self.assertEqual(
            [row["last_push_status"] for row in self.cur.fetchall()],
            ["success", "success"],
        )


if __name__ == "__main__":
    unittest.main()

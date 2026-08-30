from __future__ import annotations

import json
import uuid
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import psycopg2
from psycopg2.extras import RealDictCursor

from services.erp import shared_express_push as service
from tests.unit._pg_smoke import connect_or_skip, LOCAL_DSN, require_disposable_db

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER_TENANT = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
ACTOR_A = "11111111-1111-4111-8111-111111111111"
ACTOR_B = "22222222-2222-4222-8222-222222222222"
FOREIGN_ACTOR = "99999999-9999-4999-8999-999999999999"
ENDPOINT = "33333333-3333-4333-8333-333333333333"
HISTORY = "44444444-4444-4444-8444-444444444444"
WORKSPACE = 101


class SharedExpressPushPgSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = connect_or_skip()
        cls.cur = cls.admin.cursor(cursor_factory=RealDictCursor)
        cls.schema = f"smoke_shared_push_{uuid.uuid4().hex[:12]}"
        cls.cur.execute(f'CREATE SCHEMA "{cls.schema}"')
        cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
        cls.cur.execute("""
            CREATE TABLE users (id uuid primary key, tenant_id uuid not null, is_active boolean not null);
            CREATE TABLE workspace_clients (
              id bigint primary key, tenant_id uuid not null, is_active boolean not null,
              erp_endpoint_id uuid, tax_id text, created_at timestamptz not null default now()
            );
            CREATE TABLE erp_endpoints (
              id uuid primary key, user_id uuid, name text not null, adapter text not null,
              config jsonb not null default '{}'::jsonb, is_default boolean not null default false,
              enabled boolean not null default true, shared_scope boolean not null default false,
              tenant_id uuid, workspace_client_id bigint, binding_generation bigint not null default 0,
              bound_account_set text, bound_profile_key text, live_account_set text, live_profile_key text,
              agent_last_seen_at timestamptz, revoked_at timestamptz, created_at timestamptz not null default now()
            );
            CREATE TABLE ocr_history (
              id uuid primary key, user_id uuid not null, tenant_id uuid not null,
              workspace_client_id bigint, staged boolean not null default false,
              filename text, page_count integer, confidence text, elapsed_ms integer, pages jsonb,
              invoice_no text, invoice_date date, seller_name text, total_amount numeric(18,2),
              archive_name text, category_tag text, fields_edited_at timestamptz, edit_count integer,
              created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
              client_id bigint, seller_name_official text, seller_name_verified boolean,
              posting_kind text, last_push_status text, last_pushed_at timestamptz
            );
            CREATE TABLE purchase_docs (
              id uuid primary key default gen_random_uuid(), tenant_id uuid not null,
              workspace_client_id bigint not null, created_by uuid, status text not null,
              ocr_history_id uuid
            );
            CREATE TABLE sales_documents (
              id uuid primary key default gen_random_uuid(), tenant_id uuid not null,
              seller_workspace_client_id bigint, created_by uuid, status text not null,
              ocr_history_id uuid
            );
            CREATE TABLE erp_push_logs (
              id uuid primary key default gen_random_uuid(), user_id uuid not null,
              endpoint_id uuid, history_id uuid, invoice_no text, seller_name text,
              total_amount numeric(18,2), status text not null, http_status integer,
              request_body jsonb, response_body text, error_msg text, attempt integer not null default 1,
              elapsed_ms integer, trigger text not null default 'manual', tenant_id uuid,
              workspace_client_id bigint, retry_count integer not null default 0,
              max_retries integer not null default 3, next_retry_at timestamptz,
              lease_owner text, lease_expires_at timestamptz,
              created_at timestamptz not null default now()
            );
            """)
        cls.admin.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.admin.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, "smoke_shared_push_")
            cls.cur.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')
            cls.admin.commit()
        finally:
            cls.cur.close()
            cls.admin.close()

    def setUp(self):
        self.admin.rollback()
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute(
            "TRUNCATE erp_push_logs, sales_documents, purchase_docs, ocr_history, "
            "erp_endpoints, workspace_clients, users"
        )
        self.cur.execute(
            "INSERT INTO users VALUES (%s,%s,TRUE),(%s,%s,TRUE),(%s,%s,TRUE)",
            (ACTOR_A, TENANT, ACTOR_B, TENANT, FOREIGN_ACTOR, OTHER_TENANT),
        )
        self.cur.execute(
            "INSERT INTO workspace_clients (id,tenant_id,is_active,erp_endpoint_id,tax_id) "
            "VALUES (%s,%s,TRUE,%s,'0105555555555')",
            (WORKSPACE, TENANT, ENDPOINT),
        )
        self.cur.execute(
            "INSERT INTO erp_endpoints "
            "(id,user_id,name,adapter,config,is_default,enabled,shared_scope,tenant_id,workspace_client_id,"
            "binding_generation,bound_account_set,bound_profile_key,live_account_set,live_profile_key,agent_last_seen_at) "
            "VALUES (%s,%s,'Shared Express','express',%s::jsonb,TRUE,TRUE,TRUE,%s,%s,3,'main','v1:key','main','v1:key',clock_timestamp())",
            (ENDPOINT, ACTOR_A, json.dumps({"directions": ["purchase"]}), TENANT, WORKSPACE),
        )
        self.cur.execute(
            "INSERT INTO ocr_history "
            "(id,user_id,tenant_id,workspace_client_id,filename,page_count,confidence,elapsed_ms,pages,"
            "invoice_no,invoice_date,seller_name,total_amount,edit_count,seller_name_verified) "
            "VALUES (%s,%s,%s,%s,'invoice.pdf',1,'high',5,'[]'::jsonb,'INV-1',current_date,'Supplier',100,0,FALSE)",
            (HISTORY, ACTOR_A, TENANT, WORKSPACE),
        )
        self.cur.execute(
            "INSERT INTO purchase_docs (tenant_id,workspace_client_id,created_by,status,ocr_history_id) "
            "VALUES (%s,%s,%s,'posted',%s)",
            (TENANT, WORKSPACE, ACTOR_A, HISTORY),
        )
        self.admin.commit()

    @contextmanager
    def _service_cursor(self, commit=False, **_context):
        connection = psycopg2.connect(LOCAL_DSN, connect_timeout=3)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f'SET search_path TO "{self.schema}", public')
        try:
            yield cursor
            if commit:
                connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def _authz(self):
        return SimpleNamespace(
            membership_id="membership",
            has=lambda _code: True,
            allows_workspace=lambda _workspace: True,
        )

    def _enqueue(self, _endpoint, _history, **_kwargs):
        payload = {
            "payload_version": 1,
            "direction": "purchase",
            "account_set": "main",
            "items": [{"code": "P1", "qty": 1}],
        }
        return {
            "success": False,
            "http_status": 202,
            "response_body": json.dumps({"queued": True}),
            "error_msg": "EXPRESS_QUEUED",
            "elapsed_ms": 1,
            "request_body": payload,
            "adapter": "express",
        }

    def _call(self, actor=ACTOR_A, tenant=TENANT):
        with (
            patch.object(service.db, "get_cursor_rls", self._service_cursor),
            patch.object(service, "erp_shared_express_endpoint_enabled_for", return_value=True),
            patch.object(service, "enable_shared_express_select", return_value=True),
            patch.object(service, "resolve", return_value=self._authz()),
            patch.object(service, "enqueue_express", side_effect=self._enqueue),
        ):
            return service.reserve_managed_manual_push(
                user={"id": actor, "tenant_id": tenant, "entry": "cowork"},
                history_id=HISTORY,
                endpoint_id=ENDPOINT,
                requested_workspace_id=WORKSPACE,
                posting_kind="service",
            )

    def test_cross_actor_reuse_rollback_and_cross_tenant_are_atomic(self):
        first = self._call(ACTOR_A)
        second = self._call(ACTOR_B)
        self.assertTrue(first["queued"])
        self.assertEqual(second["log_id"], first["log_id"])
        self.assertTrue(second["reused"])
        self.cur.execute("SELECT user_id::text,request_body,status FROM erp_push_logs")
        row = self.cur.fetchone()
        self.assertEqual(row["user_id"], ACTOR_A)
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["request_body"]["managed_generation"], 3)
        self.assertEqual(row["request_body"]["items"], [{"code": "P1", "qty": 1}])

        self.cur.execute(
            "UPDATE erp_push_logs SET status='success',http_status=200 WHERE id=%s",
            (first["log_id"],),
        )
        self.admin.commit()
        duplicate = self._call(ACTOR_B)
        self.assertEqual(duplicate["log_id"], first["log_id"])
        self.assertEqual(duplicate["status"], "skipped_dup")
        self.assertFalse(duplicate["queued"])
        self.cur.execute("SELECT count(*) AS n FROM erp_push_logs")
        self.assertEqual(self.cur.fetchone()["n"], 1)

        self.cur.execute("DELETE FROM erp_push_logs")
        self.cur.execute(
            "UPDATE ocr_history SET last_push_status='success',last_pushed_at=clock_timestamp() WHERE id=%s",
            (HISTORY,),
        )
        self.cur.execute(
            "CREATE FUNCTION fail_shared_push_insert() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'forced insert failure'; END $$"
        )
        self.cur.execute(
            "CREATE TRIGGER fail_shared_push_insert BEFORE INSERT ON erp_push_logs "
            "FOR EACH ROW EXECUTE FUNCTION fail_shared_push_insert()"
        )
        self.admin.commit()
        with self.assertRaises(Exception):
            self._call(ACTOR_A)
        self.cur.execute("SELECT last_push_status FROM ocr_history WHERE id=%s", (HISTORY,))
        self.assertEqual(self.cur.fetchone()["last_push_status"], "success")
        self.cur.execute("SELECT count(*) AS n FROM erp_push_logs")
        self.assertEqual(self.cur.fetchone()["n"], 0)
        self.cur.execute("DROP TRIGGER fail_shared_push_insert ON erp_push_logs")
        self.cur.execute("DROP FUNCTION fail_shared_push_insert()")
        self.admin.commit()

        self.assertIsNone(self._call(FOREIGN_ACTOR, OTHER_TENANT))
        self.cur.execute("SELECT count(*) AS n FROM erp_push_logs")
        self.assertEqual(self.cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main()

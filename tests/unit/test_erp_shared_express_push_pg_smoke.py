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
from services.cowork_line import push_reservation as cowork_reservation
from tests.unit._pg_smoke import connect_or_skip, LOCAL_DSN, require_disposable_db

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER_TENANT = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
ACTOR_A = "11111111-1111-4111-8111-111111111111"
ACTOR_B = "22222222-2222-4222-8222-222222222222"
FOREIGN_ACTOR = "99999999-9999-4999-8999-999999999999"
ENDPOINT = "33333333-3333-4333-8333-333333333333"
HISTORY = "44444444-4444-4444-8444-444444444444"
WORKSPACE = 101
SNAPSHOT = "55555555-5555-4555-8555-555555555555"
SECOND_ACCOUNT = r"S:\70EXP\TEST2020"


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
              auto_push boolean not null default false, last_used_at timestamptz, last_status text,
              success_count integer not null default 0, failure_count integer not null default 0,
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
            CREATE TABLE erp_target_projection_snapshots (
              id uuid primary key, source_hash text not null, observed_at timestamptz not null,
              adapter text not null, collector jsonb not null, account_sets jsonb not null,
              form_schema jsonb not null, capabilities jsonb not null, entity_counts jsonb not null
            );
            CREATE TABLE erp_target_projection_heads (
              tenant_id uuid not null, endpoint_id uuid not null, scope_kind text not null,
              scope_key text not null, current_snapshot_id uuid, current_revision bigint not null,
              account_sets_revision bigint not null, master_revision bigint not null,
              form_schema_revision bigint not null, capability_revision bigint not null,
              last_refresh_status text not null, last_refresh_error_code text,
              last_refresh_source jsonb not null, last_refresh_attempted_at timestamptz,
              last_observed_at timestamptz, updated_at timestamptz not null default now()
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
            "TRUNCATE erp_target_projection_heads, erp_target_projection_snapshots, "
            "erp_push_logs, sales_documents, purchase_docs, ocr_history, "
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
        account_sets = [
            {
                "source_id": "main",
                "label": "TEST2019",
                "active": True,
                "attributes": {"path": "main", "writable": True},
            },
            {
                "source_id": SECOND_ACCOUNT.lower(),
                "label": "TEST2020",
                "active": True,
                "attributes": {"path": SECOND_ACCOUNT, "writable": True},
            },
        ]
        self.cur.execute(
            "INSERT INTO erp_target_projection_snapshots "
            "(id,source_hash,observed_at,adapter,collector,account_sets,form_schema,capabilities,entity_counts) "
            "VALUES (%s,'hash',clock_timestamp(),'express','{}',%s::jsonb,'{}','{}','{}')",
            (SNAPSHOT, json.dumps(account_sets)),
        )
        self.cur.execute(
            "INSERT INTO erp_target_projection_heads "
            "(tenant_id,endpoint_id,scope_kind,scope_key,current_snapshot_id,current_revision,"
            "account_sets_revision,master_revision,form_schema_revision,capability_revision,"
            "last_refresh_status,last_refresh_source,last_refresh_attempted_at,last_observed_at) "
            "VALUES (%s,%s,'endpoint','@endpoint',%s,1,1,1,1,1,'fresh','{}',"
            "clock_timestamp(),clock_timestamp())",
            (TENANT, ENDPOINT, SNAPSHOT),
        )
        self.cur.execute(
            "INSERT INTO ocr_history "
            "(id,user_id,tenant_id,workspace_client_id,filename,page_count,confidence,elapsed_ms,pages,"
            "invoice_no,invoice_date,seller_name,total_amount,edit_count,seller_name_verified) "
            "VALUES (%s,%s,%s,%s,'invoice.pdf',1,'high',5,'[{\"fields\":{\"direction\":\"purchase\"}}]'::jsonb,"
            "'INV-1',current_date,'Supplier',100,0,FALSE)",
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
        config = _endpoint.get("config") or {}
        payload = {
            "payload_version": 1,
            "direction": "purchase",
            "account_set": config.get("account_set") or "main",
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

    def _call(self, actor=ACTOR_A, tenant=TENANT, account_set_key=None):
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
                account_set_key=account_set_key,
            )

    def _call_cowork_batch(self, account_set_key=None):
        with (
            patch.object(cowork_reservation.db, "get_cursor_rls", self._service_cursor),
            patch.object(
                cowork_reservation,
                "erp_shared_express_endpoint_enabled_for",
                return_value=True,
            ),
            patch.object(cowork_reservation, "enable_shared_express_select", return_value=True),
            patch.object(cowork_reservation, "_active_actor", return_value=self._authz()),
            patch.object(cowork_reservation, "enqueue_express", side_effect=self._enqueue),
        ):
            return cowork_reservation.reserve_managed_batch(
                {
                    "user_id": ACTOR_A,
                    "tenant_id": TENANT,
                    "membership_id": "membership",
                },
                [HISTORY],
                {
                    "endpoint_id": ENDPOINT,
                    "workspace_client_id": WORKSPACE,
                    "adapter": "express",
                },
                posting_kind="service",
                account_set_key=account_set_key,
                account_config=(
                    {
                        "account_set": SECOND_ACCOUNT.lower(),
                        "account_dir": SECOND_ACCOUNT,
                    }
                    if account_set_key
                    else None
                ),
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

    def test_selected_account_is_persisted_without_overwriting_the_bound_default(self):
        result = self._call(account_set_key=SECOND_ACCOUNT)

        self.assertTrue(result["queued"])
        self.cur.execute("SELECT request_body FROM erp_push_logs WHERE id=%s", (result["log_id"],))
        self.assertEqual(self.cur.fetchone()["request_body"]["account_set"], SECOND_ACCOUNT.lower())
        self.cur.execute(
            "SELECT bound_account_set,config FROM erp_endpoints WHERE id=%s", (ENDPOINT,)
        )
        endpoint = self.cur.fetchone()
        self.assertEqual(endpoint["bound_account_set"], "main")
        self.assertNotIn("account_set", endpoint["config"])

    def test_cowork_confirmation_and_pending_log_commit_or_rollback_together(self):
        self.cur.execute("UPDATE ocr_history SET staged=TRUE WHERE id=%s", (HISTORY,))
        self.admin.commit()

        result = self._call_cowork_batch()
        self.assertEqual(result[0]["status"], "pending")
        self.cur.execute("SELECT staged,last_push_status FROM ocr_history WHERE id=%s", (HISTORY,))
        history = self.cur.fetchone()
        self.assertFalse(history["staged"])
        self.assertEqual(history["last_push_status"], "pending")
        self.cur.execute("SELECT count(*) AS n FROM erp_push_logs WHERE history_id=%s", (HISTORY,))
        self.assertEqual(self.cur.fetchone()["n"], 1)

        self.cur.execute("DELETE FROM erp_push_logs")
        self.cur.execute(
            "UPDATE ocr_history SET staged=TRUE,last_push_status=NULL WHERE id=%s", (HISTORY,)
        )
        self.cur.execute(
            "CREATE FUNCTION fail_cowork_push_insert() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'forced insert failure'; END $$"
        )
        self.cur.execute(
            "CREATE TRIGGER fail_cowork_push_insert BEFORE INSERT ON erp_push_logs "
            "FOR EACH ROW EXECUTE FUNCTION fail_cowork_push_insert()"
        )
        self.admin.commit()
        with self.assertRaises(Exception):
            self._call_cowork_batch()
        self.cur.execute("SELECT staged,last_push_status FROM ocr_history WHERE id=%s", (HISTORY,))
        rolled_back = self.cur.fetchone()
        self.assertTrue(rolled_back["staged"])
        self.assertIsNone(rolled_back["last_push_status"])
        self.cur.execute("SELECT count(*) AS n FROM erp_push_logs")
        self.assertEqual(self.cur.fetchone()["n"], 0)
        self.cur.execute("DROP TRIGGER fail_cowork_push_insert ON erp_push_logs")
        self.cur.execute("DROP FUNCTION fail_cowork_push_insert()")
        self.admin.commit()

    def test_cowork_selected_account_is_kept_in_the_managed_queue(self):
        self.cur.execute("UPDATE ocr_history SET staged=TRUE WHERE id=%s", (HISTORY,))
        self.admin.commit()

        result = self._call_cowork_batch(SECOND_ACCOUNT)

        self.assertEqual(result[0]["status"], "pending")
        self.cur.execute("SELECT request_body FROM erp_push_logs WHERE history_id=%s", (HISTORY,))
        self.assertEqual(self.cur.fetchone()["request_body"]["account_set"], SECOND_ACCOUNT.lower())

    def test_cowork_mrerp_reserves_before_send_and_finalizes_the_same_log(self):
        self.cur.execute(
            "UPDATE erp_endpoints SET adapter='mrerp',shared_scope=FALSE,binding_generation=0,"
            'config=\'{"username":"u","password":"p"}\'::jsonb WHERE id=%s',
            (ENDPOINT,),
        )
        self.cur.execute("UPDATE ocr_history SET staged=TRUE WHERE id=%s", (HISTORY,))
        self.admin.commit()
        identity = {
            "user_id": ACTOR_A,
            "tenant_id": TENANT,
            "membership_id": "membership",
        }
        target = {
            "endpoint_id": ENDPOINT,
            "workspace_client_id": WORKSPACE,
            "adapter": "mrerp",
        }
        with (
            patch.object(cowork_reservation.db, "get_cursor_rls", self._service_cursor),
            patch.object(cowork_reservation, "_active_actor", return_value=self._authz()),
        ):
            endpoint, intents = cowork_reservation.reserve_legacy_batch(identity, [HISTORY], target)

        self.assertEqual(intents[0]["status"], "retrying")
        self.cur.execute("SELECT staged,last_push_status FROM ocr_history WHERE id=%s", (HISTORY,))
        confirmed = self.cur.fetchone()
        self.assertFalse(confirmed["staged"])
        self.assertEqual(confirmed["last_push_status"], "retrying")
        self.cur.execute("SELECT id::text,status FROM erp_push_logs")
        reserved = self.cur.fetchone()
        self.assertEqual(reserved["id"], intents[0]["log_id"])
        self.assertEqual(reserved["status"], "retrying")

        result = {
            "success": True,
            "http_status": 200,
            "request_body": {"invoice": "INV-1"},
            "response_body": "ok",
            "error_msg": None,
            "elapsed_ms": 8,
        }
        with patch.object(cowork_reservation.db, "get_cursor_rls", self._service_cursor):
            finalized = cowork_reservation.finalize_legacy_intent(
                identity, endpoint, intents[0], result
            )
        self.assertTrue(finalized)
        self.cur.execute("SELECT id::text,status,lease_owner FROM erp_push_logs")
        final_log = self.cur.fetchone()
        self.assertEqual(final_log["id"], reserved["id"])
        self.assertEqual(final_log["status"], "success")
        self.assertIsNone(final_log["lease_owner"])
        self.cur.execute("SELECT success_count FROM erp_endpoints WHERE id=%s", (ENDPOINT,))
        self.assertEqual(self.cur.fetchone()["success_count"], 1)


if __name__ == "__main__":
    unittest.main()

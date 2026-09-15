"""Exercise credential GET/PUT against PostgreSQL with tenant/user RLS enabled."""

from contextlib import contextmanager
import os
import sys
import importlib.util
from pathlib import Path
from cryptography.fernet import Fernet
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import db
from core.pos_api import register_pos_error_handler
from routes import line_dms_credentials_routes as routes
from services.erp import push_store
from services.line_dms import binding_guard, schema, store
from tests.unit._pg_smoke import require_disposable_db


class CredentialRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ.get("PEARNLY_DMS_BINDING_TEST_DSN", "")
        if not cls.dsn:
            raise unittest.SkipTest("explicit disposable DMS binding DSN required")
        parsed = urlsplit(cls.dsn)
        if (
            parsed.hostname not in {"localhost", "127.0.0.1"}
            or parsed.path != "/pearnly_ci_dms_binding"
        ):
            raise RuntimeError("refusing non-disposable credentials database")
        suffix = uuid4().hex
        cls.schema, cls.role = "dms_credentials_test_" + suffix, "dms_credentials_role_" + suffix
        with psycopg2.connect(cls.dsn) as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
            cur.execute(
                sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS").format(
                    sql.Identifier(cls.role)
                )
            )
        with cls.cursor(commit=True) as cur:
            cur.execute(schema._BINDINGS)
            cur.execute(
                "CREATE TABLE erp_endpoints (id uuid PRIMARY KEY, user_id uuid, name text, adapter text, "
                "config jsonb, binding_generation integer DEFAULT 0, enabled boolean DEFAULT true, "
                "is_default boolean DEFAULT false, auto_push boolean DEFAULT false, last_used_at timestamptz, "
                "last_status text, success_count integer DEFAULT 0, failure_count integer DEFAULT 0, "
                "created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now())"
            )
            cur.execute(
                "CREATE TABLE workspace_clients (id uuid PRIMARY KEY, erp_endpoint_id uuid, is_active boolean)"
            )
            cur.execute("ALTER TABLE line_dms_bindings ENABLE ROW LEVEL SECURITY")
            cur.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
            cur.execute(
                "CREATE POLICY binding_tenant ON line_dms_bindings USING "
                "(tenant_id::text = current_setting('app.current_tenant_id',true))"
            )
            cur.execute(
                "CREATE POLICY endpoint_user ON erp_endpoints USING "
                "(user_id::text = current_setting('app.current_user_id',true))"
            )
            cur.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(cls.schema), sql.Identifier(cls.role)
                )
            )
            cur.execute(
                sql.SQL("GRANT SELECT,UPDATE ON ALL TABLES IN SCHEMA {} TO {}").format(
                    sql.Identifier(cls.schema), sql.Identifier(cls.role)
                )
            )

    @classmethod
    @contextmanager
    def cursor(cls, commit=False):
        conn = psycopg2.connect(cls.dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(cls.schema))
                )
                yield cur
                if commit:
                    conn.commit()
        finally:
            conn.close()

    @classmethod
    @contextmanager
    def rls_cursor(cls, tenant_id=None, *, user_id=None, commit=False, **kwargs):
        with cls.cursor(commit=commit) as cur:
            cur.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(cls.role)))
            if tenant_id:
                cur.execute("SET LOCAL app.current_tenant_id=%s", (str(tenant_id),))
            if user_id:
                cur.execute("SET LOCAL app.current_user_id=%s", (str(user_id),))
            yield cur

    @classmethod
    def tearDownClass(cls):
        with cls.cursor(commit=True) as cur:
            require_disposable_db(cur, cls.schema, "dms_credentials_test_")
            cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))
            cur.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(cls.role)))

    def setUp(self):
        self.tenant, self.user_id, self.other_id, self.endpoint, self.other_endpoint = [
            str(uuid4()) for _ in range(5)
        ]
        self.line = "line-" + uuid4().hex
        with self.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO line_dms_bindings(line_user_id,tenant_id,user_id) VALUES (%s,%s,%s)",
                (self.line, self.tenant, self.user_id),
            )
            for endpoint, user_id in (
                (self.endpoint, self.user_id),
                (self.other_endpoint, self.other_id),
            ):
                cur.execute(
                    "INSERT INTO erp_endpoints(id,user_id,name,adapter,config) VALUES (%s,%s,'test','mrerp_dms',%s::jsonb)",
                    (endpoint, user_id, '{"username":"test-sale","password":"old-dms-password"}'),
                )
        self.enterContext(patch.object(db, "get_cursor", self.cursor))
        self.enterContext(patch.object(db, "get_cursor_rls", self.rls_cursor))
        self.user = {
            "id": self.user_id,
            "tenant_id": self.tenant,
            "role": "member",
            "is_active": True,
        }
        self.binding = store.get_binding_by_line_user(self.line)
        self.enterContext(patch.object(db, "find_user_by_id", return_value=self.user))
        self.enterContext(
            patch("services.dms_roster.store.get_profile", return_value={"status": "active"})
        )
        self.enterContext(patch("routes.dms_routes._authorize", return_value=self.user))
        self.enterContext(patch.object(routes, "dms_line_enabled_for", return_value=True))
        self.enterContext(
            patch(
                "core.auth.decode_access_token",
                return_value={
                    "sub": self.user_id,
                    "entry": "dms",
                    "typ": "access",
                    "dms_binding": self.binding,
                },
            )
        )
        spec = importlib.util.spec_from_file_location(
            "core.kms_helper", Path(__file__).resolve().parents[2] / "core/kms_helper.py"
        )
        self.kms = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {"PEARNLY_KMS_KEY": Fernet.generate_key().decode()}):
            spec.loader.exec_module(self.kms)
        self.enterContext(patch.dict(sys.modules, {"core.kms_helper": self.kms}))
        app = FastAPI()
        app.include_router(routes.router)
        register_pos_error_handler(app)
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer signed-test-binding"}

    def config(self, endpoint):
        with self.cursor() as cur:
            cur.execute("SELECT config FROM erp_endpoints WHERE id=%s", (endpoint,))
            return cur.fetchone()["config"]

    def test_binding_is_hidden_without_tenant_context(self):
        with self.rls_cursor(user_id=self.user_id) as cur:
            cur.execute("SELECT id FROM line_dms_bindings WHERE line_user_id=%s", (self.line,))
            self.assertIsNone(cur.fetchone())
        with self.rls_cursor(self.tenant, user_id=self.user_id) as cur:
            cur.execute("SELECT id FROM line_dms_bindings WHERE line_user_id=%s", (self.line,))
            self.assertIsNotNone(cur.fetchone())

    def test_real_http_save_and_readback_under_rls(self):
        original_other = self.config(self.other_endpoint)
        self.assertEqual(
            self.client.get("/api/line/dms-credentials", headers=self.headers).status_code, 200
        )
        response = self.client.put(
            "/api/line/dms-credentials",
            headers=self.headers,
            json={"username": "updated-sale", "password": "new-dms-password"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["data"]["updated"])
        cfg = self.config(self.endpoint)
        self.assertEqual(self.kms.decrypt_str(cfg["password_enc"]), "new-dms-password")
        self.assertNotIn("password", cfg)
        readback = self.client.get("/api/line/dms-credentials", headers=self.headers)
        self.assertEqual(readback.json()["data"], {"username": "updated-sale"})
        self.assertEqual(self.config(self.other_endpoint), original_other)

    def test_rebind_after_load_rejects_save_without_changing_either_account(self):
        originals = [self.config(self.endpoint), self.config(self.other_endpoint)]
        self.assertEqual(
            self.client.get("/api/line/dms-credentials", headers=self.headers).status_code, 200
        )
        with self.cursor(commit=True) as cur:
            cur.execute(
                "UPDATE line_dms_bindings SET id=gen_random_uuid() WHERE line_user_id=%s",
                (self.line,),
            )
        response = self.client.put(
            "/api/line/dms-credentials",
            headers=self.headers,
            json={"username": "wrong-account", "password": "do-not-write"},
        )
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual([self.config(self.endpoint), self.config(self.other_endpoint)], originals)

    def test_binding_cannot_write_another_user_endpoint(self):
        original = self.config(self.other_endpoint)
        with binding_guard.scope(self.binding):
            self.assertFalse(
                push_store.update_erp_endpoint(
                    self.other_id, self.other_endpoint, config={"bad": True}
                )
            )
        self.assertEqual(self.config(self.other_endpoint), original)

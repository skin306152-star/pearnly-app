# -*- coding: utf-8 -*-
"""F1-B1 migration, index and dormant RLS contracts on disposable PostgreSQL state."""

from __future__ import annotations

import importlib.util
import unittest
import uuid
from pathlib import Path
from unittest import mock

from core import rls
from services.erp import shared_express_managed_schema
from services.erp import shared_express_schema
from tests.unit._pg_smoke import connect_or_skip

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "0108_erp_shared_express_foundation.py"

TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
OWNER = "11111111-1111-1111-1111-111111111111"
EMPLOYEE = "22222222-2222-2222-2222-222222222222"
EXPRESS_ENDPOINT = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0001"
MRERP_ENDPOINT = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0002"
DISABLED_ENDPOINT = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0003"
PRIVATE_ENDPOINT = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0004"
EXPRESS_LOG = "dddddddd-dddd-dddd-dddd-dddddddd0001"
MRERP_LOG = "dddddddd-dddd-dddd-dddd-dddddddd0002"
DISABLED_LOG = "dddddddd-dddd-dddd-dddd-dddddddd0003"
PRIVATE_LOG = "dddddddd-dddd-dddd-dddd-dddddddd0004"
WORKSPACE_A = 101
WORKSPACE_B = 202


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_0108_pg_smoke", MIGRATION)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


class SharedExpressPgSmokeTests(unittest.TestCase):
    conn = None
    cur = None

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        cls._previous_managed_ready = shared_express_managed_schema._MANAGED_FOUNDATION_READY
        shared_express_managed_schema._MANAGED_FOUNDATION_READY = True
        from psycopg2.extras import RealDictCursor

        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        try:
            rls.ensure_rls_app_role(cls.cur)
            cls.conn.commit()
            cls.cur.execute("SET search_path TO pg_temp, public")
            cls.cur.execute(
                "CREATE TEMP TABLE erp_endpoints ("
                "id UUID PRIMARY KEY, user_id UUID NOT NULL, tenant_id UUID, "
                "adapter TEXT NOT NULL, enabled BOOLEAN NOT NULL DEFAULT TRUE)"
            )
            cls.cur.execute(
                "CREATE TEMP TABLE erp_push_logs ("
                "id UUID PRIMARY KEY, user_id UUID NOT NULL, tenant_id UUID, endpoint_id UUID)"
            )
            cls.cur.execute("SELECT current_schema() AS schema")
            cls.schema = cls.cur.fetchone()["schema"]
            rls.apply_user_rls(cls.cur, "erp_endpoints", "erp_push_logs")

            migration = _load_migration()
            for statement in migration._DDL:
                cls.cur.execute(statement)
            shared_express_schema.apply_shared_express_foundation(cls.cur)

            cls.cur.execute(f'GRANT USAGE ON SCHEMA "{cls.schema}" TO {rls.RLS_APP_ROLE}')
            cls.cur.execute(
                f'GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA "{cls.schema}" '
                f"TO {rls.RLS_APP_ROLE}"
            )
            cls.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
            cls.cur.execute("ALTER TABLE erp_push_logs FORCE ROW LEVEL SECURITY")
            cls.conn.commit()
        except Exception:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = cls._previous_managed_ready
            cls.conn.rollback()
            cls.cur.close()
            cls.conn.close()
            cls.cur = None
            cls.conn = None
            raise

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = cls._previous_managed_ready
            return
        shared_express_managed_schema._MANAGED_FOUNDATION_READY = cls._previous_managed_ready
        cls.conn.rollback()
        cls.cur.close()
        cls.conn.close()

    def _seed(self):
        self.cur.execute(
            "INSERT INTO erp_endpoints "
            "(id,user_id,tenant_id,workspace_client_id,adapter,enabled,shared_scope) "
            "VALUES (%s,%s,%s,%s,'express',TRUE,TRUE),"
            "(%s,%s,%s,%s,'mrerp',TRUE,TRUE),"
            "(%s,%s,%s,%s,'express',FALSE,TRUE),"
            "(%s,%s,%s,%s,'express',TRUE,FALSE)",
            (
                EXPRESS_ENDPOINT,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                MRERP_ENDPOINT,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                DISABLED_ENDPOINT,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                PRIVATE_ENDPOINT,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
            ),
        )
        self.cur.execute(
            "INSERT INTO erp_push_logs "
            "(id,user_id,tenant_id,workspace_client_id,endpoint_id) "
            "VALUES (%s,%s,%s,%s,%s),(%s,%s,%s,%s,%s),"
            "(%s,%s,%s,%s,%s),(%s,%s,%s,%s,%s)",
            (
                EXPRESS_LOG,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                EXPRESS_ENDPOINT,
                MRERP_LOG,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                MRERP_ENDPOINT,
                DISABLED_LOG,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                DISABLED_ENDPOINT,
                PRIVATE_LOG,
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                PRIVATE_ENDPOINT,
            ),
        )

    def _employee_context(self, tenant=TENANT_A, workspace=WORKSPACE_A):
        self.cur.execute(f"SET LOCAL ROLE {rls.RLS_APP_ROLE}")
        self.cur.execute("SET LOCAL app.current_user_id = %s", (EMPLOYEE,))
        self.cur.execute("SET LOCAL app.current_tenant_id = %s", (tenant,))
        self.cur.execute("SET LOCAL app.current_workspace_id = %s", (str(workspace),))

    def test_migration_startup_index_and_rls_contract(self):
        import psycopg2

        self._seed()
        shared_express_schema.apply_shared_express_foundation(self.cur)

        self.cur.execute(
            "SELECT table_name, column_name, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name IN ('erp_endpoints','erp_push_logs') "
            "AND column_name IN ('workspace_client_id','shared_scope')",
            (self.schema,),
        )
        columns = {(row["table_name"], row["column_name"]): row for row in self.cur.fetchall()}
        self.assertEqual(columns[("erp_endpoints", "workspace_client_id")]["is_nullable"], "YES")
        self.assertEqual(columns[("erp_push_logs", "workspace_client_id")]["is_nullable"], "YES")
        shared_scope = columns[("erp_endpoints", "shared_scope")]
        self.assertEqual(shared_scope["is_nullable"], "NO")
        self.assertIn("false", shared_scope["column_default"].lower())

        self.cur.execute(
            "SELECT tablename, policyname, cmd FROM pg_policies "
            "WHERE schemaname = %s ORDER BY tablename, policyname",
            (self.schema,),
        )
        policies = {
            (row["tablename"], row["policyname"]): row["cmd"] for row in self.cur.fetchall()
        }
        self.assertEqual(policies[("erp_endpoints", "tenant_isolation")], "ALL")
        self.assertEqual(policies[("erp_push_logs", "tenant_isolation")], "ALL")
        self.assertEqual(
            policies[("erp_endpoints", "erp_endpoints_shared_express_select")], "SELECT"
        )
        self.assertEqual(
            policies[("erp_push_logs", "erp_push_logs_shared_express_select")], "SELECT"
        )

        self.cur.execute(
            "SELECT pg_get_indexdef(indexrelid) AS definition, "
            "pg_get_expr(indpred, indrelid) AS predicate, "
            "indisvalid, indisready, indislive "
            "FROM pg_index WHERE indexrelid = %s::regclass",
            (shared_express_schema.SHARED_EXPRESS_INDEX,),
        )
        index = self.cur.fetchone()
        self.assertTrue(index["indisvalid"])
        self.assertTrue(index["indisready"])
        self.assertTrue(index["indislive"])
        self.assertIn("(tenant_id, workspace_client_id, adapter)", index["definition"])
        for fragment in ("enabled", "shared_scope", "express", "tenant_id", "workspace_client_id"):
            self.assertIn(fragment, index["predicate"])

        self.cur.execute("SAVEPOINT wrong_same_name_index")
        self.cur.execute(f"DROP INDEX {shared_express_schema.SHARED_EXPRESS_INDEX}")
        self.cur.execute(
            f"CREATE UNIQUE INDEX {shared_express_schema.SHARED_EXPRESS_INDEX} "
            "ON erp_endpoints (tenant_id) "
            "WHERE enabled = TRUE AND shared_scope = TRUE AND adapter = 'express'"
        )
        with self.assertRaisesRegex(
            psycopg2.Error, "does not match the F1 shared Express contract"
        ):
            shared_express_schema.apply_shared_express_foundation(self.cur)
        self.cur.execute("ROLLBACK TO SAVEPOINT wrong_same_name_index")
        self.cur.execute("RELEASE SAVEPOINT wrong_same_name_index")

        self.cur.execute(
            "SELECT adapter FROM erp_endpoints WHERE id IN (%s,%s) ORDER BY adapter",
            (EXPRESS_ENDPOINT, MRERP_ENDPOINT),
        )
        self.assertEqual([row["adapter"] for row in self.cur.fetchall()], ["express", "mrerp"])

        self.cur.execute("SAVEPOINT duplicate_active_shared")
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.cur.execute(
                "INSERT INTO erp_endpoints "
                "(id,user_id,tenant_id,workspace_client_id,adapter,enabled,shared_scope) "
                "VALUES (%s,%s,%s,%s,'express',TRUE,TRUE)",
                (str(uuid.uuid4()), EMPLOYEE, TENANT_A, WORKSPACE_A),
            )
        self.cur.execute("ROLLBACK TO SAVEPOINT duplicate_active_shared")
        self.cur.execute("RELEASE SAVEPOINT duplicate_active_shared")

        for tenant, workspace, enabled, shared in (
            (TENANT_A, WORKSPACE_A, False, True),
            (TENANT_A, WORKSPACE_A, True, False),
            (TENANT_A, WORKSPACE_B, True, True),
            (TENANT_B, WORKSPACE_A, True, True),
        ):
            self.cur.execute(
                "INSERT INTO erp_endpoints "
                "(id,user_id,tenant_id,workspace_client_id,adapter,enabled,shared_scope) "
                "VALUES (%s,%s,%s,%s,'express',%s,%s)",
                (str(uuid.uuid4()), OWNER, tenant, workspace, enabled, shared),
            )
        self.conn.commit()

        self._employee_context()
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ):
            self.assertFalse(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, None)
            )
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual(self.cur.fetchall(), [])
        self.conn.rollback()

        self.cur.execute(f"SET LOCAL ROLE {rls.RLS_APP_ROLE}")
        self.cur.execute("SET LOCAL app.current_user_id = %s", (EMPLOYEE,))
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ):
            self.assertFalse(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, WORKSPACE_A)
            )
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual(self.cur.fetchall(), [])
        self.conn.rollback()

        self._employee_context(TENANT_B, WORKSPACE_A)
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ):
            self.assertFalse(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, WORKSPACE_A)
            )
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual(self.cur.fetchall(), [])
        self.conn.rollback()

        self._employee_context()
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=False,
        ):
            self.assertFalse(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, WORKSPACE_A)
            )
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual(self.cur.fetchall(), [])
        self.conn.rollback()

        self._employee_context()
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ):
            self.assertTrue(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, WORKSPACE_A)
            )
        self.cur.execute("SELECT id FROM erp_endpoints ORDER BY id")
        self.assertEqual([str(row["id"]) for row in self.cur.fetchall()], [EXPRESS_ENDPOINT])
        self.cur.execute("SELECT endpoint_id FROM erp_push_logs")
        self.assertEqual(
            [str(row["endpoint_id"]) for row in self.cur.fetchall()], [EXPRESS_ENDPOINT]
        )

        self.cur.execute("SET LOCAL app.current_workspace_id = %s", (str(WORKSPACE_B),))
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual(self.cur.fetchall(), [])
        self.cur.execute("SET LOCAL app.current_workspace_id = %s", (str(WORKSPACE_A),))
        self.cur.execute("SET LOCAL app.current_tenant_id = %s", (TENANT_B,))
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual(self.cur.fetchall(), [])
        self.cur.execute("SET LOCAL app.current_tenant_id = %s", (TENANT_A,))

        self.cur.execute(
            "UPDATE erp_endpoints SET enabled = FALSE WHERE id = %s", (EXPRESS_ENDPOINT,)
        )
        self.assertEqual(self.cur.rowcount, 0)

        self.cur.execute("SAVEPOINT forged_creator")
        with self.assertRaises(psycopg2.Error):
            self.cur.execute(
                "INSERT INTO erp_endpoints "
                "(id,user_id,tenant_id,workspace_client_id,adapter,enabled,shared_scope) "
                "VALUES (%s,%s,%s,%s,'express',TRUE,FALSE)",
                (str(uuid.uuid4()), OWNER, TENANT_A, WORKSPACE_A),
            )
        self.cur.execute("ROLLBACK TO SAVEPOINT forged_creator")
        self.cur.execute("RELEASE SAVEPOINT forged_creator")
        self.conn.commit()

        self._employee_context()
        self.cur.execute("SELECT current_setting('app.erp_shared_express_endpoint', true) AS gate")
        self.assertNotEqual(self.cur.fetchone()["gate"], "on")
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual(self.cur.fetchall(), [])
        self.conn.rollback()

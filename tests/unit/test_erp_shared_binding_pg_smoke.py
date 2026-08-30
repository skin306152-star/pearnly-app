# -*- coding: utf-8 -*-
"""F1-B3B1 binding columns and checks on disposable PostgreSQL temp tables."""

from __future__ import annotations

import importlib.util
import re
import unittest
import uuid
from pathlib import Path
from unittest import mock

from services.erp import shared_express_binding_schema
from tests.unit._pg_smoke import connect_or_skip

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "0109_erp_shared_express_binding.py"
BASELINE = ROOT / "alembic" / "sql" / "001a_legacy_tables.sql"

EXPECTED_COLUMNS = {
    "bound_account_set": ("text", "YES"),
    "bound_profile_key": ("text", "YES"),
    "live_account_set": ("text", "YES"),
    "live_profile_key": ("text", "YES"),
    "agent_last_seen_at": ("timestamp with time zone", "YES"),
    "agent_version": ("text", "YES"),
    "binding_generation": ("bigint", "NO"),
}


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_0109_pg", MIGRATION)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def _legacy_table(cur, poison_column=""):
    poison = f", {poison_column}" if poison_column else ""
    cur.execute(
        "CREATE TEMP TABLE erp_endpoints ("
        "id UUID PRIMARY KEY, user_id UUID NOT NULL, name TEXT NOT NULL, "
        "adapter TEXT NOT NULL, config JSONB NOT NULL DEFAULT '{}'::jsonb" + poison + ")"
    )


class SharedExpressBindingPgSmokeTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.cur.execute("SET search_path TO pg_temp, public")

    def tearDown(self):
        self.conn.rollback()
        self.cur.close()
        self.conn.close()

    def _apply_twice(self):
        migration = _load_migration()
        with mock.patch.object(migration.op, "execute", side_effect=self.cur.execute):
            migration.upgrade()
            migration.downgrade()
        shared_express_binding_schema.apply_shared_express_binding_foundation(self.cur)
        shared_express_binding_schema.apply_shared_express_binding_foundation(self.cur)

    def _binding_catalog(self):
        self.cur.execute("SELECT current_schema() AS schema")
        schema = self.cur.fetchone()["schema"]
        self.cur.execute(
            "SELECT column_name,data_type,is_nullable,column_default "
            "FROM information_schema.columns WHERE table_schema=%s "
            "AND table_name='erp_endpoints' AND column_name=ANY(%s) "
            "ORDER BY column_name",
            (schema, list(EXPECTED_COLUMNS)),
        )
        return [dict(row) for row in self.cur.fetchall()]

    def _run_archive_upgrade(self):
        migration = _load_migration()
        with mock.patch.object(migration.op, "execute", side_effect=self.cur.execute):
            migration.upgrade()

    def _run_startup_ensure(self):
        cm = mock.MagicMock()
        cm.__enter__.return_value = self.cur
        cm.__exit__.return_value = False
        with mock.patch.object(
            shared_express_binding_schema.db,
            "get_cursor",
            return_value=cm,
        ):
            shared_express_binding_schema.ensure_shared_express_binding_foundation()

    def _assert_poison_rejected_without_rewrite(self, poison_column):
        import psycopg2

        _legacy_table(self.cur, poison_column)
        before = self._binding_catalog()
        for runner in (self._run_archive_upgrade, self._run_startup_ensure):
            with self.subTest(runner=runner.__name__, poison=poison_column):
                self.cur.execute("SAVEPOINT poison_binding_contract")
                with self.assertRaises(psycopg2.errors.RaiseException):
                    runner()
                self.cur.execute("ROLLBACK TO SAVEPOINT poison_binding_contract")
                self.cur.execute("RELEASE SAVEPOINT poison_binding_contract")
                self.assertEqual(self._binding_catalog(), before)

    def test_migration_and_startup_are_idempotent_without_existing_row_backfill(self):
        _legacy_table(self.cur)
        endpoint_id = str(uuid.uuid4())
        self.cur.execute(
            "INSERT INTO erp_endpoints (id,user_id,name,adapter,config) "
            "VALUES (%s,%s,'Legacy Express','express','{\"account_set\":\"DATAT\"}'::jsonb)",
            (endpoint_id, str(uuid.uuid4())),
        )

        self._apply_twice()

        self.cur.execute(
            "SELECT bound_account_set,bound_profile_key,live_account_set,live_profile_key,"
            "agent_last_seen_at,agent_version,binding_generation "
            "FROM erp_endpoints WHERE id=%s",
            (endpoint_id,),
        )
        row = self.cur.fetchone()
        for column in EXPECTED_COLUMNS:
            if column == "binding_generation":
                self.assertEqual(row[column], 0)
            else:
                self.assertIsNone(row[column])

    def test_catalog_types_defaults_not_null_and_validated_checks(self):
        _legacy_table(self.cur)
        self._apply_twice()
        self.cur.execute("SELECT current_schema() AS schema")
        schema = self.cur.fetchone()["schema"]
        self.cur.execute(
            "SELECT column_name,data_type,is_nullable,column_default "
            "FROM information_schema.columns WHERE table_schema=%s "
            "AND table_name='erp_endpoints' AND column_name=ANY(%s)",
            (schema, list(EXPECTED_COLUMNS)),
        )
        columns = {row["column_name"]: row for row in self.cur.fetchall()}
        self.assertEqual(set(columns), set(EXPECTED_COLUMNS))
        for name, (data_type, nullable) in EXPECTED_COLUMNS.items():
            self.assertEqual(columns[name]["data_type"], data_type)
            self.assertEqual(columns[name]["is_nullable"], nullable)
        self.assertEqual(columns["binding_generation"]["column_default"], "0")

        self.cur.execute(
            "SELECT conname,convalidated,pg_get_constraintdef(oid) AS definition "
            "FROM pg_constraint WHERE conrelid='erp_endpoints'::regclass "
            "AND (conname LIKE 'erp_endpoints_%profile_pair_chk' "
            "OR conname='erp_endpoints_binding_generation_chk')"
        )
        constraints = {row["conname"]: row for row in self.cur.fetchall()}
        self.assertEqual(
            set(constraints),
            {
                "erp_endpoints_bound_profile_pair_chk",
                "erp_endpoints_live_profile_pair_chk",
                "erp_endpoints_binding_generation_chk",
            },
        )
        self.assertTrue(all(row["convalidated"] for row in constraints.values()))

    def test_checks_reject_half_pairs_and_negative_generation(self):
        import psycopg2

        _legacy_table(self.cur)
        self._apply_twice()
        base = (str(uuid.uuid4()), str(uuid.uuid4()), "Express")
        bad_fragments = (
            ("bound_account_set", "'DATAT'"),
            ("bound_profile_key", "'v1:key'"),
            ("live_account_set", "'DATAT'"),
            ("live_profile_key", "'v1:key'"),
            ("binding_generation", "-1"),
        )
        for column, value in bad_fragments:
            with self.subTest(column=column):
                self.cur.execute("SAVEPOINT invalid_binding")
                with self.assertRaises(psycopg2.errors.CheckViolation):
                    self.cur.execute(
                        "INSERT INTO erp_endpoints (id,user_id,name,adapter," + column + ") "
                        "VALUES (%s,%s,%s,'express'," + value + ")",
                        base,
                    )
                self.cur.execute("ROLLBACK TO SAVEPOINT invalid_binding")
                self.cur.execute("RELEASE SAVEPOINT invalid_binding")

        self.cur.execute(
            "INSERT INTO erp_endpoints "
            "(id,user_id,name,adapter,bound_account_set,bound_profile_key,"
            "live_account_set,live_profile_key,binding_generation) "
            "VALUES (%s,%s,%s,'express','DATAT','v1:bound','DATAT','v1:live',1)",
            base,
        )

    def test_wrong_existing_type_is_rejected_without_rewrite(self):
        self._assert_poison_rejected_without_rewrite("bound_account_set BIGINT")

    def test_wrong_existing_default_is_rejected_without_rewrite(self):
        self._assert_poison_rejected_without_rewrite("agent_version TEXT DEFAULT 'poison'")

    def test_wrong_existing_nullability_is_rejected_without_rewrite(self):
        self._assert_poison_rejected_without_rewrite("live_profile_key TEXT NOT NULL")

    def test_fresh_baseline_table_block_executes_with_target_shape(self):
        source = BASELINE.read_text(encoding="utf-8")
        match = re.search(
            r'CREATE TABLE IF NOT EXISTS "erp_endpoints" \(.*?^\);',
            source,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        ddl = match.group(0).replace(
            'CREATE TABLE IF NOT EXISTS "erp_endpoints"',
            "CREATE TEMP TABLE erp_endpoints",
            1,
        )
        self.cur.execute(ddl)
        endpoint_id = str(uuid.uuid4())
        self.cur.execute(
            "INSERT INTO erp_endpoints (id,user_id,name,adapter) "
            "VALUES (%s,%s,'Fresh Express','express')",
            (endpoint_id, str(uuid.uuid4())),
        )
        self.cur.execute(
            "SELECT bound_account_set,bound_profile_key,live_account_set,live_profile_key,"
            "agent_last_seen_at,agent_version,binding_generation "
            "FROM erp_endpoints WHERE id=%s",
            (endpoint_id,),
        )
        row = self.cur.fetchone()
        self.assertEqual(row["binding_generation"], 0)
        for column in EXPECTED_COLUMNS:
            if column != "binding_generation":
                self.assertIsNone(row[column])


if __name__ == "__main__":
    unittest.main(verbosity=2)

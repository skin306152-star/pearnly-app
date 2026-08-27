# -*- coding: utf-8 -*-
"""会计事务所身份 schema 与 0103 迁移契约。"""

from __future__ import annotations

import contextlib
import importlib.util
import inspect
import unittest
from pathlib import Path
from unittest import mock

from core import db
from services import startup
from services.firm import schema

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "alembic" / "versions" / "0103_accounting_firm_profiles.py"
SPEC = importlib.util.spec_from_file_location("firm_profile_migration_0103", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)


class RecordingCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


@contextlib.contextmanager
def cursor_context(cursor, *args, **kwargs):
    yield cursor


def compact(sql: str) -> str:
    return " ".join(sql.split())


class RuntimeSchemaContractTests(unittest.TestCase):
    def test_runtime_schema_executes_classification_profile_and_rls(self):
        cursor = RecordingCursor()
        with (
            mock.patch.object(db, "get_cursor", lambda *a, **k: cursor_context(cursor)),
            mock.patch.object(schema, "apply_tenant_rls") as apply_rls,
        ):
            schema.ensure_firm_schema()

        sql = "\n".join(call[0] for call in cursor.calls)
        self.assertIn("ALTER COLUMN tenant_type_v2 DROP DEFAULT", sql)
        self.assertIn("CREATE SEQUENCE IF NOT EXISTS", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS accounting_firm_profiles", sql)
        self.assertIn("ON CONFLICT (tenant_id) DO NOTHING", sql)
        apply_rls.assert_called_once_with(cursor, "accounting_firm_profiles")

    def test_classification_uses_only_canonical_business_type_mapping(self):
        sql = compact(schema._BACKFILL_TENANT_TYPE)
        for phrase in (
            "= 'firm' THEN 'f_firm'",
            "IN ('retail', 'pharmacy', 'restaurant') THEN 's_micro'",
            "IN ('service', 'b2b') THEN 'm_business'",
            "module_key = '__business_type__'",
            "tenant_type_v2 IS NULL OR",
            "NOT IN ('s_micro', 'm_business', 'f_firm')",
        ):
            self.assertIn(phrase, sql)
        for forbidden in ("erp_portal", "dms_portal", "pos_entitlements", "tenant.name"):
            self.assertNotIn(forbidden, sql)

    def test_profile_backfill_is_firm_only_and_never_overwrites(self):
        sql = compact(schema._BACKFILL_PROFILES)
        self.assertIn("WHERE t.tenant_type_v2 = 'f_firm'", sql)
        self.assertIn("COALESCE(NULLIF(t.display_name, ''), t.name)", sql)
        self.assertIn("CASE WHEN t.status = 'active' THEN 'active' ELSE 'suspended' END", sql)
        self.assertIn("ON CONFLICT (tenant_id) DO NOTHING", sql)
        self.assertNotIn("DO UPDATE", sql)

    def test_membership_source_no_longer_defaults_every_tenant_to_firm(self):
        from services.membership import schema as membership_schema

        source = inspect.getsource(membership_schema.ensure_membership_tables)
        self.assertIn("ADD COLUMN IF NOT EXISTS tenant_type_v2 TEXT", source)
        self.assertNotIn("tenant_type_v2 TEXT DEFAULT 'firm'", source)

    def test_startup_runs_firm_schema_before_orphan_rls_guard(self):
        source = inspect.getsource(startup._boot_schema_ddl)
        firm_at = source.index("ensure_firm_schema")
        guard_at = source.rindex("ensure_no_orphan_rls")
        self.assertLess(firm_at, guard_at)


class AlembicParityTests(unittest.TestCase):
    def setUp(self):
        self.sql = []
        with mock.patch.object(MIGRATION.op, "execute", side_effect=self.sql.append):
            MIGRATION.upgrade()
        self.joined = "\n".join(self.sql)

    def test_revision_extends_current_head(self):
        self.assertEqual(MIGRATION.revision, "0103_accounting_firm_profiles")
        self.assertEqual(MIGRATION.down_revision, "0102_line_dms_login_tickets")

    def test_runtime_and_migration_share_critical_sql(self):
        normalized = compact(self.joined)
        for runtime_sql in (
            schema._BACKFILL_TENANT_TYPE,
            schema._SEQUENCE,
            schema._TABLE,
            schema._BACKFILL_PROFILES,
        ):
            self.assertIn(compact(runtime_sql), normalized)

    def test_constraint_allows_null_but_rejects_other_non_null_values(self):
        check_sql = compact(schema._CHECK_TENANT_TYPE)
        self.assertIn("CHECK (tenant_type_v2 IN ('s_micro', 'm_business', 'f_firm'))", check_sql)
        self.assertNotIn("NOT NULL", check_sql)

    def test_alembic_policy_is_idempotent_after_startup_dual_run(self):
        drop_at = self.joined.index(
            "DROP POLICY IF EXISTS tenant_isolation ON accounting_firm_profiles"
        )
        create_at = self.joined.index("CREATE POLICY tenant_isolation ON accounting_firm_profiles")
        self.assertLess(drop_at, create_at)

    def test_firm_code_uses_unique_sequence_backed_human_code(self):
        sql = compact(schema._TABLE)
        self.assertIn("firm_code text NOT NULL UNIQUE", sql)
        self.assertIn("'PF' || lpad(nextval", sql)
        self.assertIn("::text, 8, '0'", sql)


if __name__ == "__main__":
    unittest.main()

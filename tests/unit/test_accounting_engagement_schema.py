"""accounting_engagements schema、迁移与灰度闸契约。"""

from __future__ import annotations

import contextlib
import importlib.util
import inspect
import unittest
from pathlib import Path
from unittest import mock

from core import db, rls
from services import startup
from services.accounting_engagement import flags, schema

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "alembic" / "versions" / "0104_accounting_engagements.py"
SPEC = importlib.util.spec_from_file_location("accounting_engagements_0104", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)


class Cursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


@contextlib.contextmanager
def cursor_context(cursor, *args, **kwargs):
    yield cursor


def compact(sql: str) -> str:
    return " ".join(sql.split())


class AccountingEngagementSchemaTests(unittest.TestCase):
    def test_runtime_builds_constraints_indexes_and_participant_rls(self):
        cursor = Cursor()
        with (
            mock.patch.object(db, "get_cursor", lambda *a, **k: cursor_context(cursor)),
            mock.patch.object(schema, "apply_participant_tenant_rls") as apply_rls,
        ):
            schema.ensure_accounting_engagement_schema()

        sql = "\n".join(call[0] for call in cursor.calls)
        self.assertIn("CREATE TABLE IF NOT EXISTS accounting_engagements", sql)
        self.assertIn("ck_accounting_engagement_active_ready", sql)
        self.assertIn("uq_engagement_primary_merchant_open", sql)
        self.assertIn("uq_engagement_firm_workspace_open", sql)
        apply_rls.assert_called_once_with(
            cursor,
            "accounting_engagements",
            left_column="firm_tenant_id",
            right_column="merchant_tenant_id",
        )

    def test_partial_unique_and_active_readiness_contracts(self):
        table = compact(schema._TABLE)
        indexes = compact(" ".join(schema._INDEXES))
        for field in (
            "firm_workspace_client_id IS NOT NULL",
            "merchant_workspace_client_id IS NOT NULL",
            "merchant_accepted_at IS NOT NULL",
            "firm_accepted_at IS NOT NULL",
            "active_from IS NOT NULL",
        ):
            self.assertIn(field, table)
        self.assertIn("WHERE is_primary AND status <> 'ended'", indexes)
        self.assertIn("firm_tenant_id <> merchant_tenant_id", table)

    def test_participant_rls_matches_either_side_and_rejects_unknown_columns(self):
        cursor = Cursor()
        rls.apply_participant_tenant_rls(
            cursor,
            "accounting_engagements",
            left_column="firm_tenant_id",
            right_column="merchant_tenant_id",
        )
        policy = compact(cursor.calls[-1][0])
        self.assertIn("firm_tenant_id::text = current_setting", policy)
        self.assertIn("merchant_tenant_id::text = current_setting", policy)
        with self.assertRaises(ValueError):
            rls.apply_participant_tenant_rls(
                Cursor(),
                "accounting_engagements",
                left_column="tenant_id; DROP TABLE users",
                right_column="merchant_tenant_id",
            )

    def test_startup_runs_after_firm_and_before_rls_orphan_guard(self):
        source = inspect.getsource(startup._boot_schema_ddl)
        firm_at = source.index("ensure_firm_schema")
        engagement_at = source.index("ensure_accounting_engagement_schema")
        guard_at = source.rindex("ensure_no_orphan_rls")
        self.assertLess(firm_at, engagement_at)
        self.assertLess(engagement_at, guard_at)

    def test_flag_is_absent_or_error_fail_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=False
        ) as enabled:
            self.assertFalse(flags.enabled_for("tenant-a"))
            enabled.assert_called_once_with(flags.ERP_COWORK_ENGAGEMENTS_KEY, "tenant-a")
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", side_effect=RuntimeError
        ):
            self.assertFalse(flags.enabled_for("tenant-a"))
        self.assertFalse(flags.enabled_for(None))


class AccountingEngagementMigrationTests(unittest.TestCase):
    def setUp(self):
        self.sql = []
        with mock.patch.object(MIGRATION.op, "execute", side_effect=self.sql.append):
            MIGRATION.upgrade()
        self.joined = compact("\n".join(self.sql))

    def test_revision_extends_current_head(self):
        self.assertEqual(MIGRATION.revision, "0104_accounting_engagements")
        self.assertEqual(MIGRATION.down_revision, "0103_accounting_firm_profiles")

    def test_migration_contains_runtime_critical_contracts(self):
        for phrase in (
            "CREATE TABLE IF NOT EXISTS accounting_engagements",
            "uq_engagement_primary_merchant_open",
            "uq_engagement_firm_workspace_open",
            "participant_tenant_isolation",
            "merchant_tenant_id::text = current_setting",
        ):
            self.assertIn(phrase, self.joined)


if __name__ == "__main__":
    unittest.main()

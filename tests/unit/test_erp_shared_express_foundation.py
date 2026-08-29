# -*- coding: utf-8 -*-
"""Contracts for the dormant F1 shared Express database foundation."""

import importlib.util
import re
import unittest
from pathlib import Path
from unittest import mock

from services.erp import shared_express_flag, shared_express_schema

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "0108_erp_shared_express_foundation.py"
BASELINE = ROOT / "alembic" / "sql" / "001a_legacy_tables.sql"
SNAPSHOT = ROOT / "docs" / "db" / "prod-schema.sql"


def _norm(statement: str) -> str:
    return " ".join(statement.lower().split())


class SharedExpressFlagTests(unittest.TestCase):
    def test_key_is_exact(self):
        self.assertEqual(
            shared_express_flag.ERP_SHARED_EXPRESS_ENDPOINT_KEY,
            "erp_shared_express_endpoint",
        )

    def test_missing_tenant_is_closed_without_store_lookup(self):
        with mock.patch("services.platform_settings.store.is_enabled_for_user") as enabled:
            self.assertFalse(shared_express_flag.erp_shared_express_endpoint_enabled_for(None))
            enabled.assert_not_called()

    def test_missing_setting_is_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=False
        ) as enabled:
            self.assertFalse(
                shared_express_flag.erp_shared_express_endpoint_enabled_for("tenant-1")
            )
            enabled.assert_called_once_with("erp_shared_express_endpoint", "tenant-1")

    def test_explicit_tenant_enable_is_honored(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user", return_value=True
        ) as enabled:
            self.assertTrue(shared_express_flag.erp_shared_express_endpoint_enabled_for("tenant-1"))
            enabled.assert_called_once_with("erp_shared_express_endpoint", "tenant-1")

    def test_store_failure_is_closed(self):
        with mock.patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("unavailable"),
        ):
            self.assertFalse(
                shared_express_flag.erp_shared_express_endpoint_enabled_for("tenant-1")
            )


class SharedExpressSchemaTests(unittest.TestCase):
    def test_additive_columns_and_exact_partial_unique(self):
        ddl = _norm(" ".join(shared_express_schema.SHARED_EXPRESS_DDL))
        self.assertIn("erp_endpoints add column if not exists workspace_client_id bigint", ddl)
        self.assertIn(
            "erp_endpoints add column if not exists shared_scope boolean not null default false",
            ddl,
        )
        self.assertIn("erp_push_logs add column if not exists workspace_client_id bigint", ddl)
        expected = _norm(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "uq_erp_endpoints_shared_express_workspace "
            "ON erp_endpoints (tenant_id, workspace_client_id, adapter) "
            "WHERE enabled = TRUE AND shared_scope = TRUE AND adapter = 'express' "
            "AND tenant_id IS NOT NULL AND workspace_client_id IS NOT NULL"
        )
        self.assertIn(expected, [_norm(sql) for sql in shared_express_schema.SHARED_EXPRESS_DDL])
        contract = _norm(shared_express_schema._INDEX_CONTRACT_DDL)
        self.assertIn("pg_get_indexdef", contract)
        self.assertIn("pg_get_expr", contract)
        self.assertIn("v_columns is distinct from array", contract)
        self.assertIn("v_valid is distinct from true", contract)
        self.assertIn("v_ready is distinct from true", contract)
        self.assertIn("v_live is distinct from true", contract)
        self.assertIn("index_meta.indisvalid", contract)
        self.assertIn("index_meta.indisready", contract)
        self.assertIn("index_meta.indislive", contract)
        self.assertIn("raise exception", contract)

    def test_shared_policies_are_select_only_and_adapter_gated(self):
        policies = [
            _norm(sql)
            for sql in shared_express_schema.SHARED_EXPRESS_DDL
            if sql.startswith("CREATE POLICY")
        ]
        self.assertEqual(len(policies), 2)
        for policy in policies:
            self.assertIn(" for select using ", policy)
            self.assertNotRegex(policy, r" for (all|insert|update|delete) ")
            self.assertIn("app.erp_shared_express_endpoint", policy)
            self.assertIn("app.erp_shared_express_tenant_id", policy)
            self.assertIn("app.erp_shared_express_workspace_id", policy)
            self.assertIn("app.current_tenant_id", policy)
            self.assertIn("app.current_workspace_id", policy)
            self.assertIn("adapter = 'express'", policy)
            self.assertIn(
                "current_setting('app.erp_shared_express_tenant_id', true) "
                "= current_setting('app.current_tenant_id', true)",
                policy,
            )
            self.assertIn(
                "current_setting('app.erp_shared_express_workspace_id', true) "
                "= current_setting('app.current_workspace_id', true)",
                policy,
            )
            self.assertIn(
                "tenant_id::text " "= current_setting('app.erp_shared_express_tenant_id', true)",
                policy,
            )
            self.assertIn(
                "workspace_client_id::text "
                "= current_setting('app.erp_shared_express_workspace_id', true)",
                policy,
            )
        self.assertIn("shared_endpoint.id = erp_push_logs.endpoint_id", policies[1])

    def test_existing_owner_policy_is_not_replaced(self):
        ddl = _norm(" ".join(shared_express_schema.SHARED_EXPRESS_DDL))
        self.assertNotIn("drop policy if exists tenant_isolation", ddl)
        self.assertNotIn("create policy tenant_isolation", ddl)

    def test_session_gate_stays_closed_when_tenant_flag_is_off(self):
        cursor = mock.Mock()
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=False,
        ) as enabled:
            self.assertFalse(
                shared_express_schema.enable_shared_express_select(cursor, "tenant-1", 101)
            )
        enabled.assert_called_once_with("tenant-1")
        cursor.execute.assert_called_once_with("SET LOCAL app.erp_shared_express_endpoint = 'off'")

    def test_session_gate_stays_closed_without_both_scopes(self):
        for tenant_id, workspace_id in ((None, 101), ("tenant-1", None), ("", 101)):
            with self.subTest(tenant_id=tenant_id, workspace_id=workspace_id):
                cursor = mock.Mock()
                with mock.patch.object(
                    shared_express_schema,
                    "erp_shared_express_endpoint_enabled_for",
                ) as enabled:
                    self.assertFalse(
                        shared_express_schema.enable_shared_express_select(
                            cursor, tenant_id, workspace_id
                        )
                    )
                enabled.assert_not_called()
                cursor.execute.assert_called_once_with(
                    "SET LOCAL app.erp_shared_express_endpoint = 'off'"
                )

    def test_session_gate_rejects_flag_tenant_and_cursor_scope_mismatch(self):
        cursor = mock.Mock()
        cursor.fetchone.return_value = {"matches": False}
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ) as enabled:
            self.assertFalse(
                shared_express_schema.enable_shared_express_select(cursor, "tenant-a", 101)
            )
        enabled.assert_called_once_with("tenant-a")
        self.assertEqual(cursor.execute.call_count, 2)
        self.assertIn(
            "current_setting('app.current_tenant_id', true)",
            cursor.execute.call_args_list[1].args[0],
        )
        self.assertIn(
            "current_setting('app.current_workspace_id', true)",
            cursor.execute.call_args_list[1].args[0],
        )
        self.assertEqual(cursor.execute.call_args_list[1].args[1], ("tenant-a", "101"))

    def test_session_gate_binds_validated_tenant_and_workspace(self):
        cursor = mock.Mock()
        cursor.fetchone.return_value = {"matches": True}
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ) as enabled:
            self.assertTrue(
                shared_express_schema.enable_shared_express_select(cursor, "tenant-1", 101)
            )
        enabled.assert_called_once_with("tenant-1")
        self.assertEqual(cursor.execute.call_count, 3)
        self.assertEqual(cursor.execute.call_args_list[1].args[1], ("tenant-1", "101"))
        self.assertEqual(cursor.execute.call_args_list[2].args[1], ("tenant-1", "101"))
        self.assertIn(
            "set_config('app.erp_shared_express_endpoint', 'on', true)",
            cursor.execute.call_args_list[2].args[0],
        )

    def test_startup_ensure_is_idempotent_and_data_preserving(self):
        cursor = mock.Mock()
        cm = mock.MagicMock()
        cm.__enter__.return_value = cursor
        with mock.patch.object(shared_express_schema.db, "get_cursor", return_value=cm):
            shared_express_schema.ensure_shared_express_foundation()
            shared_express_schema.ensure_shared_express_foundation()
        expected = list(shared_express_schema.SHARED_EXPRESS_DDL) * 2
        self.assertEqual([call.args[0] for call in cursor.execute.call_args_list], expected)
        ddl = _norm(" ".join(expected))
        self.assertNotIn("drop column", ddl)
        self.assertNotRegex(ddl, r"\b(delete|update)\s+(from\s+)?erp_")


class SharedExpressMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("migration_0108", MIGRATION)
        cls.migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.migration)

    def test_revision_chain_and_dual_run_match(self):
        self.assertEqual(self.migration.revision, "0108_erp_shared_express_foundation")
        self.assertEqual(self.migration.down_revision, "0107_sales_line_item_type")
        self.assertEqual(
            [_norm(sql) for sql in self.migration._DDL],
            [_norm(sql) for sql in shared_express_schema.SHARED_EXPRESS_DDL],
        )

    def test_upgrade_is_idempotent_and_downgrade_is_non_destructive(self):
        with mock.patch.object(self.migration.op, "execute") as execute:
            self.migration.upgrade()
        self.assertEqual(
            [call.args[0] for call in execute.call_args_list], list(self.migration._DDL)
        )
        source = MIGRATION.read_text(encoding="utf-8")
        downgrade = source.split("def downgrade()", 1)[1]
        self.assertNotIn("DROP COLUMN", downgrade.upper())
        self.assertNotIn("DELETE FROM", downgrade.upper())

    def test_startup_wires_foundation_before_rls_enroll(self):
        source = (ROOT / "services" / "startup.py").read_text(encoding="utf-8")
        ensure_at = source.index("ensure_shared_express_foundation")
        enroll_at = source.index("run_rls_enrolls")
        self.assertLess(ensure_at, enroll_at)

    def test_fresh_baseline_and_snapshot_include_target_shape(self):
        for path in (BASELINE, SNAPSHOT):
            source = _norm(path.read_text(encoding="utf-8"))
            self.assertIn('"workspace_client_id" bigint', source)
            self.assertIn('"shared_scope" boolean default false not null', source)
        baseline = _norm(BASELINE.read_text(encoding="utf-8"))
        snapshot = _norm(SNAPSHOT.read_text(encoding="utf-8"))
        self.assertNotIn("create unique index if not exists uq_erp_endpoints_shared", baseline)
        self.assertIn("uq_erp_endpoints_shared_express_workspace", snapshot)

    def test_legacy_user_unique_remains(self):
        source = _norm(BASELINE.read_text(encoding="utf-8"))
        self.assertIn("uq_erp_endpoints_user_express", source)
        self.assertIn("on public.erp_endpoints using btree (user_id)", source)
        migration_source = _norm(MIGRATION.read_text(encoding="utf-8"))
        self.assertNotIn("drop index uq_erp_endpoints_user_express", migration_source)


if __name__ == "__main__":
    unittest.main()

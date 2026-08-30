"""Static contract checks for the B3B3 live-profile schema."""

import importlib.util
import unittest
from pathlib import Path

from services.erp.shared_express_live_ddl import LIVE_DDL


class ManagedLiveSchemaContractTests(unittest.TestCase):
    def test_migration_chain_startup_order_and_canonical_ddl(self):
        root = Path(__file__).resolve().parents[2]
        migration_path = root / "alembic/versions/0113_erp_shared_express_live.py"
        spec = importlib.util.spec_from_file_location("migration_0113", migration_path)
        migration = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(migration)
        self.assertEqual(migration.revision, "0113_erp_shared_express_live")
        self.assertEqual(migration.down_revision, "0112_erp_shared_express_lifecycle")
        self.assertIs(migration.LIVE_DDL, LIVE_DDL)
        startup = (root / "services/startup.py").read_text(encoding="utf-8")
        self.assertLess(
            startup.index("ensure_shared_express_lifecycle_schema"),
            startup.index("ensure_shared_express_live_schema"),
        )

    def test_contract_contains_independent_gate_and_policies(self):
        sql = "\n".join(LIVE_DDL)
        for value in (
            "guard_erp_endpoint_managed_live_columns",
            "guard_erp_endpoint_managed_profile_confirm",
            "erp_endpoints_managed_live_columns_guard",
            "erp_endpoints_managed_profile_confirm_guard",
            "erp_endpoints_managed_live_select",
            "erp_endpoints_managed_live_update",
            "erp_endpoints_managed_live_confirm",
            "app.erp_managed_live_heartbeat",
            "app.erp_managed_live_confirm",
            "SET search_path = pg_catalog",
            "REVOKE ALL ON FUNCTION",
            "guard_erp_endpoint_managed_profile_confirm()",
            "binding_generation::text = (NULLIF(pg_catalog.current_setting('app.erp_managed_live_expected_generation', true), '')::bigint + 1)::text",
        ):
            self.assertIn(value, sql)

    def test_heartbeat_trigger_has_complete_non_live_column_denylist(self):
        sql = next(
            statement
            for statement in LIVE_DDL
            if "guard_erp_endpoint_managed_live_columns" in statement
        )
        for column in (
            "tenant_id",
            "workspace_client_id",
            "binding_generation",
            "enabled",
            "shared_scope",
            "bound_account_set",
            "bound_profile_key",
            "config",
            "updated_at",
            "revoked_at",
            "revoked_by",
            "success_count",
            "failure_count",
        ):
            self.assertIn(f"NEW.{column} IS DISTINCT FROM OLD.{column}", sql)

    def test_no_queue_or_push_writer_is_introduced(self):
        sql = "\n".join(LIVE_DDL).lower()
        self.assertNotIn("insert into erp_push_logs", sql)
        self.assertNotIn("lease", sql)
        self.assertNotIn("ack", sql)

    def test_auth_function_is_minimal_and_managed_only(self):
        sql = next(
            statement for statement in LIVE_DDL if "erp_managed_live_authenticate" in statement
        )
        self.assertIn("jsonb_build_object", sql)
        self.assertNotIn("to_jsonb(endpoint)", sql)
        self.assertIn("endpoint.adapter = 'express'", sql)
        self.assertIn("endpoint.binding_generation > 0", sql)
        self.assertIn("endpoint.revoked_at IS NULL", sql)
        projection = sql.split("SELECT jsonb_build_object(", 1)[1].split(") INTO v_endpoint", 1)[0]
        self.assertEqual(
            {part for part in projection.split("'")[1::2]},
            {
                "tenant_id",
                "enabled",
                "shared_scope",
                "workspace_client_id",
                "binding_generation",
                "bound_account_set",
                "bound_profile_key",
            },
        )
        self.assertIn("workspace.tenant_id = endpoint.tenant_id", sql)
        self.assertIn("workspace.is_active = TRUE", sql)
        self.assertIn("tenant.status IN ('active', 'warning')", sql)

    def test_archives_are_exact_canonical_mirrors(self):
        root = Path(__file__).resolve().parents[2]
        canonical = ";\n".join(LIVE_DDL) + ";"
        archives = (
            (
                "alembic/sql/001a_legacy_tables.sql",
                "-- B3B3 managed live profile (canonical runtime: services/erp/shared_express_live_ddl.py)\n",
                "-- F1-B3B2b promotion guard.",
            ),
            (
                "docs/db/prod-schema.sql",
                "-- B3B3 managed live profile; kept in sync with shared_express_live_ddl.py.\n",
                "REVOKE ALL ON FUNCTION public.preserve_managed_erp_endpoints_on_user_delete() FROM PUBLIC;",
            ),
        )
        for name, start, end in archives:
            text = (root / name).read_text(encoding="utf-8")
            excerpt = text.split(start, 1)[1].split(end, 1)[0].strip()
            self.assertEqual(excerpt, canonical, name)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path

from services.erp.target_projection_schema import DDL, TABLES

ROOT = Path(__file__).resolve().parents[2]


class TargetProjectionSchemaTests(unittest.TestCase):
    def test_schema_has_immutable_history_head_items_and_rls(self):
        ddl = "\n".join(DDL)
        self.assertEqual(
            TABLES,
            (
                "erp_target_projection_snapshots",
                "erp_target_projection_heads",
                "erp_target_projection_items",
                "erp_target_refresh_requests",
            ),
        )
        for token in (
            "UNIQUE (tenant_id, endpoint_id, scope_kind, scope_key, revision)",
            "current_snapshot_id",
            "last_refresh_status",
            "last_refresh_attempted_at",
            "account_sets_revision",
            "master_revision",
            "form_schema_revision",
            "capability_revision",
            "entity_type IN ('products', 'customers', 'suppliers', 'units', 'branches', 'accounts')",
            "status IN ('requested', 'leased', 'succeeded', 'failed')",
        ):
            self.assertIn(token, ddl)
        schema = (ROOT / "services/erp/target_projection_schema.py").read_text()
        self.assertIn("apply_tenant_rls(cur, *TABLES)", schema)

    def test_alembic_and_startup_share_the_schema_source(self):
        migration = (ROOT / "alembic/versions/0119_erp_target_projection.py").read_text()
        startup = (ROOT / "services/startup.py").read_text()
        self.assertIn('revision = "0119_erp_target_projection"', migration)
        self.assertIn('down_revision = "0118_dms_line_query_permission"', migration)
        self.assertIn("from services.erp.target_projection_schema import DDL, TABLES", migration)
        self.assertIn("ensure_target_projection_schema()", startup)
        refresh_migration = (
            ROOT / "alembic/versions/0120_erp_target_refresh_requests.py"
        ).read_text()
        self.assertIn('revision = "0120_erp_target_refresh_requests"', refresh_migration)
        self.assertIn('down_revision = "0119_erp_target_projection"', refresh_migration)

    def test_new_read_api_is_feature_gated_and_registered(self):
        flags = (ROOT / "core/feature_flags.py").read_text()
        routes = (ROOT / "routes/erp_routes.py").read_text()
        self.assertIn('ERP_TARGET_PROJECTION_KEY = "erp_target_projection"', flags)
        self.assertIn("erp_target_projection_enabled_for", flags)
        self.assertIn("_target_projection_router", routes)


if __name__ == "__main__":
    unittest.main()

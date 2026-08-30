"""Static contracts for the B3B2b-2 database boundary."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

from services.erp import shared_express_lifecycle_schema as schema

ROOT = Path(__file__).resolve().parents[2]


class SharedExpressLifecycleSchemaContractTests(unittest.TestCase):
    def test_migration_chain_and_startup_hook(self):
        migration_path = ROOT / "alembic/versions/0112_erp_shared_express_lifecycle.py"
        spec = importlib.util.spec_from_file_location("migration_0112", migration_path)
        migration = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(migration)
        self.assertEqual(migration.revision, "0112_erp_shared_express_lifecycle")
        self.assertEqual(migration.down_revision, "0111_erp_shared_express_enrollment")
        startup = (ROOT / "services/startup.py").read_text(encoding="utf-8")
        self.assertIn("ensure_shared_express_lifecycle_schema", startup)
        self.assertLess(
            startup.index("ensure_shared_express_enrollment_rls"),
            startup.index("ensure_shared_express_lifecycle_schema"),
        )

    def test_additive_columns_constraints_index_and_exact_guc_policy(self):
        ddl = " ".join(schema.SHARED_EXPRESS_LIFECYCLE_DDL).lower()
        for token in (
            "add column if not exists revoked_at timestamptz",
            "add column if not exists revoked_by uuid",
            "erp_endpoints_revoked_pair_chk",
            "erp_endpoints_revoked_terminal_chk",
            "uq_operation_logs_erp_endpoint_lifecycle_operation",
            "details ->> 'operation_id'",
            "erp.endpoint.rebind",
            "erp.endpoint.enable",
            "erp.endpoint.disable",
            "erp.endpoint.revoke",
            "app.erp_endpoint_lifecycle_tenant_id",
            "app.erp_endpoint_lifecycle_actor_id",
            "app.erp_endpoint_lifecycle_endpoint_id",
            "app.erp_endpoint_lifecycle_action",
            "app.erp_endpoint_lifecycle_source_workspace_id",
            "app.erp_endpoint_lifecycle_target_workspace_id",
            "app.erp_endpoint_lifecycle_expected_generation",
            "erp_endpoints_managed_lifecycle_select",
        ):
            self.assertIn(token, ddl)

    def test_trigger_and_helper_are_security_definer_with_fixed_search_path(self):
        ddl = " ".join(schema.SHARED_EXPRESS_LIFECYCLE_DDL).lower()
        self.assertIn("security definer", ddl)
        self.assertGreaterEqual(ddl.count("set search_path = pg_catalog"), 2)
        self.assertIn("guard_erp_endpoint_lifecycle_columns", ddl)
        self.assertIn("erp_managed_endpoint_has_activity", ddl)
        self.assertIn("lease_owner is not null", ddl)
        self.assertIn("lease_expires_at is not null", ddl)
        self.assertIn("before update of tenant_id, workspace_client_id, binding_generation", ddl)
        self.assertIn("revoked_by, updated_at", ddl)
        self.assertNotIn(
            "before update of tenant_id, workspace_client_id, binding_generation, enabled, shared_scope, revoked_at, revoked_by, config",
            ddl,
        )
        self.assertIn(
            "revoke all on function public.erp_managed_endpoint_has_activity(uuid) from public", ddl
        )
        self.assertIn(
            "revoke all on function public.guard_erp_endpoint_lifecycle_columns() from public", ddl
        )
        self.assertIn(
            "before update of tenant_id, workspace_client_id, binding_generation, enabled", ddl
        )

    def test_archives_keep_index_fail_closed_contract_and_trigger_terminator(self):
        baseline = (ROOT / "alembic/sql/001a_legacy_tables.sql").read_text(encoding="utf-8").lower()
        archive = (ROOT / "docs/db/prod-schema.sql").read_text(encoding="utf-8").lower()
        for payload in (baseline, archive):
            self.assertIn(
                "duplicate tenant operation_id prevents lifecycle index contract", payload
            )
            self.assertIn(
                "does not match lifecycle contract",
                payload,
            )
        self.assertNotIn(
            "end\n$pearnly$\nrevoke all on function public.guard_erp_endpoint_lifecycle_columns()",
            archive,
        )
        self.assertIn(
            "end\n$pearnly$;\nrevoke all on function public.guard_erp_endpoint_lifecycle_columns()",
            archive,
        )

    def test_audit_contract_accepts_lifecycle_details_and_rejects_noncanonical_operation_id(self):
        from services.audit import store

        details = {
            "operation_id": "11111111-1111-4111-8111-111111111111",
            "expected_generation": 1,
            "actual_generation": 2,
            "workspace_before": 101,
            "workspace_after": 202,
            "target_workspace_client_id": 202,
            "revoked_before": False,
            "revoked_after": True,
            "reason": "owner_request",
        }
        store.insert_operation_log_tx(
            mock.Mock(),
            tenant_id="tenant",
            actor_user_id="actor",
            actor_username="owner",
            actor_is_super=False,
            action="erp.endpoint.revoke",
            target_type="erp_endpoint",
            target_id="endpoint",
            details=details,
        )
        with self.assertRaises(ValueError):
            store.insert_operation_log_tx(
                mock.Mock(),
                tenant_id="tenant",
                actor_user_id="actor",
                actor_username="owner",
                actor_is_super=False,
                action="erp.endpoint.revoke",
                target_type="erp_endpoint",
                target_id="endpoint",
                details={"operation_id": "not-a-uuid"},
            )


if __name__ == "__main__":
    unittest.main()

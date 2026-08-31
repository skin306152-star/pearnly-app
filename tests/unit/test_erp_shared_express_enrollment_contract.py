"""Contracts for the owner-only legacy Express promotion slice."""

from pathlib import Path
import unittest

from services.erp import shared_express_enrollment_schema as schema

ROOT = Path(__file__).resolve().parents[2]


class SharedEnrollmentContractTests(unittest.TestCase):
    def test_route_is_registered_in_erp_aggregate(self):
        source = (ROOT / "routes" / "erp_routes.py").read_text(encoding="utf-8")
        self.assertIn("erp_shared_express_enrollment_routes", source)
        self.assertIn("_shared_enrollment_router", source)

    def test_route_does_not_use_super_admin_erp_bypass(self):
        source = (ROOT / "routes" / "erp_shared_express_enrollment_routes.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('user.get("is_super_admin")', source)

    def test_schema_is_additive_and_has_no_bypass_policy(self):
        ddl = " ".join(schema.SHARED_EXPRESS_ENROLLMENT_RLS_DDL).lower()
        self.assertIn("for update", ddl)
        self.assertIn("binding_generation = 0", ddl)
        self.assertIn("binding_generation = 1", ddl)
        self.assertIn("shared_scope = true", ddl)
        self.assertNotIn("bypass_rls", ddl)

    def test_promotion_has_column_guard_and_fixed_search_path(self):
        ddl = " ".join(schema.SHARED_EXPRESS_ENROLLMENT_RLS_DDL).lower()
        self.assertIn("erp_endpoint_has_legacy_activity", ddl)
        self.assertIn("status in ('pending', 'retrying')", ddl)
        self.assertIn("next_retry_at is not null", ddl)
        self.assertIn("lease_owner is not null", ddl)
        self.assertIn("revoke all on function public.erp_endpoint_has_legacy_activity(uuid)", ddl)
        self.assertIn("pg_catalog.pg_roles", ddl)
        self.assertIn("if exists", ddl)
        self.assertIn(
            "execute 'grant execute on function public.erp_endpoint_has_legacy_activity(uuid) to pearnly_app'",
            ddl,
        )
        self.assertIn("guard_erp_endpoint_enrollment_columns", ddl)
        self.assertIn("security definer", ddl)
        self.assertIn("search_path = pg_catalog", ddl)
        self.assertIn("new.config is distinct from old.config", ddl)
        self.assertIn("new.user_id is distinct from old.user_id", ddl)
        self.assertIn("before update on public.erp_endpoints", ddl)
        self.assertIn("v_tgtype is distinct from 19", ddl)
        self.assertIn("tgattr::text", ddl)
        self.assertIn("v_tgattr is distinct from ''", ddl)
        self.assertNotIn("int2vector", ddl)
        self.assertIn("v_has_when", ddl)
        self.assertIn("v_enabled is distinct from 'o'", ddl)

    def test_archive_and_snapshot_put_policy_after_workspace_tables(self):
        archive = (ROOT / "alembic" / "sql" / "001a_legacy_tables.sql").read_text(encoding="utf-8")
        snapshot = (ROOT / "docs" / "db" / "prod-schema.sql").read_text(encoding="utf-8")
        self.assertIn("to_regclass('public.workspace_clients')", archive)
        self.assertIn("erp_endpoints_shared_express_enroll", archive)
        self.assertGreater(
            snapshot.rfind("erp_endpoints_shared_express_enroll"),
            snapshot.rfind('CREATE TABLE IF NOT EXISTS "workspace_clients"'),
        )

    def test_response_source_has_only_safe_fields(self):
        source = (ROOT / "services" / "erp" / "shared_express_enrollment.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"binding_generation"', source)
        self.assertNotIn('"config":', source)
        self.assertNotIn("agent_token_hash", source)

    def test_request_rejects_unrecognized_body_fields(self):
        from routes.erp_shared_express_enrollment_routes import EnrollRequest

        with self.assertRaises(ValueError):
            EnrollRequest.model_validate({"unexpected": True})

    def test_enrollment_refuses_legacy_queue_work_before_promotion(self):
        source = (ROOT / "services" / "erp" / "shared_express_enrollment.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("erp_endpoint_has_legacy_activity", source)
        self.assertIn('"erp.endpoint_busy"', source)

    def test_legacy_mutation_sinks_are_generation_zero_only(self):
        source = (ROOT / "services" / "erp" / "push_store.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(source.count("binding_generation = 0"), 7)
        reporting = (ROOT / "services" / "erp" / "express_push" / "agent_reporting.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("WHERE id = %s AND adapter = 'express'\n", reporting)

    def test_old_log_mutations_lock_or_reject_managed_endpoints(self):
        retry = (ROOT / "services" / "erp" / "push_retry.py").read_text(encoding="utf-8")
        self.assertIn("read_log_endpoint_id", retry)
        helper = (ROOT / "services" / "erp" / "legacy_generation.py").read_text(encoding="utf-8")
        self.assertIn("FOR SHARE", helper)
        self.assertIn("binding_generation = 0", helper)
        queries = (ROOT / "services" / "erp" / "push_log_queries.py").read_text(encoding="utf-8")
        self.assertIn("binding_generation > 0", queries)
        self.assertIn("endpoint_id IS NULL", queries)

    def test_workspace_binder_rejects_tenantless_cross_scope_endpoints(self):
        source = (ROOT / "services" / "workspace" / "endpoint_binding.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("elif endpoint_tenant is not None", source)
        self.assertIn("exclude_workspace_client_id", source)
        self.assertIn("AND is_active = TRUE", source)
        enrollment = (ROOT / "services" / "erp" / "shared_express_enrollment.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("FOR UPDATE", enrollment)
        self.assertNotIn("FOR UPDATE SKIP LOCKED", enrollment)

    def test_retry_lock_order_is_advisory_then_endpoint_share_then_log_update(self):
        source = (ROOT / "services" / "erp" / "push_retry.py").read_text(encoding="utf-8")
        block = source[source.index("def _lock_log_endpoint") : source.index("# 指数退避序列")]
        self.assertLess(block.index("read_log_endpoint_id"), block.index("lock_endpoint_binding"))
        self.assertLess(block.index("lock_endpoint_binding"), block.index("lock_legacy_endpoint"))
        update = source.index("UPDATE erp_push_logs", source.index("def schedule_log_retry"))
        self.assertLess(source.index("def _lock_log_endpoint"), update)

    def test_enrollment_route_uses_real_http_boundary_behaviors(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from unittest.mock import patch
        import routes.erp_shared_express_enrollment_routes as route

        app = FastAPI()
        app.include_router(route.router)
        user = {"id": "u1", "tenant_id": "t1", "entry": "main", "is_super_admin": False}
        with (
            patch.object(route, "get_current_user_from_request", return_value=user),
            patch.object(route, "require_erp_portal", return_value=user),
            patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=False),
        ):
            response = TestClient(app).post(
                "/api/erp/endpoints/e1/shared/enroll", headers={"X-Workspace-Client-Id": "1"}
            )
        self.assertEqual(response.status_code, 404)

        for rejected in (
            {**user, "is_super_admin": True},
            {**user, "entry": "pos"},
        ):
            with (
                patch.object(route, "get_current_user_from_request", return_value=rejected),
                patch.object(route, "require_erp_portal", return_value=rejected),
                patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=True),
            ):
                response = TestClient(app).post(
                    "/api/erp/endpoints/e1/shared/enroll", headers={"X-Workspace-Client-Id": "1"}
                )
            self.assertEqual(response.status_code, 403)

        with (
            patch.object(route, "get_current_user_from_request", return_value=user),
            patch.object(route, "require_erp_portal", return_value=user),
            patch.object(route, "erp_shared_express_endpoint_enabled_for", return_value=True),
        ):
            response = TestClient(app).post(
                "/api/erp/endpoints/e1/shared/enroll",
                headers={"X-Workspace-Client-Id": "1"},
                json={"extra": True},
            )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""F1-B3B2a managed ownership, RLS, and deletion-protection contracts."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

from services.erp import shared_express_managed_schema, shared_express_schema

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "0110_erp_shared_express_managed_access.py"
BASELINE = ROOT / "alembic" / "sql" / "001a_legacy_tables.sql"
SNAPSHOT = ROOT / "docs" / "db" / "prod-schema.sql"


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


class SharedExpressManagedSchemaTests(unittest.TestCase):
    def test_catalog_contract_quotes_literals_and_identifiers(self):
        contract, validate = shared_express_managed_schema._check_constraint(
            "endpoint_scope_chk",
            "adapter = 'express'",
            "checkadapter='express'::text",
        )
        self.assertIn("conname = 'endpoint_scope_chk'", contract)
        self.assertIn("v_definition <> 'checkadapter=''express''::text'", contract)
        self.assertNotIn("adapter='express'::text' THEN", contract)
        self.assertIn('ADD CONSTRAINT "endpoint_scope_chk"', contract)
        self.assertEqual(
            validate,
            'ALTER TABLE erp_endpoints VALIDATE CONSTRAINT "endpoint_scope_chk"',
        )

    def test_structure_is_additive_and_fail_closed(self):
        ddl = _norm(" ".join(shared_express_managed_schema.SHARED_EXPRESS_MANAGED_STRUCTURE_DDL))
        self.assertIn("alter table erp_endpoints alter column user_id drop not null", ddl)
        self.assertIn("erp_endpoints_legacy_creator_chk", ddl)
        self.assertIn("binding_generation > 0 or user_id is not null", ddl)
        self.assertIn("erp_endpoints_managed_scope_chk", ddl)
        self.assertIn("erp_endpoints_shared_generation_chk", ddl)
        for fragment in (
            "binding_generation = 0",
            "tenant_id is not null",
            "workspace_client_id is not null",
            "adapter = 'express'",
        ):
            self.assertIn(fragment, ddl)
        self.assertIn("erp_endpoints_tenant_id_fkey", ddl)
        self.assertIn("references tenants(id) on delete cascade", ddl)
        self.assertIn("orphan tenant_id", ddl)
        self.assertNotRegex(ddl, r"\bupdate\s+erp_endpoints\s+set\s+tenant_id")

    def test_creator_delete_trigger_is_security_definer_and_search_path_safe(self):
        ddl = _norm(" ".join(shared_express_managed_schema.SHARED_EXPRESS_MANAGED_STRUCTURE_DDL))
        self.assertIn("security definer", ddl)
        self.assertIn("set search_path = pg_catalog", ddl)
        self.assertIn("prosecdef", ddl)
        self.assertIn("proconfig", ddl)
        self.assertIn("before delete on public.users", ddl)
        self.assertIn("for each row", ddl)
        self.assertIn("binding_generation > 0", ddl)
        self.assertIn("set user_id = null", ddl)
        self.assertIn("tg_table_schema", ddl)
        self.assertIn("format( 'update %i.erp_endpoints", ddl)
        self.assertIn("revoke all on function", ddl)
        self.assertIn("prevent_managed_erp_endpoint_creator_change", ddl)
        self.assertIn("before update of user_id", ddl)

    def test_rls_splits_legacy_shared_and_managed_commands(self):
        ddl = _norm(" ".join(shared_express_managed_schema.SHARED_EXPRESS_MANAGED_RLS_DDL))
        self.assertIn("erp_endpoints_legacy_user_all", ddl)
        self.assertIn("binding_generation = 0", ddl)
        self.assertIn("erp_endpoints_shared_express_select", ddl)
        self.assertIn("binding_generation > 0", ddl)
        self.assertIn("erp_endpoints_managed_owner_select", ddl)
        self.assertIn("erp_endpoints_managed_owner_update", ddl)
        self.assertIn("for update", ddl)
        self.assertIn("with check", ddl)
        self.assertIn("memberships", ddl)
        self.assertIn("roles", ddl)
        self.assertIn("workspace_clients", ddl)
        self.assertIn("status = 'active'", ddl)
        self.assertIn("name = 'owner'", ddl)
        self.assertIn("erp_endpoints_no_managed_delete", ddl)
        self.assertIn("as restrictive for delete", ddl)

    def test_managed_gate_is_transaction_local_and_validates_current_context(self):
        previous = shared_express_managed_schema._MANAGED_FOUNDATION_READY
        shared_express_managed_schema._MANAGED_FOUNDATION_READY = True
        cur = mock.Mock()
        cur.fetchone.side_effect = [
            {"matches": True},
            {"id": 7},
            {"id": "membership"},
            {"id": 7},
        ]

        try:
            ok = shared_express_managed_schema.enable_managed_express_owner_access(
                cur,
                tenant_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                workspace_client_id=7,
                actor_user_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            )

            self.assertTrue(ok)
            sql = _norm(
                " ".join(
                    [
                        str(call.args[0])
                        + " "
                        + " ".join(str(value) for value in (call.args[1] or ()))
                        for call in cur.execute.call_args_list
                    ]
                )
            )
            self.assertIn("set_config", sql)
            self.assertIn("app.erp_managed_express_owner", sql)
            self.assertIn("app.current_tenant_id", sql)
            self.assertIn("app.current_workspace_id", sql)
            self.assertIn("app.current_user_id", sql)
            self.assertIn("for share", sql)
            statements = [call.args[0].lower() for call in cur.execute.call_args_list]
            self.assertLess(
                next(
                    i for i, statement in enumerate(statements) if "from memberships" in statement
                ),
                next(i for i, statement in enumerate(statements) if "from users" in statement),
            )
            self.assertLess(
                next(i for i, statement in enumerate(statements) if "from users" in statement),
                next(
                    i
                    for i, statement in enumerate(statements)
                    if "from workspace_clients" in statement
                ),
            )
        finally:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = previous

    def test_managed_gate_fails_closed_before_enabling(self):
        cur = mock.Mock()
        cur.fetchone.return_value = {"matches": False}

        self.assertFalse(
            shared_express_managed_schema.enable_managed_express_owner_access(
                cur,
                tenant_id="tenant",
                workspace_client_id=7,
                actor_user_id="actor",
            )
        )
        calls = [call.args[0] for call in cur.execute.call_args_list]
        self.assertEqual(sum("'on'" in sql for sql in calls), 0)

    def test_readiness_is_false_until_startup_ensure_succeeds(self):
        previous = shared_express_managed_schema._MANAGED_FOUNDATION_READY
        try:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = None
            self.assertFalse(shared_express_managed_schema.managed_foundation_ready())
            cur = mock.Mock()
            self.assertFalse(shared_express_schema.enable_shared_express_select(cur, "tenant", 7))
        finally:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = previous

    def test_managed_gate_failure_marks_shared_foundation_unavailable(self):
        previous = shared_express_managed_schema._MANAGED_FOUNDATION_READY
        try:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = None
            with mock.patch.object(
                shared_express_managed_schema.db,
                "get_cursor",
                side_effect=RuntimeError("drift"),
            ):
                with self.assertRaisesRegex(RuntimeError, "drift"):
                    shared_express_managed_schema.ensure_shared_express_managed_foundation()
            self.assertFalse(shared_express_managed_schema.managed_foundation_ready())
        finally:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = previous

    def test_b3a_shared_read_fails_closed_after_foundation_failure(self):
        previous = shared_express_managed_schema._MANAGED_FOUNDATION_READY
        try:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = False
            cur = mock.Mock()
            self.assertFalse(shared_express_schema.enable_shared_express_select(cur, "tenant", 7))
            cur.execute.assert_called_once()
        finally:
            shared_express_managed_schema._MANAGED_FOUNDATION_READY = previous


class SharedExpressManagedMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("migration_0110", MIGRATION)
        cls.migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.migration)

    def test_revision_chain_and_runtime_ddl_are_identical(self):
        self.assertEqual(self.migration.revision, "0110_erp_shared_express_managed_access")
        self.assertEqual(self.migration.down_revision, "0109_erp_shared_express_binding")
        self.assertEqual(
            [_norm(sql) for sql in self.migration._DDL],
            [_norm(sql) for sql in shared_express_managed_schema.SHARED_EXPRESS_MANAGED_DDL],
        )

    def test_upgrade_is_expand_only_archive(self):
        with mock.patch.object(self.migration.op, "execute") as execute:
            self.migration.upgrade()
        self.assertEqual(
            [call.args[0] for call in execute.call_args_list],
            list(self.migration._DDL),
        )
        downgrade = MIGRATION.read_text(encoding="utf-8").split("def downgrade()", 1)[1]
        self.assertNotRegex(downgrade.upper(), r"DROP\s+(COLUMN|CONSTRAINT|TRIGGER|FUNCTION)")

    def test_startup_and_rls_installer_order(self):
        startup = (ROOT / "services" / "startup.py").read_text(encoding="utf-8")
        binding_at = startup.index("ensure_shared_express_binding_foundation")
        managed_at = startup.index("ensure_shared_express_managed_foundation")
        enroll_at = startup.index("run_rls_enrolls")
        self.assertLess(binding_at, managed_at)
        self.assertLess(managed_at, enroll_at)

        push_schema = (ROOT / "services" / "erp" / "push_schema.py").read_text(encoding="utf-8")
        ensure = push_schema.split("def ensure_erp_push_rls", 1)[1]
        self.assertIn("apply_shared_express_managed_rls", ensure)
        self.assertNotIn('apply_user_rls(cur, "erp_endpoints", "erp_push_logs")', ensure)

    def test_fresh_baseline_and_snapshot_have_managed_shape(self):
        for path in (BASELINE, SNAPSHOT):
            source = _norm(path.read_text(encoding="utf-8"))
            endpoint = source.split('create table if not exists "erp_endpoints"', 1)[1].split(
                ");", 1
            )[0]
            self.assertIn('"user_id" uuid', endpoint)
            self.assertNotIn('"user_id" uuid not null', endpoint)
            self.assertIn('constraint "erp_endpoints_legacy_creator_chk"', endpoint)
            self.assertIn('constraint "erp_endpoints_managed_scope_chk"', endpoint)
            self.assertIn("erp_endpoints_tenant_id_fkey", source)
            self.assertIn("preserve_managed_erp_endpoints_on_user_delete", source)
            self.assertIn("erp_endpoints_preserve_managed_creator_delete", source)
            self.assertIn("erp_endpoints_managed_creator_immutable", source)
            self.assertIn("erp_endpoints_shared_generation_chk", endpoint)

    def test_canonical_cleanup_paths_bypass_managed_rls(self):
        owner_store = (ROOT / "services" / "tenant" / "owner_users.py").read_text(encoding="utf-8")
        demo_route = (ROOT / "routes" / "auth_admin_routes.py").read_text(encoding="utf-8")
        self.assertIn("get_cursor_rls(bypass=True, commit=True)", owner_store)
        self.assertIn('"erp_endpoints"', demo_route)
        self.assertIn("purge_managed_erp_endpoints_for_users", demo_route)
        self.assertIn("failed closed", demo_route)
        self.assertIn("get_cursor_rls(bypass=True, commit=True)", demo_route)

    def test_pg_smoke_fixture_has_canonical_endpoint_dependencies(self):
        smoke = (ROOT / "tests" / "unit" / "test_erp_shared_managed_pg_smoke.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("erp_endpoints_user_id_fkey", smoke)
        self.assertIn("erp_endpoints_tenant_id_fkey", smoke)
        self.assertIn("ON DELETE CASCADE", smoke)
        self.assertIn("uq_erp_endpoints_user_express", smoke)
        self.assertIn("binding_generation = 0", smoke)
        self.assertIn("race_conn = connect()", smoke)
        self.assertIn("_create_tables(race_cur)", smoke)
        self.assertIn("race_cur.fetchone()[0]", smoke)

    def test_legacy_express_unique_index_excludes_managed_generation(self):
        baseline = BASELINE.read_text(encoding="utf-8")
        snapshot = SNAPSHOT.read_text(encoding="utf-8")
        push_schema = (ROOT / "services" / "erp" / "push_schema.py").read_text(encoding="utf-8")
        for source in (baseline, snapshot, push_schema):
            self.assertIn("uq_erp_endpoints_user_express", source)
            self.assertIn("binding_generation = 0", source)


if __name__ == "__main__":
    unittest.main()

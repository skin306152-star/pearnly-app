# -*- coding: utf-8 -*-
"""F1-B3B1 typed binding schema and profile-key contracts."""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path
from unittest import mock

from services.erp import shared_express_binding_schema, shared_express_profile

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "0109_erp_shared_express_binding.py"
BASELINE = ROOT / "alembic" / "sql" / "001a_legacy_tables.sql"
SNAPSHOT = ROOT / "docs" / "db" / "prod-schema.sql"

EXPECTED_COLUMNS = {
    "bound_account_set": "TEXT",
    "bound_profile_key": "TEXT",
    "live_account_set": "TEXT",
    "live_profile_key": "TEXT",
    "agent_last_seen_at": "TIMESTAMPTZ",
    "agent_version": "TEXT",
    "binding_generation": "BIGINT NOT NULL DEFAULT 0",
}
EXPECTED_CATALOG = {
    "bound_account_set": ("text", False, None),
    "bound_profile_key": ("text", False, None),
    "live_account_set": ("text", False, None),
    "live_profile_key": ("text", False, None),
    "agent_last_seen_at": ("timestamp with time zone", False, None),
    "agent_version": ("text", False, None),
    "binding_generation": ("bigint", True, "0"),
}


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


class SharedExpressProfileKeyTests(unittest.TestCase):
    def test_key_is_versioned_irreversible_and_deterministic(self):
        key = shared_express_profile.profile_key(" DATAT ", "C:\\Express\\DATA\\")

        self.assertRegex(key, r"^v1:[0-9a-f]{64}$")
        self.assertNotIn("datat", key)
        self.assertNotIn("express", key)
        self.assertEqual(
            key,
            shared_express_profile.profile_key("datat", "c:/express/data"),
        )

    def test_unc_case_slashes_and_trailing_separator_normalize(self):
        self.assertEqual(
            shared_express_profile.profile_key("DATAZ", "\\\\SERVER\\Share\\Client\\"),
            shared_express_profile.profile_key("dataz", "//server/share/client"),
        )

    def test_account_or_physical_path_change_changes_key(self):
        base = shared_express_profile.profile_key("DATAT", r"C:\Express\DATA")
        self.assertNotEqual(
            base,
            shared_express_profile.profile_key("DATAZ", r"C:\Express\DATA"),
        )
        self.assertNotEqual(
            base,
            shared_express_profile.profile_key("DATAT", r"C:\Express\OTHER"),
        )

    def test_empty_nul_relative_and_invalid_windows_paths_are_rejected(self):
        bad_values = (
            ("", r"C:\Express\DATA"),
            ("DATAT", ""),
            ("DA\x00TAT", r"C:\Express\DATA"),
            ("DATAT", "C:\\Express\x00DATA"),
            ("DATAT", r"Express\DATA"),
            ("DATAT", r"C:Express\DATA"),
            ("DATAT", r"\Express\DATA"),
            ("DATAT", "C:\\"),
            ("DATAT", r"\\server"),
            ("DATAT", r"\\?\C:\Express\DATA"),
            ("DATAT", r"C:\Express\..\DATA"),
            ("DATAT", r"C:\Express\DA*TA"),
            ("DATAT", r"C:\Express\CON"),
            ("DATAT", r"C:\Express\nul.txt"),
            ("DATAT", "C:\\Express\\DATA."),
            ("DATAT", "C:\\Express\\DATA "),
        )
        for account_set, account_dir in bad_values:
            with self.subTest(account_set=account_set, account_dir=account_dir):
                with self.assertRaises(ValueError):
                    shared_express_profile.profile_key(account_set, account_dir)

    def test_public_api_never_returns_normalized_path(self):
        self.assertEqual(shared_express_profile.__all__, ["profile_key"])


class SharedExpressBindingSchemaTests(unittest.TestCase):
    def test_adds_exact_seven_typed_columns(self):
        ddl = _norm(" ".join(shared_express_binding_schema.SHARED_EXPRESS_BINDING_DDL))
        for name, definition in EXPECTED_COLUMNS.items():
            self.assertIn(
                _norm(f"ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS {name} {definition}"),
                ddl,
            )

    def test_constraints_are_exact_and_data_is_never_backfilled(self):
        ddl = _norm(" ".join(shared_express_binding_schema.SHARED_EXPRESS_BINDING_DDL))
        self.assertIn("erp_endpoints_bound_profile_pair_chk", ddl)
        self.assertIn("(bound_account_set is null) = (bound_profile_key is null)", ddl)
        self.assertIn("erp_endpoints_live_profile_pair_chk", ddl)
        self.assertIn("(live_account_set is null) = (live_profile_key is null)", ddl)
        self.assertIn("erp_endpoints_binding_generation_chk", ddl)
        self.assertIn("binding_generation >= 0", ddl)
        self.assertNotRegex(ddl, r"\bupdate\s+erp_endpoints\b")
        self.assertNotIn("config->", ddl)

    def test_catalog_contract_covers_all_columns_and_fails_closed_on_drift(self):
        self.assertEqual(
            {
                name: (catalog_type, not_null, default)
                for name, _add, catalog_type, not_null, default in (
                    shared_express_binding_schema.SHARED_EXPRESS_BINDING_COLUMNS
                )
            },
            EXPECTED_CATALOG,
        )
        contract = _norm(shared_express_binding_schema.SHARED_EXPRESS_BINDING_COLUMN_CONTRACT_DDL)
        for fragment in (
            "pg_attribute",
            "pg_attrdef",
            "format_type",
            "attnotnull",
            "pg_get_expr",
            "raise exception",
        ):
            self.assertIn(fragment, contract)
        for name in EXPECTED_COLUMNS:
            self.assertIn(name, contract)

    def test_startup_ensure_is_idempotent_and_expand_only(self):
        cursor = mock.Mock()
        cm = mock.MagicMock()
        cm.__enter__.return_value = cursor
        with mock.patch.object(shared_express_binding_schema.db, "get_cursor", return_value=cm):
            shared_express_binding_schema.ensure_shared_express_binding_foundation()
            shared_express_binding_schema.ensure_shared_express_binding_foundation()

        expected = list(shared_express_binding_schema.SHARED_EXPRESS_BINDING_DDL) * 2
        self.assertEqual([call.args[0] for call in cursor.execute.call_args_list], expected)
        ddl = _norm(" ".join(expected))
        self.assertNotIn("drop column", ddl)
        self.assertNotRegex(ddl, r"\b(delete|update)\s+(from\s+)?erp_endpoints")


class SharedExpressBindingMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("migration_0109", MIGRATION)
        cls.migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.migration)

    def test_revision_chain_and_dual_run_match(self):
        self.assertEqual(self.migration.revision, "0109_erp_shared_express_binding")
        self.assertEqual(self.migration.down_revision, "0108_erp_shared_express_foundation")
        self.assertEqual(
            [_norm(sql) for sql in self.migration._DDL],
            [_norm(sql) for sql in shared_express_binding_schema.SHARED_EXPRESS_BINDING_DDL],
        )
        self.assertEqual(
            self.migration._COLUMN_CONTRACTS,
            shared_express_binding_schema.SHARED_EXPRESS_BINDING_COLUMNS,
        )
        self.assertEqual(
            _norm(self.migration._COLUMN_CONTRACT_DDL),
            _norm(shared_express_binding_schema.SHARED_EXPRESS_BINDING_COLUMN_CONTRACT_DDL),
        )

    def test_upgrade_executes_archive_and_downgrade_preserves_additive_shape(self):
        with mock.patch.object(self.migration.op, "execute") as execute:
            self.migration.upgrade()
        self.assertEqual(
            [call.args[0] for call in execute.call_args_list],
            list(self.migration._DDL),
        )
        downgrade = MIGRATION.read_text(encoding="utf-8").split("def downgrade()", 1)[1]
        self.assertNotRegex(downgrade.upper(), r"DROP\s+(COLUMN|CONSTRAINT)")
        self.assertNotRegex(downgrade.upper(), r"\b(DELETE|UPDATE)\s+ERP_ENDPOINTS")

    def test_startup_wires_binding_after_b1_and_before_rls_enroll(self):
        source = (ROOT / "services" / "startup.py").read_text(encoding="utf-8")
        b1_at = source.index("ensure_shared_express_foundation")
        binding_at = source.index("ensure_shared_express_binding_foundation")
        enroll_at = source.index("run_rls_enrolls")
        self.assertLess(b1_at, binding_at)
        self.assertLess(binding_at, enroll_at)

    def test_fresh_baseline_and_snapshot_have_exact_shape(self):
        for path in (BASELINE, SNAPSHOT):
            source = _norm(path.read_text(encoding="utf-8"))
            for name, definition in EXPECTED_COLUMNS.items():
                snapshot_definition = definition.replace("TIMESTAMPTZ", "timestamp with time zone")
                if name == "binding_generation":
                    snapshot_definition = "BIGINT DEFAULT 0 NOT NULL"
                self.assertIn(_norm(f'"{name}" {snapshot_definition}'), source, str(path))
            self.assertIn('constraint "erp_endpoints_bound_profile_pair_chk"', source)
            self.assertIn('constraint "erp_endpoints_live_profile_pair_chk"', source)
            self.assertIn('constraint "erp_endpoints_binding_generation_chk"', source)

    def test_0108_archive_remains_unchanged_by_b3b1(self):
        previous = (
            ROOT / "alembic" / "versions" / "0108_erp_shared_express_foundation.py"
        ).read_text(encoding="utf-8")
        for column in EXPECTED_COLUMNS:
            self.assertNotIn(column, previous)


if __name__ == "__main__":
    unittest.main()

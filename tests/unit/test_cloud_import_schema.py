"""Cloud serving imports must not race the explicit schema release job."""

import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from services.auth.schema import _ensure_schema


class CloudImportSchemaTests(unittest.TestCase):
    def test_auth_schema_does_not_run_in_serving_roles(self):
        for role in ("web", "worker"):
            with (
                self.subTest(role=role),
                patch.dict(os.environ, PEARNLY_RUNTIME_ROLE=role),
                patch("core.db.get_cursor") as cursor,
            ):
                _ensure_schema()
                cursor.assert_not_called()

    def test_explicit_schema_role_keeps_auth_migrations(self):
        with (
            patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="schema"),
            patch("core.db.get_cursor", return_value=MagicMock()) as cursor,
        ):
            _ensure_schema()
            self.assertGreater(cursor.call_count, 0)

    def test_schema_gate_captures_warnings_during_domain_imports(self):
        import builtins
        import logging
        from services.cloud_runtime import schema

        real_import = builtins.__import__

        def warned_import(name, *args, **kwargs):
            if name == "services.startup":
                logging.getLogger("schema_import_test").warning("import DDL failed")
            return real_import(name, *args, **kwargs)

        with (
            patch("services.auth.schema._ensure_schema"),
            patch("services.startup._boot_schema_ddl"),
            patch("services.users.columns.ensure_user_profile_columns"),
            patch("services.cloud_tasks.store.ensure_table"),
            patch("services.cloud_runtime.schema.migrate_queue_schema"),
            patch("builtins.__import__", side_effect=warned_import),
        ):
            with self.assertRaisesRegex(RuntimeError, "Schema gate reported failures"):
                schema.migrate()

    def test_cloud_schema_audits_zero_policy_tables_without_disabling_rls(self):
        from core.rls import ensure_no_orphan_rls

        cursor = MagicMock()
        cursor.fetchall.return_value = [{"relname": "cloud_task_deliveries"}]
        context = MagicMock()
        context.__enter__.return_value = cursor
        with (
            patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="schema"),
            patch("core.db.get_cursor", return_value=context),
        ):
            self.assertEqual(ensure_no_orphan_rls(), ["cloud_task_deliveries"])
        self.assertTrue(
            all("DISABLE" not in call.args[0] for call in cursor.execute.call_args_list)
        )

    def test_fresh_application_import_has_no_database_access(self):
        source = """
from unittest.mock import patch
from core import db
with patch.object(db, "get_pool", side_effect=AssertionError("DB during import")) as pool:
    import app
    assert pool.call_count == 0, pool.call_count
"""
        root = Path(__file__).resolve().parents[2]
        for role in ("web", "worker"):
            with self.subTest(role=role):
                result = subprocess.run(
                    [sys.executable, "-c", source],
                    cwd=root,
                    env={**os.environ, "PEARNLY_RUNTIME_ROLE": role},
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()

"""client_submissions schema、迁移、状态与产品边界契约。"""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

from services.client_submission import schema

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "alembic" / "versions" / "0105_client_submissions.py"
SPEC = importlib.util.spec_from_file_location("client_submissions_0105", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)


def compact(sql: str) -> str:
    return " ".join(sql.split())


class ClientSubmissionSchemaTests(unittest.TestCase):
    def test_schema_pins_product_scope_status_and_idempotency_key(self):
        ddl = schema._TABLE
        self.assertIn("product_scope text NOT NULL DEFAULT 'erp'", ddl)
        self.assertIn("CHECK (product_scope = 'erp')", ddl)
        self.assertIn("'pending', 'delivered', 'failed', 'superseded'", ddl)
        self.assertIn(
            "engagement_id, source_document_type, source_document_id, source_revision", ddl
        )
        self.assertIn("cowork_history_id", ddl)
        self.assertIn("ON DELETE SET NULL", ddl)
        self.assertIn("status <> 'delivered' OR delivered_at IS NOT NULL", ddl)
        self.assertNotIn("cowork_history_id IS NOT NULL AND delivered_at", ddl)

    def test_schema_uses_participant_rls(self):
        class Cursor:
            def __init__(self):
                self.calls = []

            def execute(self, sql, params=None):
                self.calls.append((sql, params))

        cursor = Cursor()

        class Db:
            class Context:
                def __enter__(self):
                    return cursor

                def __exit__(self, *_args):
                    return False

            @staticmethod
            def get_cursor(**_kwargs):
                return Db.Context()

        with mock.patch("core.db.get_cursor", Db.get_cursor):
            schema.ensure_client_submission_schema()
        sql = "\n".join(statement for statement, _ in cursor.calls)
        self.assertIn("FOR SELECT", sql)
        self.assertIn("source_tenant_id::text = current_setting", sql)
        self.assertIn("target_tenant_id::text = current_setting", sql)
        self.assertIn("FOR INSERT WITH CHECK", sql)
        self.assertIn("e.status IN ('active', 'suspended')", sql)
        self.assertIn("FOR UPDATE USING (current_setting('app.bypass_rls'", sql)
        self.assertNotIn("FOR ALL", sql)

    def test_migration_matches_runtime_rls_and_current_head(self):
        statements = []
        with mock.patch.object(MIGRATION.op, "execute", side_effect=statements.append):
            MIGRATION.upgrade()
        sql = compact("\n".join(statements))

        self.assertEqual(MIGRATION.revision, "0105_client_submissions")
        self.assertEqual(MIGRATION.down_revision, "0104_accounting_engagements")
        for phrase in (
            "client_submission_participant_read",
            "client_submission_source_insert",
            "client_submission_system_update",
            "client_submission_system_delete",
            "e.status IN ('active', 'suspended')",
        ):
            self.assertIn(phrase, sql)
        self.assertNotIn("participant_tenant_isolation ON client_submissions FOR ALL", sql)


if __name__ == "__main__":
    unittest.main()

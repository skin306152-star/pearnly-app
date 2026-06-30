# -*- coding: utf-8 -*-
"""WP2 · platform_settings 建表 schema 契约 + 「显式 DISABLE RLS」回归守门。

Supabase 给 public 新表自动开 RLS → 零 policy = deny-all 孤儿(b8 incident)。schema 必须建表后
显式 DISABLE 两张表的 RLS,把终态钉死(不赖末步 ensure_no_orphan_rls 兜底·那步当次抛错就漏关)。
"""

import unittest
from unittest import mock

from core import db
from services.platform_settings import schema


class PlatformSettingsSchemaContractTests(unittest.TestCase):
    def test_db_reexports_same_object(self):
        self.assertTrue(hasattr(db, "ensure_platform_settings"))
        self.assertIs(db.ensure_platform_settings, schema.ensure_platform_settings)

    def test_creates_both_tables(self):
        joined = " ".join(schema._SQLS)
        self.assertIn("CREATE TABLE IF NOT EXISTS platform_settings", joined)
        self.assertIn("CREATE TABLE IF NOT EXISTS platform_setting_allowlist", joined)

    def test_explicitly_disables_rls_on_both_tables(self):
        disables = [s for s in schema._SQLS if "DISABLE ROW LEVEL SECURITY" in s]
        targets = {s.split()[2] for s in disables}  # ALTER TABLE <name> DISABLE ...
        self.assertEqual(targets, {"platform_settings", "platform_setting_allowlist"})

    def test_runs_each_stmt_in_own_cursor(self):
        calls = []

        class _Cur:
            def execute(self, sql, params=None):
                calls.append(sql)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with mock.patch.object(db, "get_cursor", return_value=_Cur()) as m:
            schema.ensure_platform_settings()
        self.assertEqual(m.call_count, len(schema._SQLS))
        self.assertTrue(all(k.kwargs.get("commit") is True for k in m.call_args_list))


if __name__ == "__main__":
    unittest.main()

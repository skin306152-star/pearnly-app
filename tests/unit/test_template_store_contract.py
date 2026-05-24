# -*- coding: utf-8 -*-
"""
ADR-006 S2 守门测试 · 模板映射库(services/importer/template_store)。

锁定:输入校验 / find 命中与未命中 / save upsert(占位符数==参数数,防漏传)/ 表缺失自愈 / ensure_table DDL。
全部 mock get_cursor · 不连真 DB。
"""

import unittest
from unittest import mock

from services.importer import template_store as ts


def _ctx(cur):
    c = mock.MagicMock()
    c.__enter__.return_value = cur
    return c


class FindMappingTests(unittest.TestCase):
    def test_hit_returns_mapping(self):
        cur = mock.MagicMock()
        cur.fetchone.return_value = {"mapping_json": {"date": 0, "balance": 4}}
        with mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)):
            out = ts.find_mapping("t1", "statement", "sig123")
        self.assertEqual(out, {"date": 0, "balance": 4})

    def test_miss_returns_none(self):
        cur = mock.MagicMock()
        cur.fetchone.return_value = None
        with mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)):
            self.assertIsNone(ts.find_mapping("t1", "statement", "sigX"))

    def test_bad_inputs(self):
        self.assertIsNone(ts.find_mapping("", "statement", "s"))
        self.assertIsNone(ts.find_mapping("t1", "bogus", "s"))
        self.assertIsNone(ts.find_mapping("t1", "statement", ""))

    def test_self_heal_on_missing_table(self):
        cur_ok = mock.MagicMock()
        cur_ok.fetchone.return_value = {"mapping_json": {"date": 0}}
        calls = {"n": 0}

        def fake_get_cursor(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise Exception('relation "import_template_mappings" does not exist')
            return _ctx(cur_ok)  # ensure_table 的几次 + 重试

        with mock.patch.object(ts, "get_cursor", side_effect=fake_get_cursor):
            out = ts.find_mapping("t1", "statement", "sig")
        self.assertEqual(out, {"date": 0})  # 建表后重试拿到


class SaveMappingTests(unittest.TestCase):
    def test_upsert_placeholder_param_match(self):
        cur = mock.MagicMock()
        with mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)):
            ok = ts.save_mapping(
                "t1",
                "statement",
                "sig",
                {"date": 0, "balance": 4},
                source="user",
                sample_headers=["date", "bal"],
                created_by="u1",
            )
        self.assertTrue(ok)
        sql, params = cur.execute.call_args[0][0], cur.execute.call_args[0][1]
        self.assertIn("INSERT INTO import_template_mappings", sql)
        self.assertIn("ON CONFLICT", sql)
        self.assertEqual(sql.count("%s"), len(params), f"placeholder/param mismatch: {sql}")

    def test_rejects_bad(self):
        self.assertFalse(ts.save_mapping("t1", "bogus", "s", {"date": 0}))
        self.assertFalse(ts.save_mapping("t1", "statement", "s", {}))
        self.assertFalse(ts.save_mapping("", "statement", "s", {"date": 0}))


class EnsureTableTests(unittest.TestCase):
    def test_runs_ddl(self):
        cur = mock.MagicMock()
        with mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)):
            ok = ts.ensure_table()
        self.assertTrue(ok)
        stmts = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(
            any("CREATE TABLE IF NOT EXISTS import_template_mappings" in s for s in stmts)
        )
        self.assertTrue(any("CREATE INDEX IF NOT EXISTS" in s for s in stmts))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""REFACTOR-WA 覆盖 · services/importer/template_store 未覆盖分支

补 test_template_store_contract 未覆盖的:list_mappings(带/不带 doc_type 过滤 · 行转换 ·
空 · 异常兜底)· delete_mapping(命中/未命中/异常)· ensure_table(pgcrypto 失败仍建表 · DDL 失败)·
find_mapping/save_mapping 的错误/自愈分支。全部 mock get_cursor · 不连真 DB · 0 逻辑改只加测试。
"""

import datetime
import unittest
from unittest import mock

from services.importer import template_store as ts


def _ctx(cur):
    c = mock.MagicMock()
    c.__enter__.return_value = cur
    return c


class ListMappingsTests(unittest.TestCase):
    def test_with_doc_type_filter(self):
        cur = mock.MagicMock()
        cur.fetchall.return_value = []
        with (
            mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)),
            mock.patch.object(ts, "get_cursor_rls", return_value=_ctx(cur)),
        ):
            out = ts.list_mappings("t1", "statement")
        self.assertEqual(out, [])
        sql, params = cur.execute.call_args[0][0], cur.execute.call_args[0][1]
        self.assertIn("AND document_type = %s", sql)
        self.assertEqual(params, ("t1", "statement"))

    def test_without_doc_type(self):
        cur = mock.MagicMock()
        cur.fetchall.return_value = []
        with (
            mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)),
            mock.patch.object(ts, "get_cursor_rls", return_value=_ctx(cur)),
        ):
            ts.list_mappings("t1")
        sql, params = cur.execute.call_args[0][0], cur.execute.call_args[0][1]
        self.assertNotIn("AND document_type", sql)
        self.assertEqual(params, ("t1",))

    def test_row_transform_id_str_and_created_at_iso(self):
        cur = mock.MagicMock()
        ts_dt = datetime.datetime(2026, 5, 30, 9, 0, 0)
        cur.fetchall.return_value = [
            {"id": 12345, "document_type": "gl", "created_at": ts_dt, "mapping_json": {"a": 0}}
        ]
        with (
            mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)),
            mock.patch.object(ts, "get_cursor_rls", return_value=_ctx(cur)),
        ):
            out = ts.list_mappings("t1")
        self.assertEqual(out[0]["id"], "12345")
        self.assertEqual(out[0]["created_at"], ts_dt.isoformat())

    def test_none_id_and_created_at_kept(self):
        cur = mock.MagicMock()
        cur.fetchall.return_value = [{"id": None, "created_at": None}]
        with (
            mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)),
            mock.patch.object(ts, "get_cursor_rls", return_value=_ctx(cur)),
        ):
            out = ts.list_mappings("t1")
        self.assertIsNone(out[0]["id"])
        self.assertIsNone(out[0]["created_at"])

    def test_exception_returns_empty(self):
        with (
            mock.patch.object(ts, "get_cursor", side_effect=Exception("boom")),
            mock.patch.object(ts, "get_cursor_rls", side_effect=Exception("boom")),
        ):
            self.assertEqual(ts.list_mappings("t1"), [])


class DeleteMappingTests(unittest.TestCase):
    def test_hit_returns_true(self):
        cur = mock.MagicMock()
        cur.rowcount = 1
        with (
            mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)),
            mock.patch.object(ts, "get_cursor_rls", return_value=_ctx(cur)),
        ):
            self.assertTrue(ts.delete_mapping("t1", "m1"))
        sql = cur.execute.call_args[0][0]
        self.assertIn("DELETE FROM import_template_mappings", sql)

    def test_miss_returns_false(self):
        cur = mock.MagicMock()
        cur.rowcount = 0
        with (
            mock.patch.object(ts, "get_cursor", return_value=_ctx(cur)),
            mock.patch.object(ts, "get_cursor_rls", return_value=_ctx(cur)),
        ):
            self.assertFalse(ts.delete_mapping("t1", "m1"))

    def test_exception_returns_false(self):
        with (
            mock.patch.object(ts, "get_cursor", side_effect=Exception("boom")),
            mock.patch.object(ts, "get_cursor_rls", side_effect=Exception("boom")),
        ):
            self.assertFalse(ts.delete_mapping("t1", "m1"))


class EnsureTableBranchTests(unittest.TestCase):
    def test_pgcrypto_failure_still_creates_table(self):
        cur = mock.MagicMock()
        calls = {"n": 0}

        def fake(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise Exception("no pgcrypto")  # first get_cursor (extension) fails
            return _ctx(cur)

        with (
            mock.patch.object(ts, "get_cursor", side_effect=fake),
            mock.patch.object(ts, "get_cursor_rls", side_effect=fake),
        ):
            self.assertTrue(ts.ensure_table())

    def test_ddl_failure_returns_false(self):
        calls = {"n": 0}

        def fake(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                return _ctx(mock.MagicMock())  # pgcrypto ok
            raise Exception("ddl boom")  # table DDL fails

        with (
            mock.patch.object(ts, "get_cursor", side_effect=fake),
            mock.patch.object(ts, "get_cursor_rls", side_effect=fake),
        ):
            self.assertFalse(ts.ensure_table())


class FindSaveErrorBranchTests(unittest.TestCase):
    def test_find_generic_exception_returns_none(self):
        with (
            mock.patch.object(ts, "get_cursor", side_effect=Exception("connection lost")),
            mock.patch.object(ts, "get_cursor_rls", side_effect=Exception("connection lost")),
        ):
            self.assertIsNone(ts.find_mapping("t1", "statement", "sig"))

    def test_find_self_heal_retry_still_fails(self):
        calls = {"n": 0}

        def fake(*a, **k):
            calls["n"] += 1
            # 1: original query → table missing; subsequent (ensure_table + retry) all raise
            raise Exception('relation "import_template_mappings" does not exist')

        with (
            mock.patch.object(ts, "get_cursor", side_effect=fake),
            mock.patch.object(ts, "get_cursor_rls", side_effect=fake),
        ):
            self.assertIsNone(ts.find_mapping("t1", "statement", "sig"))

    def test_save_self_heal_success(self):
        ok_cur = mock.MagicMock()
        calls = {"n": 0}

        def fake(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise Exception('relation "import_template_mappings" does not exist')
            return _ctx(ok_cur)  # ensure_table (2x) + retry upsert succeed

        with (
            mock.patch.object(ts, "get_cursor", side_effect=fake),
            mock.patch.object(ts, "get_cursor_rls", side_effect=fake),
        ):
            self.assertTrue(ts.save_mapping("t1", "statement", "sig", {"date": 0}))

    def test_save_self_heal_ensure_table_fails(self):
        def fake(*a, **k):
            # original upsert: table missing; ensure_table's DDL also fails → ensure_table False
            raise Exception('relation "import_template_mappings" does not exist')

        with (
            mock.patch.object(ts, "get_cursor", side_effect=fake),
            mock.patch.object(ts, "get_cursor_rls", side_effect=fake),
        ):
            self.assertFalse(ts.save_mapping("t1", "statement", "sig", {"date": 0}))

    def test_save_generic_exception_returns_false(self):
        with (
            mock.patch.object(ts, "get_cursor", side_effect=Exception("connection lost")),
            mock.patch.object(ts, "get_cursor_rls", side_effect=Exception("connection lost")),
        ):
            self.assertFalse(ts.save_mapping("t1", "statement", "sig", {"date": 0}))


if __name__ == "__main__":
    unittest.main()

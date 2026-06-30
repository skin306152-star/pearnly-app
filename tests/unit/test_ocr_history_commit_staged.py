# -*- coding: utf-8 -*-
"""commit_staged_ocr_history:第4步完成把草稿(staged=TRUE)翻成正式落进识别记录。

钉死:① 空 id 不碰库 ② 只翻仍是草稿的(staged=TRUE 守卫·幂等)③ 按本人 / 本租户限定归属。
从 core.db 取(re-export),避免直接 import mutations 触发循环导入。
"""

import unittest
from unittest import mock

import core.db as cdb
from core.db import commit_staged_ocr_history


class _Cur:
    def __init__(self, rowcount=2):
        self.rowcount = rowcount
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((" ".join(sql.split()), params))


class _Ctx:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class CommitStagedTests(unittest.TestCase):
    def test_empty_ids_no_db(self):
        with mock.patch.object(cdb, "get_cursor_rls") as m:
            self.assertEqual(commit_staged_ocr_history("u", []), 0)
            self.assertEqual(commit_staged_ocr_history("u", [None, ""]), 0)
            m.assert_not_called()

    def test_commits_user_scope_only_staged(self):
        cur = _Cur(rowcount=3)
        with mock.patch.object(cdb, "get_cursor_rls", return_value=_Ctx(cur)):
            n = commit_staged_ocr_history("u1", ["a", "b"])
        self.assertEqual(n, 3)
        sql, params = cur.executed[0]
        self.assertIn("staged = FALSE", sql)  # 翻成正式
        self.assertIn("staged = TRUE", sql)  # 只翻仍是草稿的(幂等)
        self.assertIn("user_id = %s::uuid", sql)
        self.assertEqual(params, (["a", "b"], "u1"))

    def test_tenant_scope(self):
        cur = _Cur(rowcount=1)
        with mock.patch.object(cdb, "get_cursor_rls", return_value=_Ctx(cur)):
            commit_staged_ocr_history("u1", ["a"], tenant_id="t1")
        sql, params = cur.executed[0]
        self.assertIn("tenant_id = %s::uuid", sql)
        self.assertEqual(params, (["a"], "t1"))


if __name__ == "__main__":
    unittest.main()

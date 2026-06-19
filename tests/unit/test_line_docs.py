# -*- coding: utf-8 -*-
"""LINE 来源进项单查询:语义(source='line'/可撤状态/ws+tenant 隔离/今天时区/最近倒序)。"""

import unittest

from services.purchase import line_docs


class _Cur:
    def __init__(self):
        self.sql = ""
        self.params = ()

    def execute(self, sql, params):
        self.sql, self.params = sql, params

    def fetchall(self):
        return [{"id": "a"}]


class FindRecentTests(unittest.TestCase):
    def test_recent_query_semantics(self):
        cur = _Cur()
        rows = line_docs.find_recent_line_docs(cur, tenant_id="T1", workspace_client_id=1, limit=3)
        self.assertEqual(rows, [{"id": "a"}])
        self.assertIn("d.source = 'line'", cur.sql)
        self.assertIn("d.status IN ('posted', 'draft')", cur.sql)
        self.assertIn("d.tenant_id = %s", cur.sql)
        self.assertIn("d.workspace_client_id = %s", cur.sql)
        self.assertIn("ORDER BY d.created_at DESC", cur.sql)
        self.assertIn("LIMIT %s", cur.sql)
        self.assertEqual(cur.params, ("T1", 1, 3))


class FindTodayTests(unittest.TestCase):
    def test_today_query_uses_bangkok_tz(self):
        cur = _Cur()
        line_docs.find_today_line_docs(cur, tenant_id="T1", workspace_client_id=2)
        self.assertIn("Asia/Bangkok", cur.sql)
        self.assertIn("d.source = 'line'", cur.sql)
        self.assertEqual(cur.params, ("T1", 2))


if __name__ == "__main__":
    unittest.main()

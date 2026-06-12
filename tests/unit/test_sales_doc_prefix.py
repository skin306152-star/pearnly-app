# -*- coding: utf-8 -*-
"""开票连号前缀 per-主体 覆盖(引导步③ doc_prefix 的真消费)。

优先级:显式请求 prefix > 主体级 doc_prefix > 租户级 number_prefix > 单据类型默认。
锁定 doc_prefix 不是死字段——真正参与开票取号。FakeCursor mock,不打真实 DB。
"""

import unittest

from services.sales import numbering


class FakeCursor:
    def __init__(self, fetchone=None):
        self._fetchone = fetchone
        self.last_sql = ""
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params

    def fetchone(self):
        return self._fetchone


class ResolvePrefixTests(unittest.TestCase):
    def test_explicit_request_wins(self):
        self.assertEqual(numbering.resolve_prefix("PAY", "WS", "TEN", "TX"), "PAY")

    def test_workspace_over_tenant(self):
        self.assertEqual(numbering.resolve_prefix(None, "WS", "TEN", "TX"), "WS")

    def test_tenant_when_no_workspace_prefix(self):
        self.assertEqual(numbering.resolve_prefix(None, None, "TEN", "TX"), "TEN")

    def test_falls_back_to_default(self):
        self.assertEqual(numbering.resolve_prefix(None, None, None, "TX"), "TX")


class WorkspaceDocPrefixLookupTests(unittest.TestCase):
    def test_returns_prefix_when_set(self):
        cur = FakeCursor(fetchone={"doc_prefix": "AB"})
        self.assertEqual(numbering.workspace_doc_prefix(cur, "t1", 7), "AB")
        self.assertIn("doc_prefix", cur.last_sql)
        self.assertEqual(cur.last_params, (7, "t1"))

    def test_none_when_no_ws_id(self):
        cur = FakeCursor(fetchone={"doc_prefix": "AB"})
        self.assertIsNone(numbering.workspace_doc_prefix(cur, "t1", None))
        self.assertEqual(cur.last_sql, "")  # 无 ws_id 直接短路不查库

    def test_none_when_blank_or_missing(self):
        self.assertIsNone(
            numbering.workspace_doc_prefix(FakeCursor(fetchone={"doc_prefix": ""}), "t1", 7)
        )
        self.assertIsNone(numbering.workspace_doc_prefix(FakeCursor(fetchone=None), "t1", 7))


if __name__ == "__main__":
    unittest.main()

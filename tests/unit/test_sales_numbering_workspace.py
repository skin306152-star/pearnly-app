# -*- coding: utf-8 -*-
"""PO-7b 守门:连号计数器按主体(document_number_sequences)。

证明:
  - workspace_client_id 给了 → INSERT/SELECT/UPDATE/ON CONFLICT 的键含 workspace_client_id;
  - 两个主体在同一 (doc_type, prefix, period) 下各自独立连续、互不串号;
  - None → 旧 4 列键(迁移前兼容路径,号序与历史逐张一致)。
内存模拟 document_number_sequences 行为(不触真库 · 同 cursor-based DAL 测试范式)。
"""

import unittest
from datetime import date

from services.sales import numbering


class _SeqCur:
    """够用的内存连号表:按 ON CONFLICT 键存 next_number,模拟 INSERT/SELECT FOR UPDATE/UPDATE。"""

    def __init__(self):
        self.rows = {}  # key tuple -> next_number
        self._last_key = None
        self._last_n = None
        self.seen_sql = []

    def execute(self, sql, params=None):
        self.seen_sql.append(sql)
        p = list(params) if params is not None else []
        if sql.startswith("INSERT"):
            *key, start = p
            self.rows.setdefault(tuple(key), start)
        elif sql.startswith("SELECT"):
            self._last_key = tuple(p)
            self._last_n = self.rows[self._last_key]
        elif sql.startswith("UPDATE"):
            self.rows[tuple(p)] += 1

    def fetchone(self):
        return {"next_number": self._last_n}


class NumberingWorkspaceTests(unittest.TestCase):
    def _alloc(self, cur, ws):
        return numbering.allocate(
            cur,
            tenant_id="t1",
            doc_type="receipt",
            prefix="INV",
            reset=numbering.RESET_YEARLY,
            on=date(2026, 6, 8),
            workspace_client_id=ws,
        )

    def test_two_subjects_number_independently(self):
        cur = _SeqCur()
        a1, _ = self._alloc(cur, 10)
        a2, _ = self._alloc(cur, 10)
        b1, _ = self._alloc(cur, 20)  # 另一主体:从头开始,不接主体 10 的号
        a3, _ = self._alloc(cur, 10)
        self.assertEqual([a1, a2, a3], ["INV2026-00001", "INV2026-00002", "INV2026-00003"])
        self.assertEqual(b1, "INV2026-00001")

    def test_key_includes_workspace(self):
        cur = _SeqCur()
        self._alloc(cur, 7)
        joined = " ".join(cur.seen_sql)
        self.assertIn("workspace_client_id", joined)
        self.assertIn(
            "ON CONFLICT (tenant_id, workspace_client_id, doc_type, prefix, period)", joined
        )

    def test_none_keeps_legacy_four_col_key(self):
        cur = _SeqCur()
        disp, _ = numbering.allocate(
            cur,
            tenant_id="t1",
            doc_type="receipt",
            prefix="INV",
            reset=numbering.RESET_YEARLY,
            on=date(2026, 6, 8),
            workspace_client_id=None,
        )
        joined = " ".join(cur.seen_sql)
        self.assertEqual(disp, "INV2026-00001")
        self.assertNotIn("workspace_client_id", joined)
        self.assertIn("ON CONFLICT (tenant_id, doc_type, prefix, period)", joined)


if __name__ == "__main__":
    unittest.main()

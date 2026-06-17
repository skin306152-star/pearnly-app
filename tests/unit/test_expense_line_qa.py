# -*- coding: utf-8 -*-
"""线 B 批4 · 查账(DB 真查)+ 问答(知识中心带出处·诚实兜底)。"""

import unittest
from decimal import Decimal

from services.expense import line_qa


class _FakeCursor:
    def __init__(self, fetchone=None):
        self.calls = []
        self._one = fetchone

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._one


class _MultiCursor:
    """fetchall 返回预置行(供 summary/detail 测)。"""

    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._rows


class MonthSummaryTests(unittest.TestCase):
    def test_summary_totals_and_breakdown(self):
        cur = _MultiCursor(
            [
                {"cat": "ต้นทุนสินค้า", "amt": Decimal("300"), "n": 1},
                {"cat": "ค่าอาหารและรับรอง", "amt": Decimal("170"), "n": 2},
            ]
        )
        s = line_qa.month_summary(cur, tenant_id="t", workspace_client_id=1)
        self.assertEqual(s["total"], Decimal("470"))
        self.assertEqual(s["count"], 3)
        self.assertEqual(s["by_category"][0]["name"], "ต้นทุนสินค้า")
        self.assertIn("FROM purchase_docs", cur.calls[0][0])
        self.assertIn("status = 'posted'", cur.calls[0][0])

    def test_summary_empty(self):
        s = line_qa.month_summary(_MultiCursor([]), tenant_id="t", workspace_client_id=1)
        self.assertEqual(s["count"], 0)
        self.assertEqual(s["total"], Decimal("0"))


class MonthDetailTests(unittest.TestCase):
    def test_detail_rows(self):
        import datetime

        cur = _MultiCursor(
            [
                {
                    "id": "D1",
                    "doc_date": datetime.date(2026, 6, 13),
                    "amt": Decimal("300"),
                    "cat": "X",
                    "vendor": "V",
                }
            ]
        )
        rows = line_qa.month_detail(cur, tenant_id="t", workspace_client_id=1)
        self.assertEqual(rows[0]["id"], "D1")
        self.assertEqual(rows[0]["date"], "2026-06-13")
        self.assertEqual(rows[0]["amount"], Decimal("300"))
        self.assertEqual(rows[0]["vendor"], "V")


class KnowledgeAnswerTests(unittest.TestCase):
    def test_degrades_to_none_on_failure(self):
        # 知识检索内部任何异常 → None(调用方诚实兜底"没找到"·绝不编造)
        out = line_qa.knowledge_answer(_FakeCursor(), tenant_id="t", question="VAT คิดยังไง")
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()

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


class MonthSpendingTests(unittest.TestCase):
    def test_sums_confirmed_this_month_scoped(self):
        cur = _FakeCursor(fetchone={"total": Decimal("1234.50")})
        total = line_qa.month_spending(cur, tenant_id="t1", workspace_client_id=7)
        self.assertEqual(total, Decimal("1234.50"))
        sql, params = cur.calls[0]
        self.assertIn("status = 'confirmed'", sql)
        self.assertIn("date_trunc('month', now())", sql)
        self.assertIn("tenant_id = %s AND workspace_client_id = %s", sql)
        self.assertEqual(params, ("t1", 7))

    def test_zero_when_none(self):
        cur = _FakeCursor(fetchone={"total": 0})
        self.assertEqual(
            line_qa.month_spending(cur, tenant_id="t", workspace_client_id=1), Decimal("0")
        )


class KnowledgeAnswerTests(unittest.TestCase):
    def test_degrades_to_none_on_failure(self):
        # 知识检索内部任何异常 → None(调用方诚实兜底"没找到"·绝不编造)
        out = line_qa.knowledge_answer(_FakeCursor(), tenant_id="t", question="VAT คิดยังไง")
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()

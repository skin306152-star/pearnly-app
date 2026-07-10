# -*- coding: utf-8 -*-
"""POS 小票行 DAL 守门测试(services/pos/sales_store · 成本快照列)。

锁定:insert_line 把 cost_total 当钱字段走 Decimal 参数化(不是裸浮点拼 SQL)、None 原样
传(诚实占位,不当 0);list_lines 把 cost_total 带出来供报表/详情用。
"""

import unittest
from decimal import Decimal

from services.pos import sales_store


class FakeCursor:
    def __init__(self, ones=None):
        self.calls = []
        self._ones = list(ones or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    @property
    def last_sql(self):
        return self.calls[-1][0]

    @property
    def last_params(self):
        return self.calls[-1][1]


class InsertLineCostTests(unittest.TestCase):
    def test_cost_total_column_present_and_decimal(self):
        cur = FakeCursor(ones=[{"id": "l1", "batch_id": "b1", "qty_base": Decimal("2")}])
        sales_store.insert_line(
            cur,
            tenant_id="t1",
            sale_id="s1",
            fields={
                "product_id": "p1",
                "sell_unit": "ea",
                "unit_factor": 1,
                "qty": 2,
                "qty_base": 2,
                "unit_price": 10,
                "line_discount": 0,
                "vat_applicable": True,
                "batch_id": "b1",
                "refund_of_line_id": None,
                "line_total": 20,
                "cost_total": "18.5",
            },
        )
        self.assertIn("cost_total", cur.last_sql)
        self.assertIn(Decimal("18.5"), cur.last_params)

    def test_cost_total_none_passes_through_not_coerced_to_zero(self):
        cur = FakeCursor(ones=[{"id": "l1", "batch_id": None, "qty_base": Decimal("2")}])
        sales_store.insert_line(
            cur,
            tenant_id="t1",
            sale_id="s1",
            fields={
                "product_id": "p1",
                "sell_unit": "ea",
                "unit_factor": 1,
                "qty": 2,
                "qty_base": 2,
                "unit_price": 10,
                "line_discount": 0,
                "vat_applicable": True,
                "batch_id": None,
                "refund_of_line_id": None,
                "line_total": 20,
                "cost_total": None,
            },
        )
        self.assertIsNone(cur.last_params[-1])  # cost_total 是最后一列 · 原样传 None,不是 0


class ListLinesTests(unittest.TestCase):
    def test_selects_cost_total(self):
        cur = FakeCursor(ones=[None])
        cur.fetchall = lambda: []
        sales_store.list_lines(cur, tenant_id="t1", sale_id="s1")
        self.assertIn("cost_total", cur.calls[0][0])


if __name__ == "__main__":
    unittest.main()

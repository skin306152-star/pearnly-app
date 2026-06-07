# -*- coding: utf-8 -*-
"""POS 销售报表聚合纯逻辑守门测试(POS 项目 · PO-B6)。

不连库:金额/数量字符串化、日期窗口片段(半开区间)、报表装配形状 + 客单价计算。真聚合
SQL(笛卡尔积防护)由 _e2e_po_b6 真库覆盖。"""

import unittest
from datetime import date
from decimal import Decimal

from services.pos import report


class _Cur:
    """按 execute 顺序回放预置结果:每次 execute pop 一组 (one, all)。"""

    def __init__(self, scripted):
        self._scripted = list(scripted)
        self._cur = None
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        self._cur = self._scripted.pop(0)

    def fetchone(self):
        return self._cur[0]

    def fetchall(self):
        return self._cur[1]


class FormatTests(unittest.TestCase):
    def test_money_and_qty(self):
        self.assertEqual(report._money(Decimal("12480")), "12480.00")
        self.assertEqual(report._money(None), "0.00")
        self.assertEqual(report._qty("412"), "412.000")

    def test_range_half_open(self):
        clause, params = report._range("sold_at", date(2026, 6, 1), date(2026, 6, 7))
        self.assertIn(">= %s", clause)
        self.assertIn("< %s", clause)
        self.assertEqual(params[0], date(2026, 6, 1))
        self.assertEqual(params[1], date(2026, 6, 8))  # to + 1 天(含 to 当天)

    def test_range_unbounded(self):
        clause, params = report._range("sold_at", None, None)
        self.assertEqual(clause, "")
        self.assertEqual(params, [])


class AssemblyTests(unittest.TestCase):
    def test_report_shape_and_avg_ticket(self):
        scripted = [
            ({"gross": Decimal("300"), "sales_count": 2, "refund": Decimal("20")}, None),  # kpi
            (None, [{"d": date(2026, 6, 1), "gross": Decimal("300")}]),  # by_day
            (None, [{"method": "cash", "amount": Decimal("200")}]),  # by_method
            (
                None,
                [
                    {
                        "product_id": "p1",
                        "name_th": "โค้ก",
                        "name_en": "Coke",
                        "name_zh": "可乐",
                        "qty": Decimal("12"),
                        "gross": Decimal("180"),
                    }
                ],
            ),  # top_products
            (
                None,
                [{"cashier_id": "c1", "name": "Nok", "sales_count": 2, "gross": Decimal("300")}],
            ),
        ]
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["kpi"]["gross"], "300.00")
        self.assertEqual(out["kpi"]["avg_ticket"], "150.00")  # 300/2
        self.assertEqual(out["kpi"]["refund"], "20.00")
        self.assertEqual(out["by_day"][0], {"date": "2026-06-01", "gross": "300.00"})
        self.assertEqual(out["by_method"], {"cash": "200.00"})
        self.assertEqual(out["top_products"][0]["name"], {"th": "โค้ก", "en": "Coke", "zh": "可乐"})
        self.assertEqual(out["top_products"][0]["qty"], "12.000")
        self.assertEqual(out["by_cashier"][0]["cashier_id"], "c1")

    def test_avg_ticket_zero_when_no_sales(self):
        scripted = [
            ({"gross": Decimal("0"), "sales_count": 0, "refund": Decimal("0")}, None),
            (None, []),
            (None, []),
            (None, []),
            (None, []),
        ]
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["kpi"]["avg_ticket"], "0.00")  # 不除零


if __name__ == "__main__":
    unittest.main()

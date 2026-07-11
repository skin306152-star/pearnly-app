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
            ({"cost": Decimal("120"), "complete": True}, None),  # kpi cost_agg
            (None, [{"d": date(2026, 6, 1), "gross": Decimal("300")}]),  # by_day
            (
                None,
                [{"d": date(2026, 6, 1), "cost": Decimal("120"), "complete": True}],
            ),  # by_day cost
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
                        "cost": Decimal("70"),
                        "complete": True,
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
        self.assertEqual(out["kpi"]["cost"], "120.00")  # 净 COGS(此桶无退货行 → 与售出成本相等)
        self.assertEqual(out["kpi"]["gross_profit"], "160.00")  # 净口径:300 - 20(退货) - 120
        self.assertTrue(out["kpi"]["cost_complete"])
        self.assertEqual(
            out["by_day"][0],
            {
                "date": "2026-06-01",
                "gross": "300.00",
                "cost": "120.00",
                "gross_profit": "180.00",
                "cost_complete": True,
            },
        )
        self.assertEqual(out["by_method"], {"cash": "200.00"})
        self.assertEqual(out["top_products"][0]["name"], {"th": "โค้ก", "en": "Coke", "zh": "可乐"})
        self.assertEqual(out["top_products"][0]["qty"], "12.000")
        self.assertEqual(out["top_products"][0]["cost"], "70.00")
        self.assertEqual(out["top_products"][0]["gross_profit"], "110.00")  # 180 - 70
        self.assertEqual(out["by_cashier"][0]["cashier_id"], "c1")

    def test_avg_ticket_zero_when_no_sales(self):
        scripted = [
            ({"gross": Decimal("0"), "sales_count": 0, "refund": Decimal("0")}, None),
            ({"cost": Decimal("0"), "complete": True}, None),
            (None, []),
            (None, []),
            (None, []),
            (None, []),
            (None, []),
        ]
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["kpi"]["avg_ticket"], "0.00")  # 不除零
        self.assertEqual(out["kpi"]["gross_profit"], "0.00")


class CostHonestyTests(unittest.TestCase):
    """成本不完整(有老单据/无成本记录)时毛利必须诚实置空,不许拿部分数据瞎猜。"""

    def test_kpi_gross_profit_null_when_cost_incomplete(self):
        scripted = [
            ({"gross": Decimal("300"), "sales_count": 2, "refund": Decimal("0")}, None),
            ({"cost": Decimal("50"), "complete": False}, None),  # 有行成本未知
            (None, []),
            (None, []),
            (None, []),
            (None, []),
            (None, []),
        ]
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertIsNone(out["kpi"]["gross_profit"])
        self.assertFalse(out["kpi"]["cost_complete"])
        self.assertEqual(out["kpi"]["cost"], "50.00")  # 已知部分仍展示,但不当最终毛利

    def test_by_day_and_top_products_null_when_incomplete(self):
        scripted = [
            ({"gross": Decimal("100"), "sales_count": 1, "refund": Decimal("0")}, None),
            ({"cost": Decimal("0"), "complete": True}, None),
            (None, [{"d": date(2026, 6, 2), "gross": Decimal("100")}]),
            (None, [{"d": date(2026, 6, 2), "cost": Decimal("40"), "complete": False}]),
            (None, []),
            (
                None,
                [
                    {
                        "product_id": "p2",
                        "name_th": "น้ำ",
                        "name_en": "Water",
                        "name_zh": "水",
                        "qty": Decimal("5"),
                        "gross": Decimal("100"),
                        "cost": Decimal("40"),
                        "complete": False,
                    }
                ],
            ),
            (None, []),
        ]
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertIsNone(out["by_day"][0]["gross_profit"])
        self.assertFalse(out["by_day"][0]["cost_complete"])
        self.assertIsNone(out["top_products"][0]["gross_profit"])
        self.assertFalse(out["top_products"][0]["cost_complete"])

    def test_by_day_missing_cost_bucket_treated_as_unknown(self):
        """理论上不该发生(每笔已完成销售必有行),但防御:某天没匹配到 cost 分组 → 置空不猜 0。"""
        scripted = [
            ({"gross": Decimal("50"), "sales_count": 1, "refund": Decimal("0")}, None),
            ({"cost": Decimal("0"), "complete": True}, None),
            (None, [{"d": date(2026, 6, 3), "gross": Decimal("50")}]),
            (None, []),  # cost_by_day 空 · 无该日分组
            (None, []),
            (None, []),
            (None, []),
        ]
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertIsNone(out["by_day"][0]["cost"])
        self.assertIsNone(out["by_day"][0]["gross_profit"])
        self.assertFalse(out["by_day"][0]["cost_complete"])


class RefundNetProfitTests(unittest.TestCase):
    """毛利净口径:退货从毛利底线回冲(营收扣退货、COGS 扣退货回冲成本),不再虚高。

    _cost_agg 已把退货行(负成本)算进净 COGS,故 cost 参数在含退货桶里就是净额。"""

    def _run(self, *, gross, refund, net_cost, complete=True):
        scripted = [
            ({"gross": Decimal(gross), "sales_count": 1, "refund": Decimal(refund)}, None),
            ({"cost": Decimal(net_cost), "complete": complete}, None),
            (None, []),
            (None, []),
            (None, []),
            (None, []),
            (None, []),
        ]
        return report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)

    def test_full_refund_zeroes_profit(self):
        """卖฿100(成本60)全退:gross=100/refund=100/净COGS=0 → 毛利=0(非虚高的 40)。"""
        out = self._run(gross="100", refund="100", net_cost="0")["kpi"]
        self.assertEqual(out["gross"], "100.00")  # gross 口径不变(仍是 sale 营收)
        self.assertEqual(out["refund"], "100.00")
        self.assertEqual(out["cost"], "0.00")  # 净 COGS = 60 售出 − 60 退货回冲
        self.assertEqual(out["gross_profit"], "0.00")  # 100 - 100 - 0

    def test_partial_refund_net_profit(self):
        """半退:营收净 50、净 COGS 30 → 毛利 20。"""
        out = self._run(gross="100", refund="50", net_cost="30")["kpi"]
        self.assertEqual(out["gross_profit"], "20.00")  # 100 - 50 - 30

    def test_incomplete_cost_null_even_with_refund(self):
        """退货行/售出行有 None 成本 → 净 COGS 不齐 → 毛利诚实置空(不拿假 0 冲)。"""
        out = self._run(gross="100", refund="100", net_cost="0", complete=False)["kpi"]
        self.assertIsNone(out["gross_profit"])
        self.assertFalse(out["cost_complete"])


if __name__ == "__main__":
    unittest.main()

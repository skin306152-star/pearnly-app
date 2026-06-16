# -*- coding: utf-8 -*-
"""库存读侧聚合守门测试(POS 项目 · PO-A3)。

锁定:① stock_overview 用预聚合子查询取均价(防 stock×batches 笛卡尔积把库存翻倍 · 实测 bug
回归)② 状态 low/ok/out + summary 计数逻辑 ③ filter 筛选。
"""

import unittest
from decimal import Decimal

from services.inventory import queries


class FakeCursor:
    def __init__(self, alls):
        self.calls = []
        self._alls = list(alls)

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._alls.pop(0) if self._alls else []


def _prow(qty, min_stock=None, avg_cost=None, image_url=None):
    return {
        "product_id": "p1",
        "name_th": "ยา",
        "name_en": None,
        "name_zh": None,
        "barcode": None,
        "image_url": image_url,
        "base_unit": "เม็ด",
        "min_stock": Decimal(str(min_stock)) if min_stock is not None else None,
        "default_cost": None,
        "qty_on_hand": Decimal(str(qty)),
        "avg_cost": Decimal(str(avg_cost)) if avg_cost is not None else None,
    }


class StockOverviewSqlTests(unittest.TestCase):
    def test_uses_preaggregated_batch_subquery_not_cartesian_join(self):
        cur = FakeCursor([[], []])
        queries.stock_overview(cur, tenant_id="t", workspace_client_id=9)
        sql = cur.calls[0][0]
        self.assertIn("AVG(unit_cost) AS avg_cost FROM inventory_batches", sql)
        # 不得直接 join inventory_batches(会笛卡尔积翻倍库存)
        self.assertNotIn("LEFT JOIN inventory_batches b ON", sql)

    def test_products_filtered_by_workspace(self):
        # PO-5:商品列表按套账隔离(不再只 p.tenant_id),批次均价子查询同步按套账。
        cur = FakeCursor([[], []])
        queries.stock_overview(cur, tenant_id="t", workspace_client_id=9)
        sql = cur.calls[0][0]
        self.assertIn("p.workspace_client_id = %s", sql)
        self.assertIn("WHERE tenant_id = %s AND workspace_client_id = %s", sql)  # 批次子查询


class StatusAndSummaryTests(unittest.TestCase):
    def test_status_low_ok_out(self):
        cur = FakeCursor(
            [[_prow(80, min_stock=100, avg_cost=2, image_url="/api/uploads/image/t/x.jpg")], []]
        )
        out = queries.stock_overview(cur, tenant_id="t", workspace_client_id=9)
        item = out["items"][0]
        self.assertEqual(item["status"], "low")
        self.assertEqual(item["qty_on_hand"], 80.0)
        self.assertEqual(item["image_url"], "/api/uploads/image/t/x.jpg")  # 库存图随商品同步
        self.assertEqual(out["summary"]["low_count"], 1)
        self.assertEqual(out["summary"]["sku_count"], 1)
        self.assertEqual(out["summary"]["stock_value"], 160.0)  # 80×2 · 不翻倍

    def test_out_of_stock(self):
        cur = FakeCursor([[_prow(0, min_stock=10)], []])
        out = queries.stock_overview(cur, tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["items"][0]["status"], "out")
        self.assertEqual(out["summary"]["out_count"], 1)
        self.assertEqual(out["summary"]["sku_count"], 0)  # 0 库存不计 sku

    def test_filter_low_excludes_ok(self):
        cur = FakeCursor([[_prow(500, min_stock=10)], []])
        out = queries.stock_overview(cur, tenant_id="t", workspace_client_id=9, filter_="low")
        self.assertEqual(out["items"], [])


class NearExpiryTests(unittest.TestCase):
    def test_query_filters_expiry_window(self):
        cur = FakeCursor([[]])
        queries.near_expiry(cur, tenant_id="t", workspace_client_id=9, days=30)
        sql = cur.calls[0][0]
        self.assertIn("b.expiry_date <= CURRENT_DATE + %s", sql)
        self.assertIn("ORDER BY b.expiry_date ASC", sql)
        self.assertEqual(cur.calls[0][1], ("t", 9, 30))


if __name__ == "__main__":
    unittest.main()

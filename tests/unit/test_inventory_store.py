# -*- coding: utf-8 -*-
"""库存 store DAL 守门测试(POS 项目 · PO-A3)。

锁定:apply_stock_delta 锁行后 UPDATE / 无行 INSERT(物化)· batch/warehouse get-or-create ·
insert_txn 参数化 + 每语句 WHERE tenant_id · qty/cost 走 Decimal。
"""

import unittest
from decimal import Decimal

from services.inventory import store


class FakeCursor:
    def __init__(self, ones=None, manys=None):
        self.calls = []
        self._ones = list(ones or [])
        self._manys = list(manys or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return self._manys.pop(0) if self._manys else []

    @property
    def last_sql(self):
        return self.calls[-1][0]

    @property
    def last_params(self):
        return self.calls[-1][1]


class SumOnHandForUpdateTests(unittest.TestCase):
    def test_sums_all_batches_and_locks(self):
        cur = FakeCursor(
            manys=[[{"q": Decimal("100")}, {"q": Decimal("100")}, {"q": Decimal("50")}]]
        )
        total = store.sum_on_hand_for_update(cur, tenant_id="t-1", product_id="p", warehouse_id=1)
        self.assertEqual(total, Decimal("250"))  # Python 求和(聚合不能 FOR UPDATE)
        self.assertIn("FOR UPDATE", cur.calls[0][0])  # 锁全部批次行防并发
        self.assertNotIn("batch_id", cur.calls[0][0])  # 跨所有批次 · 不按 batch 过滤

    def test_no_rows_is_zero(self):
        cur = FakeCursor(manys=[[]])
        total = store.sum_on_hand_for_update(cur, tenant_id="t-1", product_id="p", warehouse_id=1)
        self.assertEqual(total, Decimal("0"))


class ApplyStockDeltaTests(unittest.TestCase):
    def test_existing_row_locks_then_updates(self):
        cur = FakeCursor(
            ones=[{"id": "s1", "qty_on_hand": Decimal("5")}, {"qty_on_hand": Decimal("15")}]
        )
        qty = store.apply_stock_delta(
            cur,
            tenant_id="t-1",
            workspace_client_id=9,
            product_id="p",
            warehouse_id=1,
            batch_id=None,
            qty_delta=10,
        )
        self.assertEqual(qty, Decimal("15"))
        self.assertIn("FOR UPDATE", cur.calls[0][0])
        self.assertIn("IS NOT DISTINCT FROM", cur.calls[0][0])
        self.assertIn("UPDATE inventory_stock", cur.calls[1][0])
        self.assertIn(Decimal("10"), cur.calls[1][1])

    def test_missing_row_inserts(self):
        cur = FakeCursor(ones=[None, {"qty_on_hand": Decimal("10")}])
        qty = store.apply_stock_delta(
            cur,
            tenant_id="t-1",
            workspace_client_id=9,
            product_id="p",
            warehouse_id=1,
            batch_id="b1",
            qty_delta=10,
        )
        self.assertEqual(qty, Decimal("10"))
        self.assertIn("INSERT INTO inventory_stock", cur.calls[1][0])
        self.assertEqual(cur.calls[1][1][0], "t-1")

    def test_sale_guard_rejects_negative_before_update(self):
        cur = FakeCursor(ones=[{"id": "s1", "qty_on_hand": Decimal("2")}])
        with self.assertRaises(store.InsufficientStockError):
            store.apply_stock_delta(
                cur,
                tenant_id="t-1",
                workspace_client_id=9,
                product_id="p",
                warehouse_id=1,
                batch_id="b1",
                qty_delta=-3,
                reject_negative=True,
            )
        self.assertEqual(len(cur.calls), 1)

    def test_sale_guard_rejects_negative_missing_row_before_insert(self):
        cur = FakeCursor(ones=[None])
        with self.assertRaises(store.InsufficientStockError):
            store.apply_stock_delta(
                cur,
                tenant_id="t-1",
                workspace_client_id=9,
                product_id="p",
                warehouse_id=1,
                batch_id="b1",
                qty_delta=-1,
                reject_negative=True,
            )
        self.assertEqual(len(cur.calls), 1)


class BatchWarehouseTests(unittest.TestCase):
    def test_get_or_create_batch_returns_existing(self):
        cur = FakeCursor(
            ones=[
                {
                    "id": "b1",
                    "batch_no": "L1",
                    "expiry_date": None,
                    "unit_cost": None,
                    "workspace_client_id": 9,
                }
            ]
        )
        out = store.get_or_create_batch(
            cur, tenant_id="t-1", workspace_client_id=9, product_id="p", batch_no="L1"
        )
        self.assertEqual(out["id"], "b1")
        self.assertEqual(len(cur.calls), 1)  # 命中且套账已填 → 不 INSERT、不自愈 UPDATE
        self.assertIn("WHERE tenant_id = %s AND product_id = %s AND batch_no = %s", cur.calls[0][0])

    def test_get_or_create_batch_inserts_when_missing(self):
        cur = FakeCursor(
            ones=[
                None,
                {"id": "b2", "batch_no": "L2", "expiry_date": None, "unit_cost": Decimal("18.00")},
            ]
        )
        out = store.get_or_create_batch(
            cur, tenant_id="t-1", workspace_client_id=9, product_id="p", batch_no="L2", unit_cost=18
        )
        self.assertEqual(out["id"], "b2")
        self.assertIn("INSERT INTO inventory_batches", cur.calls[1][0])
        self.assertIn("workspace_client_id", cur.calls[1][0])  # PO-5 · 写入套账
        self.assertIn(9, cur.calls[1][1])  # workspace_client_id 入参
        self.assertIn(Decimal("18"), cur.calls[1][1])

    def test_default_warehouse_created_when_none(self):
        cur = FakeCursor(
            ones=[None, {"id": 1, "name": "ร้าน", "is_default": True, "is_active": True}]
        )
        out = store.get_or_create_default_warehouse(cur, tenant_id="t-1", workspace_client_id=9)
        self.assertEqual(out["id"], 1)
        self.assertIn("INSERT INTO warehouses", cur.calls[1][0])


class WeightedAvgCostLooseTests(unittest.TestCase):
    """POS 报表 COGS 用:散装(无批次)成本 = 全部带成本进货流水按数量加权平均。"""

    def test_weights_by_qty_across_multiple_purchases(self):
        # 两笔进货:100 件@10、50 件@16 → 加权均价 = (1000+800)/150 = 12
        cur = FakeCursor(ones=[{"cost_sum": Decimal("1800"), "qty_sum": Decimal("150")}])
        avg = store.weighted_avg_purchase_cost_loose(
            cur, tenant_id="t-1", workspace_client_id=9, product_id="p", warehouse_id=1
        )
        self.assertEqual(avg, Decimal("12"))
        sql = cur.calls[0][0]
        self.assertIn("batch_id IS NULL", sql)
        self.assertIn("txn_type = 'purchase_in'", sql)
        self.assertIn("unit_cost IS NOT NULL", sql)

    def test_no_purchase_history_returns_none_not_zero(self):
        cur = FakeCursor(ones=[{"cost_sum": None, "qty_sum": None}])
        avg = store.weighted_avg_purchase_cost_loose(
            cur, tenant_id="t-1", workspace_client_id=9, product_id="p", warehouse_id=1
        )
        self.assertIsNone(avg)  # 诚实未知,不当 0


class TxnTests(unittest.TestCase):
    def test_insert_txn_parameterized_and_decimal(self):
        cur = FakeCursor(ones=[{"id": "tx1"}])
        store.insert_txn(
            cur,
            tenant_id="t-1",
            workspace_client_id=9,
            product_id="p",
            warehouse_id=1,
            batch_id=None,
            txn_type="purchase_in",
            qty_delta=10,
            unit_cost=18,
        )
        self.assertIn("INSERT INTO inventory_transactions", cur.last_sql)
        self.assertIn("RETURNING", cur.last_sql)
        self.assertEqual(cur.last_params[0], "t-1")
        self.assertIn("purchase_in", cur.last_params)
        self.assertIn(Decimal("10"), cur.last_params)

    def test_find_by_client_uuid_scopes_tenant(self):
        cur = FakeCursor(ones=[None])
        store.find_txn_by_client_uuid(cur, tenant_id="t-1", client_uuid="cu")
        self.assertIn("tenant_id = %s AND client_uuid = %s", cur.last_sql)
        self.assertEqual(cur.last_params, ("t-1", "cu"))


if __name__ == "__main__":
    unittest.main()

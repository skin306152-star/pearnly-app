# -*- coding: utf-8 -*-
"""库存 ledger 编排守门测试(POS 项目 · PO-A3)。

锁定:单位换算(qty×factor=base)· 幂等(client_uuid 命中→deduped 不重复扣)· resolve_factor
三态 · count 差异 · 坏输入抛 InventoryError。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.inventory import ledger


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


class ResolveFactorTests(unittest.TestCase):
    def test_base_unit_is_one_without_units_query(self):
        cur = FakeCursor(ones=[{"base_unit": "ชิ้น"}])
        f = ledger.resolve_factor(cur, tenant_id="t", product_id="p", unit_name=None)
        self.assertEqual(f, Decimal("1"))
        self.assertEqual(len(cur.calls), 1)  # 只查 products · 不查 product_units

    def test_named_unit_returns_factor(self):
        cur = FakeCursor(ones=[{"base_unit": "เม็ด"}, {"factor_to_base": Decimal("100")}])
        f = ledger.resolve_factor(cur, tenant_id="t", product_id="p", unit_name="กล่อง")
        self.assertEqual(f, Decimal("100"))

    def test_unknown_product_raises(self):
        cur = FakeCursor(ones=[None])
        with self.assertRaises(ledger.InventoryError) as ctx:
            ledger.resolve_factor(cur, tenant_id="t", product_id="p", unit_name=None)
        self.assertEqual(ctx.exception.code, "pos.product_not_found")

    def test_unknown_unit_raises_line_invalid(self):
        cur = FakeCursor(ones=[{"base_unit": "เม็ด"}, None])
        with self.assertRaises(ledger.InventoryError) as ctx:
            ledger.resolve_factor(cur, tenant_id="t", product_id="p", unit_name="ผิด")
        self.assertEqual(ctx.exception.code, "pos.line_invalid")


class ApplyMovementIdempotencyTests(unittest.TestCase):
    def test_dedup_skips_insert(self):
        cur = FakeCursor(ones=[{"id": "tx-existing"}])  # find_txn 命中
        out = ledger.apply_movement(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            warehouse_id=1,
            product_id="p",
            batch_id=None,
            txn_type="purchase_in",
            qty_delta=5,
            client_uuid="cu",
        )
        self.assertTrue(out["deduped"])
        self.assertEqual(len(cur.calls), 1)  # 只查重 · 不 INSERT/不改库存
        self.assertNotIn("INSERT", " ".join(c[0] for c in cur.calls))

    def test_no_client_uuid_inserts_and_materializes(self):
        cur = FakeCursor(ones=[{"id": "tx1"}, None, {"qty_on_hand": Decimal("5")}])
        out = ledger.apply_movement(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            warehouse_id=1,
            product_id="p",
            batch_id=None,
            txn_type="purchase_in",
            qty_delta=5,
        )
        self.assertFalse(out["deduped"])
        self.assertEqual(out["qty_on_hand"], Decimal("5"))
        joined = " ".join(c[0] for c in cur.calls)
        self.assertIn("INSERT INTO inventory_transactions", joined)
        self.assertIn("inventory_stock", joined)


class ReceiveConversionTests(unittest.TestCase):
    def test_qty_converted_to_base_unit(self):
        # 入库 2 กล่อง,factor 100 → 扣/入 200 base_unit
        cur = FakeCursor(
            ones=[
                {"base_unit": "เม็ด"},  # resolve_factor products
                {"factor_to_base": Decimal("100")},  # product_units
                {"id": "tx1"},  # insert_txn
                None,  # get_stock_for_update
                {"qty_on_hand": Decimal("200")},  # insert stock
            ]
        )
        out = ledger.receive(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            warehouse_id=1,
            lines=[{"product_id": "p", "unit_name": "กล่อง", "qty": 2}],
        )
        self.assertFalse(out["deduped"])
        self.assertEqual(out["updated_stock"][0]["qty_on_hand"], 200.0)
        # insert_txn 收到 qty_delta=200 + purchase_in
        txn_call = next(c for c in cur.calls if "INSERT INTO inventory_transactions" in c[0])
        self.assertIn(Decimal("200"), txn_call[1])
        self.assertIn("purchase_in", txn_call[1])

    def test_request_level_idempotency_short_circuits(self):
        cur = FakeCursor(ones=[{"id": "tx-existing"}])  # 起手查重命中
        out = ledger.receive(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            warehouse_id=1,
            lines=[{"product_id": "p", "qty": 1}],
            client_uuid="cu",
        )
        self.assertTrue(out["deduped"])
        self.assertEqual(out["txn_ids"], [])


class ReceiveBatchGuardTests(unittest.TestCase):
    """非批次品即便传批号也不落批次行(货入散装桶)——防"库存看得见卖不出"从源头。"""

    def _run(self, tracks):
        created, moved = [], []

        def _batch(cur, **kw):
            created.append(kw)
            return {"id": "b1"}

        def _move(cur, **kw):
            moved.append(kw.get("batch_id"))
            return {"txn": {"id": "tx1"}, "qty_on_hand": Decimal("5")}

        with (
            mock.patch.object(ledger, "resolve_factor", return_value=Decimal("1")),
            mock.patch.object(ledger.store, "product_tracks_batch", return_value=tracks),
            mock.patch.object(ledger.store, "get_or_create_batch", side_effect=_batch),
            mock.patch.object(ledger, "apply_movement", side_effect=_move),
        ):
            ledger.receive(
                object(),
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                lines=[
                    {"product_id": "p", "qty": 3, "batch_no": "L1", "expiry_date": "2027-01-01"}
                ],
            )
        return created, moved

    def test_nonbatch_product_ignores_batch_no(self):
        created, moved = self._run(tracks=False)
        self.assertEqual(created, [])  # 未建批次
        self.assertEqual(moved, [None])  # 货入散装行

    def test_batch_product_creates_batch(self):
        created, moved = self._run(tracks=True)
        self.assertEqual(len(created), 1)  # 建了批次
        self.assertEqual(moved, ["b1"])  # 货入批次行


class CountTests(unittest.TestCase):
    def test_delta_from_total_across_batches_not_single_row(self):
        # 无批次盘点:system_qty 取全批次总和(4+3=7),实盘 5 → delta -2。
        cur = FakeCursor(
            ones=[
                {"base_unit": "ชิ้น"},  # assert_product_owned
                {"id": "txc"},  # insert_txn (count)
                {"id": "sN", "qty_on_hand": Decimal("3")},  # apply_stock_delta 锁 None 行
                {"qty_on_hand": Decimal("1")},  # apply_stock_delta UPDATE RETURNING
            ],
            manys=[[{"q": Decimal("4")}, {"q": Decimal("3")}]],  # sum_on_hand_for_update
        )
        out = ledger.count(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            warehouse_id=1,
            lines=[{"product_id": "p", "batch_id": None, "counted_qty": 5}],
        )
        adj = out["adjustments"][0]
        self.assertEqual(adj["system_qty"], 7.0)
        self.assertEqual(adj["counted_qty"], 5.0)
        self.assertEqual(adj["delta"], -2.0)
        txn_call = next(c for c in cur.calls if "INSERT INTO inventory_transactions" in c[0])
        self.assertIn("count", txn_call[1])
        self.assertIn(Decimal("-2"), txn_call[1])

    def test_multibatch_count_converges_to_counted_not_double_adds(self):
        # 真机 bug 回归:库存分散 3 批(100+100+100=300 总),用户按总数盘 100。
        # 修前只读 batch=None 单行 → delta 全错;修后 system_qty=300 → delta=-200,总数收敛到 100。
        cur = FakeCursor(
            ones=[
                {"base_unit": "ชิ้น"},  # assert_product_owned
                {"id": "txc"},  # insert_txn
                {"id": "sN", "qty_on_hand": Decimal("100")},  # 锁 None 行
                {"qty_on_hand": Decimal("-100")},  # None 行落差异后(总仍收敛=100)
            ],
            manys=[[{"q": Decimal("100")}, {"q": Decimal("100")}, {"q": Decimal("100")}]],
        )
        out = ledger.count(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            warehouse_id=1,
            lines=[{"product_id": "p", "batch_id": None, "counted_qty": 100}],
        )
        adj = out["adjustments"][0]
        self.assertEqual(adj["system_qty"], 300.0)  # 总和,非单行
        self.assertEqual(adj["delta"], -200.0)
        txn_call = next(c for c in cur.calls if "INSERT INTO inventory_transactions" in c[0])
        self.assertIn(Decimal("-200"), txn_call[1])

    def test_matched_count_no_movement(self):
        # 实盘=系统总数 → delta 0 → 不写流水(治"数 600 却 +200")。
        cur = FakeCursor(
            ones=[{"base_unit": "ชิ้น"}],
            manys=[[{"q": Decimal("300")}, {"q": Decimal("300")}]],  # 总 600
        )
        out = ledger.count(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            warehouse_id=1,
            lines=[{"product_id": "p", "batch_id": None, "counted_qty": 600}],
        )
        self.assertEqual(out["adjustments"][0]["delta"], 0.0)
        self.assertFalse(any("INSERT INTO inventory_transactions" in c[0] for c in cur.calls))


if __name__ == "__main__":
    unittest.main()

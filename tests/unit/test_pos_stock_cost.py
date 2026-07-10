# -*- coding: utf-8 -*-
"""POS 卖出成本快照(POS 报表毛利 · services/pos/stock.cost_for_moves)。

锁定:多批次拆行的卖出必须按各段实际扣减的批次成本加权算 COGS(不是单批价 × 总量),
散装段退而求其次用加权平均进价;任一段成本未知 → 整行诚实置 None,不拿部分数据瞎猜。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.pos import stock


class CostForMovesTests(unittest.TestCase):
    def test_single_batch_uses_its_unit_cost(self):
        cur = object()
        with mock.patch.object(
            stock.inv_store, "get_batch", return_value={"id": "b1", "unit_cost": Decimal("10.00")}
        ):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[("b1", Decimal("3"))],
            )
        self.assertEqual(cost, Decimal("30.00"))

    def test_multi_batch_different_costs_weighted_correctly(self):
        # 同品分两批扣:2 件@฿10(旧批·先效先出先扣)+ 3 件@฿16(新批) = 20+48 = 68
        cur = object()
        costs = {"b1": Decimal("10.00"), "b2": Decimal("16.00")}

        def _get_batch(_cur, *, batch_id, **_kw):
            return {"id": batch_id, "unit_cost": costs[batch_id]}

        with mock.patch.object(stock.inv_store, "get_batch", side_effect=_get_batch):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[("b1", Decimal("2")), ("b2", Decimal("3"))],
            )
        self.assertEqual(cost, Decimal("68.00"))  # 不是单批价 x 总量(那会算成 30 或 80)

    def test_loose_segment_uses_weighted_average_cost(self):
        cur = object()
        with mock.patch.object(
            stock.inv_store, "weighted_avg_purchase_cost_loose", return_value=Decimal("12.5")
        ):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[(None, Decimal("4"))],
            )
        self.assertEqual(cost, Decimal("50.00"))

    def test_mixed_batch_and_loose_segments_summed(self):
        cur = object()
        with (
            mock.patch.object(
                stock.inv_store,
                "get_batch",
                return_value={"id": "b1", "unit_cost": Decimal("10.00")},
            ),
            mock.patch.object(
                stock.inv_store, "weighted_avg_purchase_cost_loose", return_value=Decimal("8.00")
            ),
        ):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[("b1", Decimal("2")), (None, Decimal("1"))],
            )
        self.assertEqual(cost, Decimal("28.00"))  # 20 + 8

    def test_unknown_batch_cost_makes_whole_line_none(self):
        # 老批次没记过进价(unit_cost NULL)→ 整行诚实置空,不拿另一段拼凑
        cur = object()
        with mock.patch.object(
            stock.inv_store, "get_batch", return_value={"id": "b1", "unit_cost": None}
        ):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[("b1", Decimal("2"))],
            )
        self.assertIsNone(cost)

    def test_unknown_loose_average_makes_whole_line_none(self):
        cur = object()
        with mock.patch.object(
            stock.inv_store, "weighted_avg_purchase_cost_loose", return_value=None
        ):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[(None, Decimal("5"))],
            )
        self.assertIsNone(cost)

    def test_missing_batch_row_treated_as_unknown(self):
        cur = object()
        with mock.patch.object(stock.inv_store, "get_batch", return_value=None):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[("gone", Decimal("1"))],
            )
        self.assertIsNone(cost)

    def test_zero_qty_segments_skipped(self):
        cur = object()
        with mock.patch.object(
            stock.inv_store, "get_batch", return_value={"id": "b1", "unit_cost": Decimal("10.00")}
        ):
            cost = stock.cost_for_moves(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                moves=[("b1", Decimal("2")), ("b1", Decimal("0"))],
            )
        self.assertEqual(cost, Decimal("20.00"))


class DeductForSaleReturnShapeTests(unittest.TestCase):
    """deduct_for_sale/_apply_sale_moves 现在回传 {"batch_id","moves"},moves 是成本计算的凭据。"""

    def test_explicit_batch_returns_moves_for_cost_calc(self):
        cur = object()
        with mock.patch.object(stock, "_check_and_move") as mocked:
            mocked.return_value = None
            out = stock.deduct_for_sale(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                qty_base=Decimal("3"),
                track_batch=True,
                explicit_batch_id="b1",
                sale_id="s1",
            )
        self.assertEqual(out["batch_id"], "b1")
        self.assertEqual(out["moves"], [("b1", Decimal("3"))])

    def test_fefo_multi_batch_moves_all_returned(self):
        cur = object()
        with (
            mock.patch.object(
                stock.fefo,
                "select_batches_for_outflow",
                return_value={
                    "allocations": [
                        {"batch_id": "b1", "qty": Decimal("2")},
                        {"batch_id": "b2", "qty": Decimal("3")},
                    ],
                    "shortfall": Decimal("0"),
                },
            ),
            mock.patch.object(stock.ledger, "apply_movement"),
        ):
            out = stock.deduct_for_sale(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                warehouse_id=1,
                product_id="p",
                qty_base=Decimal("5"),
                track_batch=True,
                explicit_batch_id=None,
                sale_id="s1",
            )
        self.assertEqual(out["batch_id"], "b1")  # 首批仍是行上展示锚点
        self.assertEqual(
            out["moves"], [("b1", Decimal("2")), ("b2", Decimal("3"))]
        )  # 全量分段留给成本计算


if __name__ == "__main__":
    unittest.main()

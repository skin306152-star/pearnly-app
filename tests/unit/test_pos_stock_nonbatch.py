# -*- coding: utf-8 -*-
"""非批次品出库池化守门(POS · services/pos/stock._deduct_non_batch)。

锁定"看得见卖不出"回归:非批次品被带批号进货后货落进批次行、散装行=0 时,卖出要能把
散装+批次当同一池扣(散装优先、再 FEFO),总量不足才 out_of_stock。移动机制走 mock,
本测只钉分配决策。
"""

import unittest
from decimal import Decimal
from unittest import mock

from core.pos_api import PosError
from services.pos import stock


def _sell(qty, *, loose, alloc, shortfall=Decimal("0")):
    """跑一次非批次卖出,返回 (apply_movement 调用列表 [(batch_id, qty_delta)], fefo 查询次数)。"""
    loose_row = {"qty_on_hand": Decimal(str(loose))} if loose is not None else None
    moves = []
    fefo_calls = []

    def _rec(cur, **kw):
        moves.append((kw["batch_id"], kw["qty_delta"]))

    def _fefo(cur, **kw):
        fefo_calls.append(kw)
        return {"allocations": list(alloc), "shortfall": Decimal(str(shortfall))}

    with (
        mock.patch.object(stock.inv_store, "get_stock_for_update", return_value=loose_row),
        mock.patch.object(stock.fefo, "select_batches_for_outflow", side_effect=_fefo),
        mock.patch.object(stock.ledger, "apply_movement", side_effect=_rec),
    ):
        stock.deduct_for_sale(
            object(),
            tenant_id="t",
            workspace_client_id=12,
            warehouse_id=1,
            product_id="p",
            qty_base=qty,
            track_batch=False,
            explicit_batch_id=None,
            sale_id="s1",
        )
    return moves, len(fefo_calls)


class NonBatchPoolTests(unittest.TestCase):
    def test_stranded_batch_stock_sells_via_fefo(self):
        # metta 复现:散装 0,货全在批次行 → 卖 3 全从批次扣,不报库存不足
        moves, _ = _sell(3, loose=0, alloc=[{"batch_id": "b1", "qty": Decimal("3")}])
        self.assertEqual(moves, [("b1", Decimal("-3"))])

    def test_loose_covers_skips_batch_query(self):
        # 散装够整行 → 不再查批次(短路省一次 DB 往返)
        moves, fefo_n = _sell(3, loose=10, alloc=[])
        self.assertEqual(moves, [(None, Decimal("-3"))])
        self.assertEqual(fefo_n, 0)

    def test_mixed_loose_first_then_fefo(self):
        # 散装 2 + 批次补 3 = 5
        moves, _ = _sell(5, loose=2, alloc=[{"batch_id": "b1", "qty": Decimal("3")}])
        self.assertEqual(moves, [(None, Decimal("-2")), ("b1", Decimal("-3"))])

    def test_total_short_raises_before_any_move(self):
        # 散装 1 + 批次 1,想卖 5 → shortfall>0 → out_of_stock 且不留半扣
        recorded = []
        with (
            mock.patch.object(
                stock.inv_store,
                "get_stock_for_update",
                return_value={"qty_on_hand": Decimal("1")},
            ),
            mock.patch.object(
                stock.fefo,
                "select_batches_for_outflow",
                return_value={
                    "allocations": [{"batch_id": "b1", "qty": Decimal("1")}],
                    "shortfall": Decimal("3"),
                },
            ),
            mock.patch.object(
                stock.ledger, "apply_movement", side_effect=lambda *a, **k: recorded.append(k)
            ),
        ):
            with self.assertRaises(PosError) as ctx:
                stock.deduct_for_sale(
                    object(),
                    tenant_id="t",
                    workspace_client_id=12,
                    warehouse_id=1,
                    product_id="p",
                    qty_base=5,
                    track_batch=False,
                    explicit_batch_id=None,
                    sale_id="s1",
                )
        self.assertEqual(ctx.exception.code, "pos.out_of_stock")
        self.assertEqual(recorded, [])


if __name__ == "__main__":
    unittest.main()

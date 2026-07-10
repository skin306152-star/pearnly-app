# -*- coding: utf-8 -*-
"""POS 小票编排纯逻辑守门测试(POS 项目 · PO-B2)。

不连库的纯函数:整单折扣解析、金额字符串化、成交时间解析、幂等短路(client_uuid 命中返原结果
不再发号/扣库存)。重流程(发号/扣库存/落库)由 _e2e_po_b2 真库覆盖。"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock

from services.pos import sale


class _Cur:
    def __init__(self, ones=None):
        self.calls = []
        self._ones = list(ones or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None


class HelperTests(unittest.TestCase):
    def test_header_discount_modes(self):
        self.assertEqual(sale._header_discount({"type": "pct", "value": 10}), (0, 10))
        self.assertEqual(sale._header_discount({"type": "amount", "value": 5}), (5, 0))
        self.assertEqual(sale._header_discount({"type": "none", "value": 0}), (0, 0))
        self.assertEqual(sale._header_discount(None), (0, 0))

    def test_money_two_decimals(self):
        self.assertEqual(sale._money(Decimal("55")), "55.00")
        self.assertEqual(sale._money("3.6"), "3.60")
        self.assertEqual(sale._money(None), "0.00")

    def test_parse_sold_at(self):
        dt = sale._parse_sold_at("2026-06-07T07:32:00Z")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.tzinfo, timezone.utc)
        # 坏输入回退到现在(不抛)
        self.assertIsInstance(sale._parse_sold_at("garbage"), datetime)
        self.assertIsInstance(sale._parse_sold_at(None), datetime)

    def test_vat_rate_is_seven(self):
        self.assertEqual(sale.VAT_RATE, Decimal("7"))


class IdempotencyTests(unittest.TestCase):
    def test_dedup_short_circuits_without_numbering_or_stock(self):
        existing = {
            "id": "s1",
            "receipt_no": "RCP-T1-2026-00001",
            "grand_total": Decimal("55.00"),
            "vat_amount": Decimal("3.60"),
            "paid_total": Decimal("100.00"),
            "change_amount": Decimal("45.00"),
            "status": "completed",
        }
        cur = _Cur(ones=[existing])  # find_sale_by_client_uuid 命中
        out = sale.create_sale(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            payload={
                "client_uuid": "cu-1",
                "lines": [{"product_id": "p", "qty": 1, "unit_price": 1}],
            },
        )
        self.assertTrue(out["deduped"])
        self.assertEqual(out["sale"]["receipt_no"], "RCP-T1-2026-00001")
        # 只查重一条 SQL · 没发号/没扣库存/没 INSERT
        self.assertEqual(len(cur.calls), 1)
        joined = " ".join(c[0] for c in cur.calls)
        self.assertNotIn("INSERT", joined)


class CreateSaleCostWiringTests(unittest.TestCase):
    """create_sale 建单行时必须把 stock.cost_for_moves 算出的成本快照落进 cost_total,
    且必须喂 deduct_for_sale 回传的完整 moves(不是只喂首批 batch_id)——报表毛利的地基。"""

    def _run(self, *, cost_return):
        cur = _Cur()
        product = {
            "id": "prod1",
            "base_unit": "ea",
            "track_batch": True,
            "vat_applicable": True,
            "name_th": "โค้ก",
            "name_en": "Coke",
            "name_zh": "可乐",
        }
        deducted = {"batch_id": "b1", "moves": [("b1", Decimal("1")), ("b2", Decimal("1"))]}
        insert_line_calls = []
        with (
            mock.patch.object(sale, "_assert_shift_open"),
            mock.patch.object(
                sale.inv_store, "get_or_create_default_warehouse", return_value={"id": 1}
            ),
            mock.patch.object(sale.sales_store, "get_product_for_sale", return_value=product),
            mock.patch.object(sale.numbering, "next_number", return_value=("RCP-T1-2026-00001", 1)),
            mock.patch.object(sale.stock, "deduct_for_sale", return_value=deducted) as ded_mock,
            mock.patch.object(sale.stock, "cost_for_moves", return_value=cost_return) as cost_mock,
            mock.patch.object(
                sale.sales_store,
                "insert_sale",
                return_value={
                    "id": "sale1",
                    "receipt_no": "RCP-T1-2026-00001",
                    "grand_total": Decimal("20.00"),
                    "vat_amount": Decimal("1.31"),
                    "paid_total": Decimal("20.00"),
                    "change_amount": Decimal("0.00"),
                    "status": "completed",
                },
            ),
            mock.patch.object(
                sale.sales_store,
                "insert_line",
                side_effect=lambda *a, **kw: insert_line_calls.append(kw) or {"id": "line1"},
            ),
            mock.patch.object(sale.sales_store, "insert_payment"),
            mock.patch.object(sale.acct_hooks, "enqueue_posting"),
        ):
            sale.create_sale(
                cur,
                tenant_id="t1",
                workspace_client_id=9,
                payload={
                    "shift_id": "shift1",
                    "lines": [{"product_id": "prod1", "qty": 2, "unit_price": 10}],
                    "payments": [{"method": "cash", "amount": 20}],
                },
            )
        return ded_mock, cost_mock, insert_line_calls

    def test_cost_for_moves_fed_the_full_moves_from_deduct(self):
        ded_mock, cost_mock, _calls = self._run(cost_return=Decimal("18.00"))
        self.assertEqual(ded_mock.call_count, 1)
        cost_kwargs = cost_mock.call_args.kwargs
        self.assertEqual(cost_kwargs["moves"], [("b1", Decimal("1")), ("b2", Decimal("1"))])
        self.assertEqual(cost_kwargs["product_id"], "prod1")

    def test_line_persists_known_cost_snapshot(self):
        _ded, _cost, calls = self._run(cost_return=Decimal("18.00"))
        self.assertEqual(len(calls), 1)
        fields = calls[0]["fields"]
        self.assertEqual(fields["cost_total"], Decimal("18.00"))
        self.assertEqual(fields["batch_id"], "b1")  # 展示锚点仍是首批

    def test_line_persists_none_when_cost_unknown(self):
        # 老批次没记进价 → cost_for_moves 诚实返 None,行上必须落 NULL,不许瞎猜 0
        _ded, _cost, calls = self._run(cost_return=None)
        fields = calls[0]["fields"]
        self.assertIsNone(fields["cost_total"])


if __name__ == "__main__":
    unittest.main()

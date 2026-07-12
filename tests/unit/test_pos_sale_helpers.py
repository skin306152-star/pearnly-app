# -*- coding: utf-8 -*-
"""POS 小票编排纯逻辑守门测试(POS 项目 · PO-B2)。

不连库的纯函数:整单折扣解析、金额字符串化、成交时间解析、幂等短路(client_uuid 命中返原结果
不再发号/扣库存)。重流程(发号/扣库存/落库)由 _e2e_po_b2 真库覆盖。"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock

from core.pos_api import PosError
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


class PaymentSettlementTests(unittest.TestCase):
    def test_exact_cash_payment(self):
        paid, change = sale._settle_payments(
            [{"method": "cash", "amount": "107.30"}], Decimal("107.30")
        )
        self.assertEqual(paid, Decimal("107.30"))
        self.assertEqual(change, Decimal("0"))

    def test_cash_may_create_change(self):
        paid, change = sale._settle_payments(
            [{"method": "cash", "amount": "200.00"}], Decimal("107.30")
        )
        self.assertEqual(paid, Decimal("200.00"))
        self.assertEqual(change, Decimal("92.70"))

    def test_mixed_payment_change_must_be_covered_by_cash(self):
        paid, change = sale._settle_payments(
            [
                {"method": "card", "amount": "80.00"},
                {"method": "cash", "amount": "30.00"},
            ],
            Decimal("100.00"),
        )
        self.assertEqual(paid, Decimal("110.00"))
        self.assertEqual(change, Decimal("10.00"))

    def test_every_payment_must_be_positive(self):
        for amount in ("0", "-0.01", "NaN", "Infinity", "bad", None):
            with self.subTest(amount=amount), self.assertRaises(PosError) as ctx:
                sale._settle_payments([{"method": "cash", "amount": amount}], Decimal("10"))
            self.assertEqual(ctx.exception.code, "pos.payment_invalid")
            self.assertEqual(ctx.exception.detail, "amount")

    def test_payment_shape_method_and_scale_are_validated(self):
        cases = (
            (["not-an-object"], "payment"),
            ([{"method": "crypto", "amount": "10.00"}], "method"),
            ([{"method": "cash", "amount": "10.001"}], "amount"),
        )
        for payments, detail in cases:
            with self.subTest(payments=payments), self.assertRaises(PosError) as ctx:
                sale._settle_payments(payments, Decimal("10.00"))
            self.assertEqual(ctx.exception.code, "pos.payment_invalid")
            self.assertEqual(ctx.exception.detail, detail)

    def test_supported_noncash_methods_settle_exact_amount(self):
        for method in ("qr", "promptpay", "card", "transfer"):
            with self.subTest(method=method):
                self.assertEqual(
                    sale._settle_payments(
                        [{"method": method, "amount": "10.00"}], Decimal("10.00")
                    ),
                    (Decimal("10.00"), Decimal("0.00")),
                )

    def test_qr_is_persisted_as_promptpay_without_mutating_input(self):
        source = [{"method": "qr", "amount": "10.00", "ref": "qr-1"}]
        normalized, paid, change = sale._validated_payments(source, Decimal("10.00"))
        self.assertEqual(source[0]["method"], "qr")
        self.assertEqual(
            normalized,
            [{"method": "promptpay", "amount": Decimal("10.00"), "ref": "qr-1"}],
        )
        self.assertEqual(paid - change, Decimal("10.00"))

    def test_grand_total_contract(self):
        for grand in (Decimal("NaN"), Decimal("Infinity"), Decimal("-0.01")):
            with self.subTest(grand=grand), self.assertRaises(PosError) as ctx:
                sale._settle_payments([], grand)
            self.assertEqual(ctx.exception.detail, "grand_total")
        self.assertEqual(sale._settle_payments([], Decimal("0")), (Decimal("0"), Decimal("0")))
        with self.assertRaises(PosError) as ctx:
            sale._settle_payments([{"method": "cash", "amount": "1.00"}], Decimal("0"))
        self.assertEqual(ctx.exception.detail, "zero_total")

    def test_underpayment_is_rejected(self):
        with self.assertRaises(PosError) as ctx:
            sale._settle_payments([{"method": "cash", "amount": "99.99"}], Decimal("100.00"))
        self.assertEqual(ctx.exception.code, "pos.payment_invalid")
        self.assertEqual(ctx.exception.detail, "underpaid")

    def test_noncash_cannot_create_change(self):
        cases = (
            [{"method": "card", "amount": "100.01"}],
            [
                {"method": "card", "amount": "100.01"},
                {"method": "cash", "amount": "1.00"},
            ],
        )
        for payments in cases:
            with self.subTest(payments=payments), self.assertRaises(PosError) as ctx:
                sale._settle_payments(payments, Decimal("100.00"))
            self.assertEqual(ctx.exception.code, "pos.payment_invalid")
            self.assertEqual(ctx.exception.detail, "noncash_overpay")

    def test_decimal_sum_does_not_use_binary_float(self):
        paid, change = sale._settle_payments(
            [
                {"method": "card", "amount": "0.10"},
                {"method": "cash", "amount": "0.20"},
            ],
            Decimal("0.30"),
        )
        self.assertEqual(paid, Decimal("0.30"))
        self.assertEqual(change, Decimal("0"))


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
                    "payments": [{"method": "cash", "amount": 100}],
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


class CreateSalePaymentGateTests(unittest.TestCase):
    def test_invalid_settlement_is_rejected_before_receipt_numbering(self):
        totals = {
            "subtotal": Decimal("100.00"),
            "discount_total": Decimal("0"),
            "header_discount_amount": Decimal("0"),
            "vat_amount": Decimal("0"),
            "grand_total": Decimal("100.00"),
            "lines": [],
        }
        with (
            mock.patch.object(sale, "_assert_shift_open"),
            mock.patch.object(
                sale.inv_store, "get_or_create_default_warehouse", return_value={"id": 1}
            ),
            mock.patch.object(sale, "compute_totals", return_value=totals),
            mock.patch.object(sale.numbering, "next_number") as next_number,
            self.assertRaises(PosError) as ctx,
        ):
            sale.create_sale(
                _Cur(),
                tenant_id="t1",
                workspace_client_id=9,
                payload={
                    "shift_id": "shift1",
                    "lines": [],
                    "payments": [{"method": "card", "amount": "99.99"}],
                },
            )
        self.assertEqual(ctx.exception.code, "pos.payment_invalid")
        self.assertEqual(ctx.exception.detail, "underpaid")
        next_number.assert_not_called()


if __name__ == "__main__":
    unittest.main()

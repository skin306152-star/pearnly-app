# -*- coding: utf-8 -*-
"""POS 退货多笔拆退 + 成本快照 + 毛利回冲(PC-4b-1)。

锁三件钱路事实:① 混合支付原路拆退逐笔记负额、Σ 不平 422;② 退货负单行按比例快照负成本
(老单无成本 → None 不造 0);③ 单笔 refund_method 兼容路逐字节不退化。不连库:sales_store/
stock/numbering/compute_totals 全 mock,只验编排把对的值喂给 DAL。"""

import os
import unittest
from decimal import Decimal
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from core.pos_api import PosError
from services.pos import refund as refund_svc


def _orig_line(cost_total=Decimal("60")):
    return {
        "id": "ol1",
        "product_id": "p1",
        "sell_unit": "ชิ้น",
        "unit_factor": Decimal("1"),
        "qty": Decimal("1"),
        "qty_base": Decimal("1"),
        "unit_price": Decimal("100"),
        "line_discount": Decimal("0"),
        "vat_applicable": True,
        "batch_id": None,
        "cost_total": cost_total,
    }


def _orig_sale():
    return {
        "id": "s1",
        "status": "completed",
        "sale_type": "sale",
        "price_includes_vat": False,
        "doc_kind": "receipt",
        "shift_id": None,
        "terminal_id": None,
        "member_client_id": None,
    }


class _RefundHarness:
    """把 refund() 的库/算价协作者全部 mock 掉,收集 insert_line / insert_payment 调用供断言。"""

    def __init__(self, *, orig_line_cost=Decimal("60")):
        self.line_calls = []
        self.payment_calls = []
        self._orig_line = _orig_line(orig_line_cost)

    def run(self, *, lines, refund_payments=None, refund_method="cash"):
        totals = {
            "grand_total": Decimal("100"),
            "subtotal": Decimal("100"),
            "discount_total": Decimal("0"),
            "header_discount_amount": Decimal("0"),
            "vat_amount": Decimal("0"),
            "lines": [{"discount": Decimal("0"), "line_total": Decimal("100")}],
        }
        ss = mock.Mock()
        ss.find_sale_by_client_uuid.return_value = None
        ss.get_sale.return_value = _orig_sale()
        ss.list_lines.return_value = [self._orig_line]
        ss.refunded_qty_for_line.return_value = Decimal("0")
        ss.insert_sale.return_value = {
            "id": "r1",
            "receipt_no": "RFD-1",
            "grand_total": Decimal("-100"),
        }
        ss.insert_line.side_effect = lambda *a, **k: self.line_calls.append(k) or {
            "id": "rl1",
            "batch_id": None,
            "qty_base": Decimal("1"),
        }
        ss.insert_payment.side_effect = lambda *a, **k: self.payment_calls.append(k)

        stock = mock.Mock()
        stock.sale_deducted_stock.return_value = True

        inv = mock.Mock()
        inv.get_or_create_default_warehouse.return_value = {"id": 1}

        numbering = mock.Mock()
        numbering.next_number.return_value = ("RFD-1", 1)

        with (
            mock.patch.object(refund_svc, "sales_store", ss),
            mock.patch.object(refund_svc, "stock", stock),
            mock.patch.object(refund_svc, "inv_store", inv),
            mock.patch.object(refund_svc, "numbering", numbering),
            mock.patch.object(refund_svc, "compute_totals", return_value=totals),
        ):
            return refund_svc.refund(
                object(),
                tenant_id="t",
                workspace_client_id=9,
                original_sale_id="s1",
                lines=lines,
                refund_method=refund_method,
                refund_payments=refund_payments,
            )


class MultiPaymentTests(unittest.TestCase):
    def test_split_refund_records_negative_per_method(self):
        """混合原单原路退:现金 60 + 刷卡 40 → pos_payments 两行负额,方式各归各。"""
        h = _RefundHarness()
        h.run(
            lines=[{"sale_line_id": "ol1", "qty": 1}],
            refund_payments=[
                {"method": "cash", "amount": 60},
                {"method": "card", "amount": 40},
            ],
        )
        self.assertEqual(len(h.payment_calls), 2)
        by_method = {c["method"]: c["amount"] for c in h.payment_calls}
        self.assertEqual(by_method["cash"], Decimal("-60"))
        self.assertEqual(by_method["card"], Decimal("-40"))
        self.assertEqual(sum(c["amount"] for c in h.payment_calls), Decimal("-100"))

    def test_split_sum_mismatch_raises_422(self):
        """各方式加不平退货总额 → 422,绝不落一张对不上的退货单。"""
        h = _RefundHarness()
        with self.assertRaises(PosError) as ctx:
            h.run(
                lines=[{"sale_line_id": "ol1", "qty": 1}],
                refund_payments=[
                    {"method": "cash", "amount": 60},
                    {"method": "card", "amount": 30},  # 只 90 ≠ 100
                ],
            )
        self.assertEqual(ctx.exception.code, "pos.refund_amount_mismatch")
        self.assertEqual(ctx.exception.http_status, 422)

    def test_single_method_compat_unchanged(self):
        """不带 refund_payments → 单笔原路:整额一行负额,方式=refund_method(老前台逐字节不变)。"""
        h = _RefundHarness()
        h.run(lines=[{"sale_line_id": "ol1", "qty": 1}], refund_method="qr")
        self.assertEqual(len(h.payment_calls), 1)
        self.assertEqual(h.payment_calls[0]["method"], "qr")
        self.assertEqual(h.payment_calls[0]["amount"], Decimal("-100"))


class CostSnapshotTests(unittest.TestCase):
    def test_full_refund_line_cost_negated(self):
        """全退 1/1:退货行 cost_total = 原行 60 取负。"""
        h = _RefundHarness(orig_line_cost=Decimal("60"))
        h.run(lines=[{"sale_line_id": "ol1", "qty": 1}])
        self.assertEqual(h.line_calls[0]["fields"]["cost_total"], Decimal("-60.00"))

    def test_partial_refund_cost_prorated(self):
        """半退:成本按 rqty/oqty 比例取负(退 0.5/1 → −30.00)。"""
        # oqty=1,退 0.5 → 60 * 0.5 = 30 取负
        totals = {
            "grand_total": Decimal("50"),
            "subtotal": Decimal("50"),
            "discount_total": Decimal("0"),
            "header_discount_amount": Decimal("0"),
            "vat_amount": Decimal("0"),
            "lines": [{"discount": Decimal("0"), "line_total": Decimal("50")}],
        }
        calls = []
        ss = mock.Mock()
        ss.find_sale_by_client_uuid.return_value = None
        ss.get_sale.return_value = _orig_sale()
        ss.list_lines.return_value = [_orig_line(Decimal("60"))]
        ss.refunded_qty_for_line.return_value = Decimal("0")
        ss.insert_sale.return_value = {
            "id": "r1",
            "receipt_no": "RFD-1",
            "grand_total": Decimal("-50"),
        }
        ss.insert_line.side_effect = lambda *a, **k: calls.append(k) or {
            "id": "rl1",
            "batch_id": None,
            "qty_base": Decimal("0.5"),
        }
        ss.insert_payment.side_effect = lambda *a, **k: None
        stock = mock.Mock()
        stock.sale_deducted_stock.return_value = True
        inv = mock.Mock()
        inv.get_or_create_default_warehouse.return_value = {"id": 1}
        numbering = mock.Mock()
        numbering.next_number.return_value = ("RFD-1", 1)
        with (
            mock.patch.object(refund_svc, "sales_store", ss),
            mock.patch.object(refund_svc, "stock", stock),
            mock.patch.object(refund_svc, "inv_store", inv),
            mock.patch.object(refund_svc, "numbering", numbering),
            mock.patch.object(refund_svc, "compute_totals", return_value=totals),
        ):
            refund_svc.refund(
                object(),
                tenant_id="t",
                workspace_client_id=9,
                original_sale_id="s1",
                lines=[{"sale_line_id": "ol1", "qty": 0.5}],
            )
        self.assertEqual(calls[0]["fields"]["cost_total"], Decimal("-30.00"))

    def test_old_sale_no_cost_stays_none(self):
        """老单无成本(原行 cost_total None)→ 退货行 cost_total None,诚实不造 0。"""
        h = _RefundHarness(orig_line_cost=None)
        h.run(lines=[{"sale_line_id": "ol1", "qty": 1}])
        self.assertIsNone(h.line_calls[0]["fields"]["cost_total"])


class HelperTests(unittest.TestCase):
    def test_validate_none_is_noop(self):
        refund_svc._validate_refund_payments(None, Decimal("100"))  # 不抛

    def test_validate_tolerates_sign(self):
        """调用方传正额或负额都按绝对值对账(存库统一取负在 insert 处)。"""
        refund_svc._validate_refund_payments(
            [{"method": "cash", "amount": -60}, {"method": "card", "amount": 40}],
            Decimal("100"),
        )

    def test_validate_mismatch_raises(self):
        with self.assertRaises(PosError):
            refund_svc._validate_refund_payments([{"method": "cash", "amount": 60}], Decimal("100"))

    def test_refund_line_cost_none_passthrough(self):
        self.assertIsNone(
            refund_svc._refund_line_cost({"cost_total": None, "qty": 1}, Decimal("1"))
        )

    def test_refund_line_cost_prorated_negative(self):
        cost = refund_svc._refund_line_cost(
            {"cost_total": Decimal("60"), "qty": Decimal("3")}, Decimal("1")
        )
        self.assertEqual(cost, Decimal("-20.00"))  # 60 * 1/3 取负


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""退款/作废回补库存要照扣减为镜像(POS · 勘察#6·「幻影库存」)。

零售建单每行必扣库存、餐饮埋单成品不扣(checkout.py),但通用退款/作废端点对任意
pos_sales 行都无脑 restock——对餐饮单退款/作废会把从没扣过的库存凭空补回去。
本测锁定:回补前必查 inventory_transactions 有无该单的 pos_sale 扣减痕迹,没有则
跳过全部 stock.restock(钱路照常走),状态诚实反映在 stock_returned。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.pos import refund, sale, stock, void


def _fake_cursor():
    return mock.Mock()


class SaleDeductedStockSqlShapeTests(unittest.TestCase):
    """sale_deducted_stock 的 SQL 形状:按 tenant_id + ref_type='pos_sale' + ref_id 判据。"""

    def test_queries_inventory_transactions_by_tenant_and_ref(self):
        cur = _fake_cursor()
        cur.fetchone.return_value = {"?column?": 1}
        found = stock.sale_deducted_stock(cur, tenant_id="t1", sale_id="s1")
        self.assertTrue(found)
        sql, params = cur.execute.call_args[0]
        self.assertIn("inventory_transactions", sql)
        self.assertIn("ref_type = 'pos_sale'", sql)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("ref_id = %s", sql)
        self.assertEqual(params, ("t1", "s1"))

    def test_no_row_means_not_deducted(self):
        cur = _fake_cursor()
        cur.fetchone.return_value = None
        self.assertFalse(stock.sale_deducted_stock(cur, tenant_id="t1", sale_id="s1"))


class RefundRestockGateTests(unittest.TestCase):
    """refund():无扣减痕迹(餐饮单)跳过 restock,退款单/收款照常落。"""

    def _run_refund(self, *, deducted: bool):
        cur = _fake_cursor()
        orig = {
            "id": "orig1",
            "status": "completed",
            "sale_type": "sale",
            "price_includes_vat": False,
            "terminal_id": 1,
            "shift_id": "shift1",
            "member_client_id": None,
            "doc_kind": "receipt",
        }
        oline = {
            "id": "line1",
            "product_id": "prod1",
            "sell_unit": "ea",
            "unit_factor": Decimal("1"),
            "qty": Decimal("2"),
            "qty_base": Decimal("2"),
            "unit_price": Decimal("10.00"),
            "line_discount": Decimal("0.00"),
            "vat_applicable": True,
            "batch_id": None,
        }
        restock_calls = []
        with (
            mock.patch.object(refund.sales_store, "find_sale_by_client_uuid"),
            mock.patch.object(refund.sales_store, "get_sale", return_value=orig),
            mock.patch.object(refund.sales_store, "list_lines", return_value=[oline]),
            mock.patch.object(
                refund.sales_store, "refunded_qty_for_line", return_value=Decimal("0")
            ),
            mock.patch.object(
                refund.numbering, "next_number", return_value=("RFD-T1-2026-00001", 1)
            ),
            mock.patch.object(
                refund.sales_store,
                "insert_sale",
                return_value={
                    "id": "refund1",
                    "receipt_no": "RFD-T1-2026-00001",
                    "grand_total": Decimal("-10.70"),
                },
            ),
            mock.patch.object(
                refund.inv_store, "get_or_create_default_warehouse", return_value={"id": 1}
            ),
            mock.patch.object(refund.sales_store, "insert_line"),
            mock.patch.object(refund.stock, "sale_deducted_stock", return_value=deducted),
            mock.patch.object(
                refund.stock, "restock", side_effect=lambda *a, **k: restock_calls.append(k)
            ),
            mock.patch.object(refund.sales_store, "insert_payment"),
            mock.patch.object(
                refund,
                "_current_refund_binding",
                return_value={"shift_id": "shift1", "terminal_id": 1, "cashier_id": "c1"},
            ),
        ):
            result = refund.refund(
                cur,
                tenant_id="t1",
                workspace_client_id=1,
                original_sale_id="orig1",
                lines=[{"sale_line_id": "line1", "qty": Decimal("1")}],
                cashier_id="c1",
            )
        return result, restock_calls

    def test_no_deduction_trail_skips_restock(self):
        result, restock_calls = self._run_refund(deducted=False)
        self.assertEqual(restock_calls, [])
        self.assertFalse(result["stock_returned"])
        self.assertEqual(result["refund_sale"]["id"], "refund1")  # 退款单照常落

    def test_deduction_trail_present_restocks(self):
        result, restock_calls = self._run_refund(deducted=True)
        self.assertEqual(len(restock_calls), 1)
        self.assertTrue(result["stock_returned"])


class VoidSaleRestockGateTests(unittest.TestCase):
    """void_sale():无扣减痕迹跳过 restock,stock_returned 如实反映。"""

    def _run_void(self, *, deducted: bool):
        cur = _fake_cursor()
        original = {
            "id": "s1",
            "status": "completed",
            "sale_type": "sale",
            "shift_id": None,
        }
        line = {"product_id": "prod1", "batch_id": None, "qty_base": Decimal("2")}
        restock_calls = []
        with (
            mock.patch.object(void.sales_store, "get_sale", return_value=original),
            mock.patch.object(void.sales_store, "has_refunds", return_value=False),
            mock.patch.object(
                void.inv_store, "get_or_create_default_warehouse", return_value={"id": 1}
            ),
            mock.patch.object(void.stock, "sale_deducted_stock", return_value=deducted),
            mock.patch.object(void.sales_store, "list_lines", return_value=[line]),
            mock.patch.object(
                void.stock, "restock", side_effect=lambda *a, **k: restock_calls.append(k)
            ),
            mock.patch.object(void.sales_store, "set_status", return_value=True),
        ):
            result = sale.void_sale(cur, tenant_id="t1", workspace_client_id=1, sale_id="s1")
        return result, restock_calls

    def test_no_deduction_trail_skips_restock_and_reports_false(self):
        result, restock_calls = self._run_void(deducted=False)
        self.assertEqual(restock_calls, [])
        self.assertEqual(result["status"], "void")  # 作废照常生效
        self.assertFalse(result["stock_returned"])

    def test_deduction_trail_present_restocks_and_reports_true(self):
        result, restock_calls = self._run_void(deducted=True)
        self.assertEqual(len(restock_calls), 1)
        self.assertTrue(result["stock_returned"])


if __name__ == "__main__":
    unittest.main()

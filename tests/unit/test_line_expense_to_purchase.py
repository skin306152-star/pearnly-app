# -*- coding: utf-8 -*-
"""LINE 确认入账 → 采购进项建单 data 组装(图/文同下游 · 单行=总额)。"""

import unittest
from decimal import Decimal

from services.line_binding.line_expense import _to_purchase_data


class ToPurchaseDataTests(unittest.TestCase):
    def test_expense_doc_single_line_total(self):
        data = _to_purchase_data(
            {
                "amount": Decimal("60"),
                "vendor_name": "บริษัท กาแฟพันธุ์ไทย จำกัด",
                "vendor_tax_id": "",
                "category_id": "p1",
                "subcategory_id": "c1",
                "category": "ค่าอาหารและรับรอง",
                "subcategory": "ค่าอาหาร/เครื่องดื่ม",
                "note": "กาแฟ ประชุม",
                "doc_date": "2026-06-11",
                "expense_type": "goods",
                "currency": "THB",
                "invoice_number": "NZ01000017838",
            }
        )
        self.assertEqual(data["doc_kind"], "expense")
        self.assertEqual(data["source"], "line")
        self.assertEqual(len(data["lines"]), 1)
        self.assertEqual(data["lines"][0]["unit_price"], "60")
        self.assertEqual(data["lines"][0]["category_id"], "p1")
        self.assertEqual(data["supplier"]["name"], "บริษัท กาแฟพันธุ์ไทย จำกัด")
        self.assertIsNone(data["supplier"]["tax_id"])  # 空税号 → None
        self.assertEqual(data["doc_no"], "NZ01000017838")

    def test_service_type_maps_line_item_type(self):
        data = _to_purchase_data({"amount": Decimal("500"), "expense_type": "service"})
        self.assertEqual(data["lines"][0]["item_type"], "service")

    def test_goods_default(self):
        data = _to_purchase_data({"amount": Decimal("30")})
        self.assertEqual(data["lines"][0]["item_type"], "goods")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""智能分流纯逻辑单测(P0a 方向判定 + 草稿构建 + 费用归类 · docs/purchasing/02 §0)。

判方向是进项模块灵魂:买方=本主体→进项,卖方=本主体→销项,非发票→inbox。税号比对要扛
空格/连字符差异。草稿从 OCR items 取行、无 items 单行兜底。费用文本取末位金额 + 关键词归类。
"""

import unittest
from decimal import Decimal

from services.purchase import intake as ik

MY = "1234567890123"


class JudgeDirectionTests(unittest.TestCase):
    def test_buyer_is_me_with_vat_to_purchase(self):
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "seller_tax": "9999999999999",
            "vat": "70",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("purchase_invoice", "purchase"))

    def test_seller_is_me_to_sales(self):
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": "9999999999999",
            "seller_tax": MY,
            "vat": "70",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("sales", "sales"))

    def test_not_invoice_to_inbox(self):
        f = {"is_not_invoice": True, "document_type": "other"}
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("unknown", "inbox"))

    def test_neither_matches_with_vat_defaults_purchase(self):
        # 商户拍收到的票,双方税号都没对上本主体 → 默认进项。
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": "",
            "seller_tax": "8888888888888",
            "vat": "70",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("purchase_invoice", "purchase"))

    def test_receipt_no_vat_to_expense(self):
        f = {"document_type": "receipt", "buyer_tax": "", "seller_tax": "", "vat": "0"}
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("expense", "expense"))

    def test_tax_match_ignores_spacing(self):
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": "1-2345 67890123",
            "seller_tax": "x",
            "vat": "7",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY)[1], "purchase")


class BuildDraftTests(unittest.TestCase):
    def test_items_become_lines(self):
        f = {
            "document_type": "tax_invoice",
            "seller_name": "ACME",
            "seller_tax": MY,
            "vat": "70",
            "invoice_number": "INV-1",
            "items": [{"name": "ของ", "qty": "2", "price": "50"}],
        }
        d = ik.build_draft_from_invoice(f, kind="purchase_invoice")
        self.assertEqual(d["supplier"]["name"], "ACME")
        self.assertEqual(d["doc_no"], "INV-1")
        self.assertEqual(len(d["lines"]), 1)
        self.assertEqual(d["lines"][0]["vat_rate"], 7)

    def test_no_items_fallback_single_line(self):
        f = {
            "document_type": "tax_invoice",
            "seller_name": "X",
            "vat": "7",
            "subtotal": "1000",
            "items": [],
        }
        d = ik.build_draft_from_invoice(f, kind="purchase_invoice")
        self.assertEqual(len(d["lines"]), 1)
        self.assertEqual(d["lines"][0]["unit_price"], "1000")


class ClassifyExpenseTests(unittest.TestCase):
    TREE = [
        {"id": "p1", "name": "ค่าเดินทาง", "children": [{"id": "c1", "name": "ค่าแท็กซี่"}]},
        {"id": "p2", "name": "ค่าเช่า", "children": []},
    ]

    def test_amount_is_last_number(self):
        r = ik.classify_expense_text("แท็กซี่ 50", self.TREE)
        self.assertEqual(r["amount"], Decimal("50"))

    def test_keyword_maps_to_subcategory(self):
        r = ik.classify_expense_text("นั่งแท็กซี่ไปประชุม 120", self.TREE)
        self.assertEqual((r["category_id"], r["subcategory_id"]), ("p1", "c1"))

    def test_parent_name_match(self):
        r = ik.classify_expense_text("ค่าเช่า ออฟฟิศ 8000", self.TREE)
        self.assertEqual((r["category_id"], r["subcategory_id"]), ("p2", None))

    def test_no_match_leaves_blank(self):
        r = ik.classify_expense_text("อะไรก็ไม่รู้ 30", self.TREE)
        self.assertEqual((r["category_id"], r["subcategory_id"]), (None, None))
        self.assertEqual(r["amount"], Decimal("30"))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""智能分流纯逻辑单测(方向判定 + 草稿构建 + 费用归类 · docs/purchasing/02 §0)。

待归类已下线:识别完一律建草稿落采购列表。判方向只分 进项(有 VAT)/费用(无 VAT·含截图
证据)。草稿从 OCR items 取行、无 items 单行兜底。费用文本取末位金额 + 关键词归类。
"""

import unittest
from decimal import Decimal

from services.purchase import intake as ik

MY = "1234567890123"


class JudgeDirectionTests(unittest.TestCase):
    def test_has_vat_to_purchase(self):
        f = {"document_type": "tax_invoice", "vat": "70", "buyer_tax": MY}
        self.assertEqual(ik.judge_direction(f), ("purchase_invoice", "purchase"))

    def test_tax_invoice_without_buyer_identity_stays_expense(self):
        # POS 小票可能被 OCR 标成 tax_invoice;无买方身份不能自动抵进项 VAT。
        f = {"document_type": "tax_invoice", "vat": "4.58", "buyer_name": "No.Customer:1"}
        self.assertEqual(ik.judge_direction(f), ("expense", "expense"))

    def test_no_vat_to_expense(self):
        f = {"document_type": "receipt", "vat": "0"}
        self.assertEqual(ik.judge_direction(f), ("expense", "expense"))

    def test_receipt_with_vat_stays_expense(self):
        # 普通 receipt 即便印了 VAT,也不能自动当可抵进项税票。
        f = {"document_type": "receipt", "vat": "178.08"}
        self.assertEqual(ik.judge_direction(f), ("expense", "expense"))

    def test_simplified_tax_invoice_with_vat_stays_expense(self):
        # 简式税票/小票不能抵进项 VAT,先按费用入草稿。
        f = {"document_type": "simplified_tax_invoice", "vat": "7"}
        self.assertEqual(ik.judge_direction(f), ("expense", "expense"))

    def test_payment_evidence_to_expense_no_vat(self):
        # 银行转账截图非正规税票 → 一律费用、不抵 VAT(即便 OCR 读到 vat)。
        f = {"document_type": "payment_evidence", "vat": "70"}
        self.assertEqual(ik.judge_direction(f), ("expense", "expense"))

    def test_order_evidence_to_expense(self):
        f = {"document_type": "order_evidence", "vat": "0"}
        self.assertEqual(ik.judge_direction(f), ("expense", "expense"))

    def test_no_doctype_with_vat_stays_expense(self):
        # 票种未知时不把 VAT 当成可抵进项依据。
        f = {"vat": "7"}
        self.assertEqual(ik.judge_direction(f), ("expense", "expense"))


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

    def test_expense_kind_forces_no_vat(self):
        # 费用类(含截图证据)即便 OCR 读到 vat 也不带可抵进项 VAT(进项票才抵)。
        f = {"vat": "70", "items": [{"name": "x", "qty": "1", "price": "100"}]}
        d = ik.build_draft_from_invoice(f, kind="expense")
        self.assertFalse(d["has_vat"])
        self.assertEqual(d["lines"][0]["vat_rate"], 0)

    def test_expense_receipt_uses_final_total_not_pre_vat_subtotal(self):
        # 普通 receipt/simplified tax invoice 不能抵 VAT,但 VAT 仍是费用成本。
        # 不能用税前 subtotal 2544 少记这张餐饮票,草稿金额应是最终实付 2722。
        f = {
            "document_type": "receipt",
            "seller_name": "ร้านอาหาร",
            "subtotal": "2544",
            "vat": "178.08",
            "total_amount": "2722",
            "items": [{"name": "อาหาร", "qty": "1", "price": "2544", "subtotal": "2544"}],
        }
        d = ik.build_draft_from_invoice(f, kind="expense")
        self.assertFalse(d["has_vat"])
        self.assertEqual(d["lines"], [d["lines"][0]])
        self.assertEqual(d["lines"][0]["unit_price"], "2722.00")

    def test_summary_rows_are_not_items(self):
        f = {
            "total_amount": "165",
            "items": [
                {"name": "ไก่ทอดเบตง", "qty": "1", "price": "165", "subtotal": "165"},
                {"name": "จำนวน 8", "qty": "1", "price": "131", "subtotal": "131"},
            ],
        }
        d = ik.build_draft_from_invoice(f, kind="expense")
        self.assertEqual(len(d["lines"]), 1)
        self.assertEqual(d["lines"][0]["description"], "ไก่ทอดเบตง")

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

    def test_subtotal_trusted_when_qty_price_conflict(self):
        # 加油票:qty=22(积分)× price=39.85 = 876.70 ≠ subtotal 1780 → 信 subtotal,行额=1780。
        f = {"items": [{"name": "ไฮดีเซล", "qty": "22", "price": "39.85", "subtotal": "1780"}]}
        ln = ik.build_draft_from_invoice(f, kind="expense")["lines"][0]
        self.assertEqual(ln["qty"], "1")
        self.assertEqual(ln["unit_price"], "1780")

    def test_qty_price_kept_when_consistent(self):
        # qty×price 与 subtotal 一致 → 保留明细(不动)。
        f = {"items": [{"name": "x", "qty": "2", "price": "50", "subtotal": "100"}]}
        ln = ik.build_draft_from_invoice(f, kind="expense")["lines"][0]
        self.assertEqual(ln["qty"], "2")
        self.assertEqual(ln["unit_price"], "50")

    def test_tax_invoice_infers_subtotal_from_total_and_vat(self):
        f = {
            "document_type": "tax_invoice",
            "vat": "70",
            "total_amount": "1070",
            "items": [],
        }
        d = ik.build_draft_from_invoice(f, kind="purchase_invoice")
        self.assertTrue(d["has_vat"])
        self.assertEqual(d["lines"][0]["unit_price"], "1000.00")


class OcrCorrectionTests(unittest.TestCase):
    def test_tax_id_normalized_from_labelled_text(self):
        f = ik.normalize_ocr_fields({"seller_tax": "Tax#0107537002443"})
        self.assertEqual(f["seller_tax"], "0107537002443")

    def test_branch_number_not_used_as_invoice_no(self):
        f = ik.normalize_ocr_fields(
            {
                "seller_name": "บริษัท เซ็นทรัลพัฒนา จำกัด (มหาชน) สาขาที่ 00016",
                "invoice_number": "00016",
            }
        )
        self.assertEqual(f["invoice_number"], "")
        self.assertIn("invoice_number_branch_removed", f["_corrections"])

    def test_date_normalized_from_thai_short_year(self):
        f = ik.normalize_ocr_fields({"date": "14/06/26"})
        self.assertEqual(f["date"], "2026-06-14")

    def test_vat_inferred_from_total_subtotal_when_exact_7_percent(self):
        f = ik.normalize_ocr_fields(
            {"document_type": "tax_invoice", "subtotal": "2700", "total_amount": "2889"}
        )
        self.assertEqual(f["vat"], "189.00")

    def test_total_inferred_from_subtotal_and_vat(self):
        f = ik.normalize_ocr_fields({"subtotal": "1000", "vat": "70"})
        self.assertEqual(f["total_amount"], "1070.00")


class ClassifyExpenseTests(unittest.TestCase):
    TREE = [
        {
            "id": "p1",
            "name": "ค่าเดินทางและขนส่ง",
            "children": [{"id": "c1", "name": "ค่าแท็กซี่/แกร็บ"}],
        },
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


class _FakeCur:
    def execute(self, *a, **k):
        return None

    def fetchone(self):
        return {"tax_id": "1234567890123"}


class _FakeCM:
    def __enter__(self):
        return _FakeCur()

    def __exit__(self, *a):
        return False


class LineGateTests(unittest.TestCase):
    """LINE 入账门控(统一智能通道 · 2026-06-15):开 expense 即放行(不按业态分)。

    置信驱动入账见 test_line_image_ingest.py(图)/ test_expense_confidence.py(判级)。
    """

    def _gate(self, expense_on):
        from unittest import mock

        from services.modules import store as mstore

        with mock.patch.object(mstore, "is_enabled", return_value=expense_on):
            return ik.line_expense_gate_open(_FakeCur(), tenant_id="t")

    def test_open_when_expense_on(self):
        self.assertTrue(self._gate(True))

    def test_closed_when_expense_off(self):
        self.assertFalse(self._gate(False))


class ResolveImageIntakeTests(unittest.TestCase):
    """待归类下线:识别完一律建草稿(糊图/฿0/低置信也建),不再落 inbox。"""

    def _resolve(self, fields, confidence, **kw):
        return ik.resolve_image_intake(
            _FakeCur(),
            tenant_id="t",
            workspace_client_id=1,
            fields=fields,
            confidence=confidence,
            settings={},
            **kw,
        )

    def test_zero_amount_still_builds_draft(self):
        # 糊图/金额 ฿0 也建草稿落列表(用户补全),不再兜 inbox。
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "vat": "7",
            "subtotal": "0",
            "items": [],
        }
        data = self._resolve(f, "high")
        self.assertEqual(data["route"], "purchase")
        self.assertIsNotNone(data["draft"])

    def test_low_confidence_builds_draft_not_booked(self):
        # 低置信:建草稿(route 非 booked),不自动过账。
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "vat": "7",
            "subtotal": "1000",
            "items": [{"name": "x", "qty": "1", "price": "1000"}],
        }
        data = self._resolve(f, "needs_review")
        self.assertEqual(data["route"], "purchase")
        self.assertIsNotNone(data["draft"])

    def test_source_propagates_to_draft(self):
        # 来源(line/photo)必须落到草稿,否则 create_doc 默认 manual → 列表显「手录」(PO-6)。
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "vat": "7",
            "subtotal": "1000",
            "items": [{"name": "x", "qty": "1", "price": "1000"}],
        }
        data = self._resolve(f, "high", source="line")
        self.assertIsNotNone(data["draft"])
        self.assertEqual(data["draft"]["source"], "line")


# 旧 F10「LINE 文字静默记一笔 posted 费用」已删(违反 doc 10 §5 死穴:绝不静默入账)。
# 文本路改走 services/expense 引擎:解析→直接落采购草稿单(草稿态待复核,非 posted),
# 覆盖见 test_expense_line_quick_entry.py + test_line_expense_to_purchase.py。


class PaymentDefaultTests(unittest.TestCase):
    """PO-5 智能默认付款态:现金收据 → 已付;税务发票/赊账 → 未付。"""

    def test_receipt_defaults_paid(self):
        self.assertEqual(ik.default_payment_status("receipt", "expense"), "paid")

    def test_tax_invoice_defaults_unpaid(self):
        self.assertEqual(ik.default_payment_status("tax_invoice", "purchase_invoice"), "unpaid")
        self.assertEqual(ik.default_payment_status("simplified_tax_invoice", "expense"), "paid")

    def test_expense_no_type_defaults_paid(self):
        self.assertEqual(ik.default_payment_status("", "expense"), "paid")

    def test_purchase_no_type_defaults_unpaid(self):
        self.assertEqual(ik.default_payment_status("", "purchase_invoice"), "unpaid")

    def test_build_draft_carries_payment_status(self):
        f = {
            "document_type": "receipt",
            "vat": "0",
            "items": [{"name": "x", "qty": "1", "price": "50"}],
        }
        d = ik.build_draft_from_invoice(f, kind="expense")
        self.assertEqual(d["payment_status"], "paid")


if __name__ == "__main__":
    unittest.main()

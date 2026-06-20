# -*- coding: utf-8 -*-
"""票据字段展示清洗(P1F)单测 —— Zihao 必跑 6 样例 + ingestion bug 修复 + 金额改后字段保留。"""

from __future__ import annotations

import unittest
from decimal import Decimal
from unittest import mock

from services.expense import line_correct_data as lcd
from services.expense.expense_draft import ExpenseDraft
from services.purchase import field_clean as fc
from services.purchase import ocr_corrections


class CleanTaxIdTests(unittest.TestCase):
    def test_short_number_rejected(self):  # 样例 1:tax_id=13/15/2026/06 → 空
        for bad in ("13", "15", "2026", "06", "736"):
            self.assertEqual(fc.clean_tax_id(bad), "", bad)

    def test_date_fragment_rejected(self):  # 样例 2:13/06/26 → 空
        self.assertEqual(fc.clean_tax_id("13/06/26"), "")

    def test_valid_kept(self):  # 样例 3:13 位保留
        self.assertEqual(fc.clean_tax_id("0107561000013"), "0107561000013")
        self.assertEqual(fc.clean_tax_id("0105561000013 บริษัท"), "0105561000013")

    def test_non_digit_or_too_long_rejected(self):
        self.assertEqual(fc.clean_tax_id("abc"), "")
        self.assertEqual(fc.clean_tax_id("01075610000131234"), "")  # 17 位 → invalid
        self.assertEqual(fc.clean_tax_id(None), "")


class CleanSellerTests(unittest.TestCase):
    def test_garbage_rejected(self):  # 样例 4:1780.00 / Total / VAT → 空
        for bad in ("1780.00", "Total", "VAT", "13", "13/06/26", "cash", "เงินทอน", "  ", "x"):
            self.assertEqual(fc.clean_seller(bad), "", bad)

    def test_real_seller_kept(self):
        for ok in ("Bangchak", "บางจาก", "7-11", "Total Tools", "ร้านกาแฟ"):
            self.assertEqual(fc.clean_seller(ok), ok, ok)

    def test_numeric_store_number_kept(self):  # B-2:裸「711」实为店号 → 不当金额清空
        self.assertEqual(fc.clean_seller("711"), "711")

    def test_real_amount_still_blanked(self):  # 真金额仍清(非店号)
        self.assertEqual(fc.clean_seller("1780.00"), "")
        self.assertEqual(fc.clean_seller("65"), "")


class CleanInvoiceTests(unittest.TestCase):
    def test_short_no_kept_date_rejected(self):  # 票号允许短号;纯日期不当票号
        self.assertEqual(fc.clean_invoice_no("IV69/00179"), "IV69/00179")
        self.assertEqual(fc.clean_invoice_no("123"), "123")
        self.assertEqual(fc.clean_invoice_no("13/06/26"), "")


class OcrCorrectionsTaxIdTests(unittest.TestCase):
    """ingestion bug:invalid tax 旧实现不覆盖 → 「13」残留进库(详情页显 13)。修后应清空。"""

    def test_invalid_tax_cleared(self):
        self.assertEqual(ocr_corrections.normalize_fields({"seller_tax": "13"})["seller_tax"], "")
        self.assertEqual(
            ocr_corrections.normalize_fields({"seller_tax": "13/06/26"})["seller_tax"], ""
        )

    def test_valid_tax_kept(self):
        out = ocr_corrections.normalize_fields({"seller_tax": "0107561000013"})
        self.assertEqual(out["seller_tax"], "0107561000013")


class AmountEditPreservesFieldsTests(unittest.TestCase):
    """样例 6:OCR 票金额修改后 seller/date/tax_id/invoice_no 不丢,不被异常值覆盖。"""

    def _detail(self):
        return {
            "doc": {"doc_no": "IV69/00179", "doc_date": "2026-06-13", "doc_kind": "expense"},
            "supplier": {"name": "Bangchak", "tax_id": "0107561000013"},
            "lines": [{"unit_price": "1780", "qty": "1", "description": "น้ำมัน"}],
        }

    def test_amount_edit_keeps_other_fields(self):
        data = lcd.detail_to_data(self._detail())
        lcd.apply_changes(None, data, ExpenseDraft(amount=Decimal("1500")), ["amount"], "t", 1, {})
        self.assertEqual(data["supplier"]["name"], "Bangchak")
        self.assertEqual(data["supplier"]["tax_id"], "0107561000013")
        self.assertEqual(data["doc_date"], "2026-06-13")
        self.assertEqual(data["doc_no"], "IV69/00179")
        self.assertEqual(data["lines"][0]["unit_price"], "1500")  # 金额改了


class CorrectionPreservesSupplierTests(unittest.TestCase):
    """改错克隆 roundtrip 必须保留卖家(真机:711咖啡改分类→新单丢卖家·学习按钮缺「以后这家都记」)。

    根因:detail_to_data 原只带卖家名(P1F 把纯数字「711」清成空)不带 supplier_id → update_draft 按
    空名重解析 → supplier_id 被清。修:detail_to_data 带 id,_resolve_supplier 有 id 即沿用。
    """

    def _detail(self):
        return {
            "doc": {"doc_no": "X", "doc_date": "2026-06-13", "doc_kind": "expense"},
            "supplier": {"id": "SUP1", "name": "7-Eleven", "tax_id": "0107542000011"},
            "lines": [
                {"unit_price": "55", "qty": "1", "description": "กาแฟ", "category_id": "old"}
            ],
        }

    def test_detail_to_data_carries_supplier_id(self):
        data = lcd.detail_to_data(self._detail())
        self.assertEqual(data["supplier"]["id"], "SUP1")  # ★id 随单带过去
        self.assertEqual(data["supplier"]["name"], "7-Eleven")

    def test_category_change_keeps_supplier(self):
        data = lcd.detail_to_data(self._detail())
        with mock.patch.object(lcd, "_resolve_category", return_value=("goods", "fin", True)):
            lcd.apply_changes(None, data, ExpenseDraft(note="商品"), ["category"], "t", 1, {})
        self.assertEqual(data["supplier"]["id"], "SUP1")  # ★改分类不丢卖家
        self.assertEqual(data["supplier"]["name"], "7-Eleven")
        self.assertEqual(data["category_id"], "goods")

    def test_date_change_keeps_supplier(self):
        data = lcd.detail_to_data(self._detail())
        lcd.apply_changes(None, data, ExpenseDraft(doc_date="2026-06-20"), ["doc_date"], "t", 1, {})
        self.assertEqual(data["supplier"]["id"], "SUP1")  # 改其它字段同样不丢
        self.assertEqual(data["doc_date"], "2026-06-20")

    def test_vendor_change_rebuilds_without_id(self):
        # 改卖家本身:故意丢 id → 按新名重建/匹配(不回归)。
        data = lcd.detail_to_data(self._detail())
        lcd.apply_changes(
            None, data, ExpenseDraft(vendor_name="Makro"), ["vendor_name"], "t", 1, {}
        )
        self.assertEqual(data["supplier"], {"name": "Makro", "tax_id": None})

    def test_resolve_supplier_id_wins_over_empty_name(self):
        # 核心机制:有 supplier_id 即沿用,即便名被清成空(纯数字「711」)也不丢链接。
        from services.purchase import docs

        sid = docs._resolve_supplier(
            None, tenant_id="t", workspace_client_id=1, supplier={"id": "SUP1", "name": ""}
        )
        self.assertEqual(sid, "SUP1")


class DetailApiSmokeTests(unittest.TestCase):
    """detail API(get_doc)冒烟:嵌套 supplier 与 doc 扁平字段都不得带 invalid 税号(编辑表单读扁平)。"""

    class _Cur:
        def __init__(self, row):
            self.row = row

        def execute(self, *a, **k):
            pass

        def fetchone(self):
            return self.row

        def fetchall(self):
            return []

    def _get(self, raw_tax):
        from services.purchase import docs as docs_svc

        row = {
            "id": "D1",
            "supplier_id": 5,
            "supplier_tax_id": raw_tax,
            "supplier_name": "Bangchak",
            "supplier_branch_type": None,
            "supplier_branch_no": None,
            "supplier_address": None,
            "supplier_phone": None,
            "has_vat": False,  # 存库 false → 验「有效税号是否强制翻 true」
        }
        return docs_svc.get_doc(self._Cur(row), tenant_id="t", workspace_client_id=1, doc_id="D1")

    def test_valid_tax_forces_has_tax_invoice(self):  # 7-11:有税号 → has_vat 不得 false
        res = self._get("0107542000011")
        self.assertTrue(res["doc"]["has_vat"])  # 税务一致性:填了税号不允许显「ไม่มีใบกำกับ」
        self.assertEqual(res["supplier"]["tax_id"], "0107542000011")  # 真税号保留(不清空)

    def test_invalid_tax_does_not_fake_has_tax_invoice(
        self,
    ):  # Bangchak:13 无效 → 不强填·不造假税号
        res = self._get("13")
        self.assertIsNone(res["doc"]["supplier_tax_id"])  # 假税号清空(不留 13)
        self.assertFalse(res["doc"]["has_vat"])  # 无有效税号 → 不强填 has_vat

    def test_bangchak_fixture_taxid_13_cleared(self):  # 票一:Bangchak 1780
        res = self._get("13")
        self.assertIsNone(res["supplier"]["tax_id"])  # 嵌套
        self.assertIsNone(res["doc"]["supplier_tax_id"])  # 扁平(编辑表单 initial state 读这个)
        self.assertEqual(res["supplier"]["name"], "Bangchak")  # 卖家保留

    def test_restaurant_fixture_taxid_cleared(self):  # 票二:餐厅桌单 736(日期 15/06/26·税号也误读)
        for raw in ("13", "15", "15/06/26"):
            res = self._get(raw)
            self.assertIsNone(res["supplier"]["tax_id"], raw)
            self.assertIsNone(res["doc"]["supplier_tax_id"], raw)

    def test_date_fragment_tax_cleared(self):
        res = self._get("13/06/26")
        self.assertIsNone(res["supplier"]["tax_id"])
        self.assertIsNone(res["doc"]["supplier_tax_id"])

    def test_valid_tax_preserved_both(self):
        res = self._get("0107561000013")
        self.assertEqual(res["supplier"]["tax_id"], "0107561000013")
        self.assertEqual(res["doc"]["supplier_tax_id"], "0107561000013")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""进项明细 → 一行一明细导出行(export.rows.build_export_rows)· 纯函数(阶段二)。

锁:一单 N 行展 N 行 · 文档级字段逐行重复 · VAT/WHT 逐行算 · 整单折扣/凑整只落首行 ·
分类 id→名 · 借/贷/凭证号/入账状态来自 posting 摘要。
"""

import unittest
from decimal import Decimal

from services.export.entries import summarize_voucher
from services.export.rows import build_export_rows


def _item():
    return {
        "doc": {
            "id": "D1",
            "doc_date": "2026-06-01",
            "doc_no": "INV1",
            "doc_kind": "purchase_invoice",
            "payment_status": "unpaid",
            "has_vat": True,
            "discount_total": "10",
            "rounding": "0",
            "requester": "Aae",
        },
        "lines": [
            {
                "description": "A",
                "qty": "2",
                "unit_price": "100",
                "line_total": "200",
                "discount": "0",
                "vat_rate": "7",
                "vat_applicable": True,
                "wht_rate": "0",
                "item_type": "goods",
                "category_id": "c1",
                "subcategory_id": "s1",
            },
            {
                "description": "B",
                "qty": "1",
                "unit_price": "50",
                "line_total": "50",
                "discount": "0",
                "vat_rate": "7",
                "vat_applicable": True,
                "wht_rate": "3",
                "item_type": "service",
                "category_id": "c2",
                "subcategory_id": None,
            },
        ],
        "supplier": {
            "name": "Sup",
            "tax_id": "0105",
            "branch_type": "head_office",
            "branch_no": "00000",
            "address": "BKK",
        },
        "posting": summarize_voucher(
            {
                "voucher_no": "JV1",
                "status": "posted",
                "lines": [
                    {
                        "dr_cr": "debit",
                        "account_code": "5000",
                        "account_name": "采购",
                        "amount": "250",
                    },
                    {
                        "dr_cr": "credit",
                        "account_code": "2100",
                        "account_name": "应付",
                        "amount": "250",
                    },
                ],
            }
        ),
        "evidence_url": "/api/purchase/docs/D1/bill-image?idx=0",
    }


_CATS = {"c1": "办公", "s1": "文具", "c2": "差旅"}


class BuildExportRowsTests(unittest.TestCase):
    def setUp(self):
        self.rows = build_export_rows([_item()], category_names=_CATS)

    def test_one_doc_two_lines_two_rows(self):
        self.assertEqual(len(self.rows), 2)

    def test_per_line_vat_wht(self):
        self.assertEqual(self.rows[0]["line_vat"], Decimal("14.00"))
        self.assertEqual(self.rows[1]["line_vat"], Decimal("3.50"))
        self.assertEqual(self.rows[1]["line_wht"], Decimal("1.50"))

    def test_doc_discount_and_rounding_only_on_first_line(self):
        self.assertEqual(self.rows[0]["doc_discount"], Decimal("10"))
        self.assertEqual(self.rows[1]["doc_discount"], Decimal("0"))

    def test_category_name_lookup(self):
        self.assertEqual(self.rows[0]["category"], "办公")
        self.assertEqual(self.rows[0]["subcategory"], "文具")
        self.assertEqual(self.rows[1]["subcategory"], "")  # None → 空

    def test_doc_fields_repeated_each_line(self):
        for r in self.rows:
            self.assertEqual(r["doc_no"], "INV1")
            self.assertEqual(r["doc_kind"], "进货发票")
            self.assertEqual(r["supplier_name"], "Sup")

    def test_posting_columns_from_summary(self):
        self.assertEqual(self.rows[0]["debit"], "5000 采购 250")
        self.assertEqual(self.rows[0]["credit"], "2100 应付 250")
        self.assertEqual(self.rows[0]["voucher_no"], "JV1")
        self.assertEqual(self.rows[0]["posting_status"], "已过账")

    def test_item_type_labels(self):
        self.assertEqual(self.rows[0]["item_type"], "商品")
        self.assertEqual(self.rows[1]["item_type"], "服务")

    def test_not_posted_when_no_voucher(self):
        item = _item()
        item["posting"] = summarize_voucher(None)
        rows = build_export_rows([item], category_names=_CATS)
        self.assertEqual(rows[0]["posting_status"], "未记账")
        self.assertEqual(rows[0]["voucher_no"], "")


if __name__ == "__main__":
    unittest.main()

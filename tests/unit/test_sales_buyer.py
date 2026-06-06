# -*- coding: utf-8 -*-
"""买方动态模块守门测试(归一化清空 + 完整性闸 · docs/15 §7 验收 · 不连库)。"""

import unittest

from services.sales import buyer


class NormalizeTests(unittest.TestCase):
    def test_unknown_type_falls_back_to_company(self):
        b = buyer.normalize_buyer({"type": "alien"})
        self.assertEqual(b["type"], "company")

    def test_company_keeps_branch(self):
        b = buyer.normalize_buyer(
            {
                "type": "company",
                "tax_id": " 1234567890123 ",
                "branch_type": "branch",
                "branch_no": "00001",
            }
        )
        self.assertEqual(b["tax_id"], "1234567890123")
        self.assertEqual(b["branch_type"], "branch")
        self.assertEqual(b["branch_no"], "00001")

    def test_company_hq_clears_branch_no(self):
        b = buyer.normalize_buyer({"type": "company", "branch_type": "hq", "branch_no": "99999"})
        self.assertEqual(b["branch_type"], "hq")
        self.assertIsNone(b["branch_no"])

    def test_individual_drops_branch_keeps_taxid(self):
        b = buyer.normalize_buyer(
            {
                "type": "individual",
                "tax_id": "1234567890123",
                "branch_type": "branch",
                "branch_no": "00001",
            }
        )
        self.assertIsNone(b["branch_type"])
        self.assertIsNone(b["branch_no"])
        self.assertEqual(b["tax_id"], "1234567890123")

    def test_anonymous_clears_taxid(self):
        b = buyer.normalize_buyer({"type": "anonymous", "tax_id": "1234567890123"})
        self.assertEqual(b["tax_id"], "")
        self.assertIsNone(b["branch_type"])

    def test_round_trip_leaves_no_stale_values(self):
        """docs/15 §7:公司(含税号+分店)→个人→匿名→公司,不得残留上一类型的值。"""
        # 公司填满
        b = buyer.normalize_buyer(
            {
                "type": "company",
                "name": "ACME",
                "address": "BKK",
                "tax_id": "1111111111111",
                "branch_type": "branch",
                "branch_no": "00002",
            }
        )
        # 切个人:税号是新类型的语义,前端会清;后端拿到的是新块
        b = buyer.normalize_buyer({"type": "individual", "name": "ACME", "address": "BKK"})
        self.assertEqual(b["tax_id"], "")
        self.assertIsNone(b["branch_type"])
        self.assertIsNone(b["branch_no"])
        # 切匿名
        b = buyer.normalize_buyer({"type": "anonymous", "name": "ACME", "address": "BKK"})
        self.assertEqual(b["tax_id"], "")
        # 切回公司:branch 重置默认 hq,无脏 branch_no
        b = buyer.normalize_buyer({"type": "company", "name": "ACME", "address": "BKK"})
        self.assertEqual(b["branch_type"], "hq")
        self.assertIsNone(b["branch_no"])
        self.assertEqual(b["name"], "ACME")  # 姓名跨类型保留


class ValidateTests(unittest.TestCase):
    def _company(self, **over):
        base = {
            "type": "company",
            "name": "ACME",
            "address": "BKK",
            "tax_id": "1234567890123",
            "branch_type": "hq",
        }
        base.update(over)
        return base

    def test_full_company_ok(self):
        self.assertIsNone(buyer.validate_buyer(self._company(), "tax_invoice"))

    def test_full_invoice_missing_name_incomplete(self):
        self.assertEqual(
            buyer.validate_buyer(self._company(name=""), "tax_invoice"), "buyer_incomplete"
        )

    def test_anonymous_cannot_back_full_invoice(self):
        b = {"type": "anonymous", "name": "", "address": ""}
        self.assertEqual(buyer.validate_buyer(b, "tax_invoice"), "buyer_incomplete")

    def test_anonymous_ok_for_simple_invoice(self):
        b = {"type": "anonymous"}
        self.assertIsNone(buyer.validate_buyer(b, "tax_invoice_simple"))

    def test_bad_th13_rejected(self):
        self.assertEqual(
            buyer.validate_buyer(self._company(tax_id="123"), "tax_invoice"),
            "buyer_tax_id_invalid",
        )

    def test_passport_validator_for_foreigner(self):
        b = {"type": "foreigner", "name": "John", "address": "TH", "tax_id": "AB12"}
        self.assertIsNone(buyer.validate_buyer(b, "tax_invoice"))
        b["tax_id"] = "!@#"
        self.assertEqual(buyer.validate_buyer(b, "tax_invoice"), "buyer_tax_id_invalid")

    def test_company_branch_required_on_full_invoice(self):
        self.assertEqual(
            buyer.validate_buyer(self._company(branch_type=None), "tax_invoice"),
            "buyer_branch_required",
        )

    def test_company_branch_no_must_be_5_digits(self):
        b = self._company(branch_type="branch", branch_no="12")
        self.assertEqual(buyer.validate_buyer(b, "tax_invoice"), "buyer_branch_no_invalid")

    def test_combined_doc_treated_as_full(self):
        b = {"type": "anonymous"}
        self.assertEqual(buyer.validate_buyer(b, "tax_invoice_receipt"), "buyer_incomplete")

    def test_receipt_does_not_force_full_buyer(self):
        self.assertIsNone(buyer.validate_buyer({"type": "anonymous"}, "receipt"))


class ColumnMappingTests(unittest.TestCase):
    def test_to_columns_and_back(self):
        b = buyer.normalize_buyer(
            {
                "type": "company",
                "name": "ACME",
                "address": "BKK",
                "tax_id": "1234567890123",
                "branch_type": "branch",
                "branch_no": "00001",
            }
        )
        cols = buyer.to_columns(b)
        self.assertEqual(cols["buyer_type"], "company")
        self.assertEqual(cols["buyer_branch_no"], "00001")
        again = buyer.from_row(cols)
        self.assertEqual(again["type"], "company")
        self.assertEqual(again["branch_no"], "00001")


if __name__ == "__main__":
    unittest.main()

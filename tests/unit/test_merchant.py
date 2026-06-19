# -*- coding: utf-8 -*-
"""商户身份归一(P2A · 学习键 + 匹配):不同写法收敛同键;税号 → 别名。"""

import unittest

from services.expense import merchant


class NormalizeMerchantTests(unittest.TestCase):
    def test_case_and_punct_stripped(self):
        self.assertEqual(
            merchant.normalize_merchant("Cafe-Amazon"), merchant.normalize_merchant("cafe amazon")
        )

    def test_company_suffix_stripped(self):
        # 「บริษัท X จำกัด (มหาชน)」与「X」同键
        a = merchant.normalize_merchant("บริษัท สยามแม็คโคร จำกัด (มหาชน)")
        b = merchant.normalize_merchant("สยามแม็คโคร")
        self.assertEqual(a, b)

    def test_english_suffix_stripped(self):
        a = merchant.normalize_merchant("Acme Co., Ltd.")
        b = merchant.normalize_merchant("Acme")
        self.assertEqual(a, b)

    def test_empty(self):
        self.assertEqual(merchant.normalize_merchant(""), "")
        self.assertEqual(merchant.normalize_merchant(None), "")


class CanonicalMerchantTests(unittest.TestCase):
    def test_seven_eleven_variants_same_key(self):
        keys = {
            merchant.canonical_merchant("7-ELEVEN"),
            merchant.canonical_merchant("7-Eleven สาขา 123"),
            merchant.canonical_merchant("7-11"),
            merchant.canonical_merchant("CP ALL"),
            merchant.canonical_merchant("บริษัท ซีพี ออลล์ จำกัด (มหาชน)"),
            merchant.canonical_merchant("เซเว่นอีเลฟเว่น"),
        }
        self.assertEqual(keys, {"7-eleven"})

    def test_makro_variants_same_key(self):
        self.assertEqual(merchant.canonical_merchant("Makro"), "makro")
        self.assertEqual(merchant.canonical_merchant("แม็คโคร สาขาลาดพร้าว"), "makro")

    def test_fuel_brands(self):
        self.assertEqual(merchant.canonical_merchant("บางจาก"), "bangchak")
        self.assertEqual(merchant.canonical_merchant("PTT Station"), "ptt")

    def test_unknown_merchant_falls_to_normalized(self):
        self.assertEqual(
            merchant.canonical_merchant("ร้านป้าแดง"), merchant.normalize_merchant("ร้านป้าแดง")
        )

    def test_tax_id_resolves_brand_when_name_garbled(self):
        # 卖家名糊但税号是 CP ALL → 仍归 7-eleven 键
        self.assertEqual(merchant.canonical_merchant("?????", "0107542000011"), "7-eleven")


class MerchantAliasByTaxTests(unittest.TestCase):
    def test_known_tax(self):
        self.assertEqual(merchant.merchant_alias_by_tax("0107542000011"), "7-eleven cp all")

    def test_unknown_tax_empty(self):
        self.assertEqual(merchant.merchant_alias_by_tax("9999999999999"), "")
        self.assertEqual(merchant.merchant_alias_by_tax(""), "")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""services/ocr/money 归一单测(sanity 与 invoice eval 共用)。"""

import unittest

from services.ocr.money import normalize_id, normalize_money


class NormalizeMoneyTests(unittest.TestCase):
    def test_parses_commas_currency(self):
        self.assertEqual(normalize_money("฿1,780.00"), 1780.0)
        self.assertEqual(normalize_money("1,780"), 1780.0)
        self.assertEqual(normalize_money(1780), 1780.0)
        self.assertEqual(normalize_money("-114.5"), -114.5)

    def test_blank_unparsable_none(self):
        for v in (None, "", "  ", "บาท", "-", ".", "abc"):
            self.assertIsNone(normalize_money(v), v)


class NormalizeIdTests(unittest.TestCase):
    def test_keeps_digits_only(self):
        self.assertEqual(normalize_id("0-7355-27000-28-9"), "0735527000289")
        self.assertEqual(normalize_id(None), "")


if __name__ == "__main__":
    unittest.main()

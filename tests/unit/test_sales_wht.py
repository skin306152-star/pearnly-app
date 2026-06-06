# -*- coding: utf-8 -*-
"""销项 §L2 · WHT 多档预设 + 票面标签守门。"""

import unittest
from decimal import Decimal

from services.sales import wht


class WhtTests(unittest.TestCase):
    def test_presets_cover_standard_brackets(self):
        rates = [r for r, _ in wht.WHT_PRESETS]
        for expected in ("0", "1", "2", "3", "5"):
            self.assertIn(expected, rates)

    def test_pdf_label_includes_rate(self):
        self.assertIn("3%", wht.pdf_label("3"))
        self.assertIn("หัก ณ ที่จ่าย", wht.pdf_label("3"))

    def test_pdf_label_strips_trailing_zeros(self):
        self.assertIn("3%", wht.pdf_label(Decimal("3.00")))
        self.assertIn("1.5%", wht.pdf_label(Decimal("1.50")))

    def test_pdf_label_handles_none(self):
        self.assertIn("0%", wht.pdf_label(None))


if __name__ == "__main__":
    unittest.main()

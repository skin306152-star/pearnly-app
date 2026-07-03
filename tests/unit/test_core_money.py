# -*- coding: utf-8 -*-
"""core.money.amounts_equal — 跨域金额精确相等(Decimal·无容差·不可解→False)。"""

import unittest

from core.money import amounts_equal


class TestAmountsEqual(unittest.TestCase):
    def test_numeric_equal_across_types(self):
        self.assertTrue(amounts_equal("120", 120.00))
        self.assertTrue(amounts_equal(120, "120.00"))
        self.assertTrue(amounts_equal("0", 0))

    def test_not_equal(self):
        self.assertFalse(amounts_equal("120", 250))
        self.assertFalse(amounts_equal(120.01, 120.02))  # 无容差:分位不同即不等

    def test_no_float_drift(self):
        # Decimal 逐位:字符串来源不受 float 0.1+0.2 漂移影响
        self.assertTrue(amounts_equal("0.30", "0.30"))

    def test_unparseable_is_false(self):
        self.assertFalse(amounts_equal("120", None))
        self.assertFalse(amounts_equal(None, None))
        self.assertFalse(amounts_equal("abc", 1))
        self.assertFalse(amounts_equal("120", ""))


if __name__ == "__main__":
    unittest.main()

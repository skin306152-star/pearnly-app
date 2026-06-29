# -*- coding: utf-8 -*-
"""bank_arbitration_guard.divergence_reasons 单测(确定性·不连模型)。

锁:两法都出行才比、符号相反必判分歧(BBL 346万 vs −114万)、相对阈/绝对地板、
一方空不算分歧(兜底接管)。
"""

import unittest

from services.recon.bank_arbitration_guard import divergence_reasons


class DivergenceTests(unittest.TestCase):
    def test_opposite_sign_flagged(self):
        # BBL2645:免费 +3,463,701 vs Gemini −1,141,561 → 必分歧。
        r = divergence_reasons(None, 3463701.0, 18, None, -1141561.0, 18)
        self.assertTrue(any("期末两法分歧" in x for x in r))

    def test_close_values_not_flagged(self):
        # 两法期末几乎一致(尾差 < 1 铢)→ 不分歧。
        self.assertEqual(divergence_reasons(100.0, 5000.0, 30, 100.0, 5000.5, 30), [])

    def test_large_relative_gap_flagged(self):
        # 期初 3543 vs 90544(AMZ 类)→ 相对差远超 5%。
        r = divergence_reasons(3543.84, 0.0, 29, 90544.07, 0.0, 29)
        self.assertTrue(any("期初两法分歧" in x for x in r))

    def test_one_side_empty_not_divergence(self):
        # 免费 0 行(Gemini 接管)→ 不是分歧。
        self.assertEqual(divergence_reasons(None, 0.0, 0, 26.89, 26.89, 2), [])
        self.assertEqual(divergence_reasons(26.89, 26.89, 2, None, 0.0, 0), [])

    def test_within_threshold_not_flagged(self):
        # 差 5000/100000 = 5% 边界内 → 不报(吸收尾差)。
        self.assertEqual(divergence_reasons(None, 100000.0, 50, None, 104000.0, 50), [])

    def test_none_values_skipped(self):
        self.assertEqual(divergence_reasons(None, None, 10, None, None, 10), [])


if __name__ == "__main__":
    unittest.main()

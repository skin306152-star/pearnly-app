# -*- coding: utf-8 -*-
"""银行对账单两位年的消歧守门(此前零测试覆盖)。

泰国对账单上的 `31/05/69` 是佛历 2569(=2026),旧判据 `yy<70 → 2000+yy` 把它
解成 2069,而后面的 2000..2099 窗校验对 2069 照样放行 —— 未来 43 年的流水静默落库。
函数签名里的 reference(账期)当年就在,却从没被用过。
"""

from __future__ import annotations

import unittest

from core import thai_date
from services.recon.bank_stmt_legacy_fields import _normalize_thai_date, _reference_year


class TwoDigitYearTests(unittest.TestCase):
    def test_buddhist_shorthand_resolves_to_current_era(self):
        self.assertEqual(_normalize_thai_date("31/05/69", "2026-05-31"), "2026-05-31")

    def test_old_rule_would_have_given_2069(self):
        """回归钉子:旧判据 2000+69=2069 且能过窗校验。"""
        self.assertNotEqual(_normalize_thai_date("31/05/69", "2026-05-31"), "2069-05-31")

    def test_gregorian_two_digit_still_works(self):
        self.assertEqual(_normalize_thai_date("15/03/26", "2026-03-31"), "2026-03-15")

    def test_reference_anchors_the_choice(self):
        # 锚在 2025 → 佛历 2568 更近;锚在 2068 → 公历 2068 更近
        self.assertEqual(_normalize_thai_date("01/02/68", "2025-02-28"), "2025-02-01")
        self.assertEqual(_normalize_thai_date("01/02/68", "2068-02-28"), "2068-02-01")

    def test_four_digit_buddhist_year(self):
        self.assertEqual(_normalize_thai_date("31/05/2569", "2026-05-31"), "2026-05-31")

    def test_four_digit_gregorian_year(self):
        self.assertEqual(_normalize_thai_date("31/05/2026", "2026-05-31"), "2026-05-31")

    def test_malformed_input_returns_none(self):
        for v in ("", None, "31/05", "aa/bb/cc", "99/99/2569"):
            self.assertIsNone(_normalize_thai_date(v, "2026-05-31"), v)


class ReferenceYearTests(unittest.TestCase):
    def test_parses_iso_and_partial_forms(self):
        self.assertEqual(_reference_year("2026-05-31"), 2026)
        self.assertEqual(_reference_year("2026-05"), 2026)
        self.assertEqual(_reference_year("2026"), 2026)

    def test_buddhist_reference_normalized(self):
        self.assertEqual(_reference_year("2569-05-31"), 2026)

    def test_unparsable_returns_none(self):
        for v in (None, "", "n/a"):
            self.assertIsNone(_reference_year(v), v)


class TwoDigitHelperTests(unittest.TestCase):
    def test_picks_candidate_nearest_anchor(self):
        self.assertEqual(thai_date.two_digit_year_to_gregorian(69, 2026), 2026)
        self.assertEqual(thai_date.two_digit_year_to_gregorian(26, 2026), 2026)
        self.assertEqual(thai_date.two_digit_year_to_gregorian(68, 2026), 2025)
        self.assertEqual(thai_date.two_digit_year_to_gregorian(69, 2068), 2069)


if __name__ == "__main__":
    unittest.main(verbosity=2)

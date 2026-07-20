# -*- coding: utf-8 -*-
"""编辑历史记录时按票面日期反推库里的公历值。

会计看到和填写的是票面那一串(泰国票面印佛历 พ.ศ.),库里 DATE 列必须是公历 ——
换算只在这一处发生,界面上不出现公历,人不需要知道它存在。
"""

from __future__ import annotations

import unittest

from core import thai_date
from routes.history_routes import _derive_dates_from_printed


def _pages(printed, stored="2016-05-31"):
    return [{"fields": {"date_raw": printed, "date": stored, "invoice_number": "IV69/00475"}}]


class DeriveFromPrintedTests(unittest.TestCase):
    def test_buddhist_printed_date_becomes_gregorian(self):
        pages = _pages("31/5/2569")
        self.assertIsNone(_derive_dates_from_printed(pages))
        self.assertEqual(pages[0]["fields"]["date"], "2026-05-31")

    def test_correcting_the_printed_year_updates_stored_date(self):
        """事故场景:票面 2569 被读成 2559,人照票面改回来,库里的值要跟着走。"""
        pages = _pages("31/5/2569", stored="2016-05-31")
        _derive_dates_from_printed(pages)
        self.assertEqual(pages[0]["fields"]["date"], "2026-05-31")

    def test_editing_day_and_month_too(self):
        pages = _pages("15/3/2569")
        _derive_dates_from_printed(pages)
        self.assertEqual(pages[0]["fields"]["date"], "2026-03-15")

    def test_gregorian_printed_date_kept(self):
        pages = _pages("31/5/2026")
        _derive_dates_from_printed(pages)
        self.assertEqual(pages[0]["fields"]["date"], "2026-05-31")

    def test_unreadable_printed_date_is_reported(self):
        self.assertEqual(_derive_dates_from_printed(_pages("ไม่ทราบ")), "ไม่ทราบ")

    def test_missing_printed_falls_back_to_stored_and_still_blocks_buddhist(self):
        # 旧记录没有 date_raw:不动 date,但守住"库里不许存佛历年"
        pages = [{"fields": {"date": "2026-05-31"}}]
        self.assertIsNone(_derive_dates_from_printed(pages))
        self.assertEqual(_derive_dates_from_printed([{"fields": {"date": "2569-05-31"}}]), "2569-05-31")

    def test_tolerates_malformed_pages(self):
        self.assertIsNone(_derive_dates_from_printed(None))
        self.assertIsNone(_derive_dates_from_printed(["x", None, {}]))


class GregorianFromPrintedTests(unittest.TestCase):
    def test_thai_style_day_first(self):
        self.assertEqual(thai_date.gregorian_from_printed("31/5/2569"), "2026-05-31")
        self.assertEqual(thai_date.gregorian_from_printed("31-05-2569"), "2026-05-31")
        self.assertEqual(thai_date.gregorian_from_printed("31.5.2569"), "2026-05-31")

    def test_two_digit_year_uses_anchor(self):
        self.assertEqual(thai_date.gregorian_from_printed("31/5/69", 2026), "2026-05-31")

    def test_iso_input(self):
        self.assertEqual(thai_date.gregorian_from_printed("2026-05-31"), "2026-05-31")
        self.assertEqual(thai_date.gregorian_from_printed("2569-05-31"), "2026-05-31")

    def test_unparsable(self):
        for v in ("", None, "n/a", "31/5", "99/99/2569"):
            self.assertIsNone(thai_date.gregorian_from_printed(v), v)


if __name__ == "__main__":
    unittest.main(verbosity=2)

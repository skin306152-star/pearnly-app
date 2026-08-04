# -*- coding: utf-8 -*-
"""开票日期/历法守门测试(曼谷本地日 + 倒填护栏 + 佛历 · docs/16 §G · 不连库)。"""

import unittest
from datetime import date, datetime, timezone

from services.sales import dates


class IssueDateGuardTests(unittest.TestCase):
    def test_today_ok(self):
        ref = date(2026, 6, 15)
        self.assertIsNone(dates.validate_issue_date(ref, today=ref))

    def test_backdate_within_month_ok(self):
        self.assertIsNone(dates.validate_issue_date(date(2026, 6, 1), today=date(2026, 6, 15)))

    def test_future_blocked(self):
        self.assertEqual(
            dates.validate_issue_date(date(2026, 6, 16), today=date(2026, 6, 15)),
            "future_issue_date",
        )

    def test_backdate_cross_month_blocked(self):
        self.assertEqual(
            dates.validate_issue_date(date(2026, 5, 31), today=date(2026, 6, 1)),
            "backdate_cross_period",
        )

    def test_cross_year_is_cross_period(self):
        self.assertEqual(
            dates.validate_issue_date(date(2025, 12, 31), today=date(2026, 1, 2)),
            "backdate_cross_period",
        )


class ThaiDateTests(unittest.TestCase):
    def test_buddhist_era_from_date(self):
        self.assertEqual(dates.to_thai_date(date(2026, 6, 6)), "06/06/2569")

    def test_buddhist_era_from_iso_string(self):
        self.assertEqual(dates.to_thai_date("2026-06-06"), "06/06/2569")

    def test_unparseable_returns_input(self):
        self.assertEqual(dates.to_thai_date("not-a-date"), "not-a-date")
        self.assertEqual(dates.to_thai_date(None), "-")


class BangkokTodayTests(unittest.TestCase):
    def test_returns_a_date(self):
        self.assertIsInstance(dates.bangkok_today(), date)


class IsoBangkokTests(unittest.TestCase):
    def test_aware_converts_to_bangkok(self):
        """UTC 晚间 = 曼谷次日凌晨:消费端直接切串,转错会把凌晨单显示成前一天。"""
        v = datetime(2026, 8, 4, 18, 30, tzinfo=timezone.utc)
        self.assertEqual(dates.iso_bangkok(v), "2026-08-05T01:30:00+07:00")

    def test_naive_passes_through(self):
        """naive 视为已是本地值原样输出,不按机器时区猜(CI 是 UTC 机,猜会假红)。"""
        self.assertEqual(dates.iso_bangkok(datetime(2026, 7, 8, 9, 16, 11)), "2026-07-08T09:16:11")

    def test_empty_gives_none(self):
        self.assertIsNone(dates.iso_bangkok(None))


if __name__ == "__main__":
    unittest.main()

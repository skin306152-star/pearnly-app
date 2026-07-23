# -*- coding: utf-8 -*-
"""佛历/公历判定口径守门。

入口挡佛历年落库的依据 —— 库里日期列全是公历,佛历只在出口按目标系统渲染。
"""

from __future__ import annotations

import unittest

from core import thai_date


class LooksBuddhistTests(unittest.TestCase):
    def test_buddhist_years(self):
        self.assertTrue(thai_date.looks_buddhist(2569))
        self.assertTrue(thai_date.looks_buddhist(2400))  # 下界含

    def test_gregorian_years(self):
        self.assertFalse(thai_date.looks_buddhist(2026))
        self.assertFalse(thai_date.looks_buddhist(2399))
        self.assertFalse(thai_date.looks_buddhist(1999))


class ToGregorianYearTests(unittest.TestCase):
    def test_converts_buddhist(self):
        self.assertEqual(thai_date.to_gregorian_year(2569), 2026)
        self.assertEqual(thai_date.to_gregorian_year(2559), 2016)

    def test_leaves_gregorian_untouched(self):
        self.assertEqual(thai_date.to_gregorian_year(2026), 2026)


class BuddhistYearOfTests(unittest.TestCase):
    def test_flags_buddhist_iso_date(self):
        # 用户在只收公历的日期框里按泰国习惯填佛历 —— 本闸要拦的就是这个
        self.assertEqual(thai_date.buddhist_year_of("2569-05-31"), 2569)

    def test_passes_gregorian_iso_date(self):
        self.assertIsNone(thai_date.buddhist_year_of("2026-05-31"))

    def test_ignores_non_iso_and_empty(self):
        for v in ("31/5/2569", "", None, "not-a-date", 20260531):
            self.assertIsNone(thai_date.buddhist_year_of(v), v)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class GregorianPeriodTests(unittest.TestCase):
    """B-6 前置:工单期间是佛历,票面日期是公历,不换算任何「距今几个月」的判据都恒不触发。"""

    def test_buddhist_period_converts(self):
        self.assertEqual(thai_date.gregorian_period("2569-05"), "2026-05")

    def test_gregorian_period_is_idempotent(self):
        self.assertEqual(thai_date.gregorian_period("2026-05"), "2026-05")

    def test_garbage_returns_none_instead_of_guessing(self):
        for bad in ("", None, "bad", "2569", "2569-13", "2569-00", 2569):
            with self.subTest(value=bad):
                self.assertIsNone(thai_date.gregorian_period(bad))

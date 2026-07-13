# -*- coding: utf-8 -*-
"""税历截止日顺延纯函数单测(services/workorder/due_date_rules.py · MC2-B 件2)。

钉死方案金标:①周末顺延(2569-08-15 周六 → 周一 08-17)②已知泰国假日单点顺延
③紧邻假日的周末(连假)逐日前推到工作日 ④非顺延日逐字节不动(存量快照回归护栏)
⑤None 直通版(读侧序列化空日期场景)。
"""

from __future__ import annotations

import unittest
from datetime import date

from services.workorder.due_date_rules import (
    THAI_HOLIDAYS_2026,
    THAI_HOLIDAYS_2027,
    defer_due_date,
    defer_optional,
)


class DeferDueDateTests(unittest.TestCase):
    def test_golden_weekend_case_2026_08_15_saturday_to_monday(self):
        """方案金标:2569-08-15(周六)→ 顺延至周一 2026-08-17。"""
        self.assertEqual(date(2026, 8, 15).weekday(), 5)  # 周六,前提校验
        self.assertEqual(defer_due_date(date(2026, 8, 15)), date(2026, 8, 17))

    def test_sunday_defers_to_monday(self):
        self.assertEqual(date(2026, 8, 16).weekday(), 6)
        self.assertEqual(defer_due_date(date(2026, 8, 16)), date(2026, 8, 17))

    def test_known_holiday_2026_new_year_defers_to_next_workday(self):
        """2026-01-01(元旦,周四)本身非周末但是法定假日,须顺延——紧邻 01-02 内阁加假,
        再紧邻周末,连续三天不可用,顺延到下周一 01-05。"""
        self.assertEqual(defer_due_date(date(2026, 1, 1)), date(2026, 1, 5))

    def test_known_holiday_2027_constitution_day_weekday_case(self):
        """2027-12-10(宪法纪念日,周五)是纯假日单点顺延案例(不叠加周末),顺延到下周一。"""
        self.assertEqual(date(2027, 12, 10).weekday(), 4)  # 周五
        self.assertEqual(defer_due_date(date(2027, 12, 10)), date(2027, 12, 13))

    def test_consecutive_holidays_songkran_defers_past_entire_block(self):
        """宋干节三连休(2026-04-13~15,周一至周三)落在中段(04-14)也要一路顺延过整段,
        不能只跳一天又落回假日里。"""
        self.assertEqual(defer_due_date(date(2026, 4, 14)), date(2026, 4, 16))

    def test_holiday_adjacent_to_weekend_defers_through_both(self):
        """卫塞节补假(2026-06-01 周一)前一天是真正的卫塞节(05-31 周日),落在周日的
        截止日要连续跨过「周日假日 + 周一补假」才落到工作日 06-02。"""
        self.assertEqual(defer_due_date(date(2026, 5, 31)), date(2026, 6, 2))

    def test_regular_weekday_is_untouched_byte_for_byte(self):
        """非顺延日逐字节不动(存量义务快照回归护栏):普通工作日原样返回,不是新对象值。"""
        d = date(2026, 8, 20)  # 周四,非假日
        self.assertEqual(d.weekday(), 3)
        self.assertEqual(defer_due_date(d), d)

    def test_unlisted_year_only_defers_weekend_not_guessed_holidays(self):
        """假日表外年份(未录入)只按周末顺延,不假装认识没数据的年份——诚实降级。"""
        # 2030-01-05 是周六,表外年份仍按通用周末规则顺延到周一。
        self.assertEqual(date(2030, 1, 5).weekday(), 5)
        self.assertEqual(defer_due_date(date(2030, 1, 5)), date(2030, 1, 7))

    def test_defer_optional_passes_through_none(self):
        self.assertIsNone(defer_optional(None))

    def test_defer_optional_defers_real_date(self):
        self.assertEqual(defer_optional(date(2026, 8, 15)), date(2026, 8, 17))

    def test_holiday_tables_are_disjoint_year_scoped(self):
        """2026/2027 两张表各自年份内不串,金标要求"至少两年数据都有"的存在性护栏。"""
        self.assertTrue(all(d.year == 2026 for d in THAI_HOLIDAYS_2026))
        self.assertTrue(all(d.year == 2027 for d in THAI_HOLIDAYS_2027))
        self.assertGreaterEqual(len(THAI_HOLIDAYS_2026), 2)
        self.assertGreaterEqual(len(THAI_HOLIDAYS_2027), 2)


if __name__ == "__main__":
    unittest.main()

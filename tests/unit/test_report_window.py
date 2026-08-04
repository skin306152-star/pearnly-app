# -*- coding: utf-8 -*-
"""POS 报表窗口单一事实源:SQL 形状与半开边界参数。

AT TIME ZONE 的真实执行语义(边界票归属)由真库 E2E 验证:docs/pos/_e2e_report_bkk_daycut.py。
"""

import unittest
from datetime import date

from services.pos.report_window import bangkok_day_range


class BangkokDayRangeTests(unittest.TestCase):
    def test_half_open_bangkok(self):
        """曼谷 2026-08-05 单日窗口 = [08-04T17:00Z, 08-05T17:00Z):日期参数在 SQL 里按
        Asia/Bangkok 解释成绝对时刻,含凌晨 0–7 点的单;裸比较 date 会按 UTC 切日。"""
        clause, params = bangkok_day_range("sold_at", date(2026, 8, 5), date(2026, 8, 5))
        self.assertIn("sold_at >= (%s::timestamp AT TIME ZONE 'Asia/Bangkok')", clause)
        self.assertIn("sold_at < (%s::timestamp AT TIME ZONE 'Asia/Bangkok')", clause)
        self.assertEqual(params, [date(2026, 8, 5), date(2026, 8, 6)])  # to + 1 天(含 to 当天)

    def test_single_bound_and_col_injection(self):
        clause, params = bangkok_day_range("s.sold_at", date(2026, 8, 1), None)
        self.assertIn("s.sold_at >=", clause)
        self.assertNotIn("<", clause)
        self.assertEqual(params, [date(2026, 8, 1)])

    def test_unbounded_adds_nothing(self):
        self.assertEqual(bangkok_day_range("sold_at", None, None), ("", []))


if __name__ == "__main__":
    unittest.main()

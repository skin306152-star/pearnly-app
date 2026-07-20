# -*- coding: utf-8 -*-
"""编辑历史记录时的公历闸守门。

抽屉日期框收公历(库里 DATE 列是公历),但全站默认显示佛历、字段标签没标纪年。
会计按泰国习惯填 2569-05-31 时,strptime 会照单全收落库,再推 Express 时
(2569+543)%100 送出 120531 —— 比 OCR 读错还离谱。此闸把它退回让人改。
"""

from __future__ import annotations

import unittest

from routes.history_routes import _find_buddhist_date


def _pages(date_value):
    return [{"fields": {"date": date_value, "invoice_number": "IV69/00475"}}]


class FindBuddhistDateTests(unittest.TestCase):
    def test_flags_buddhist_year(self):
        self.assertEqual(_find_buddhist_date(_pages("2569-05-31")), "2569-05-31")

    def test_allows_gregorian_year(self):
        self.assertIsNone(_find_buddhist_date(_pages("2026-05-31")))

    def test_allows_missing_or_blank_date(self):
        self.assertIsNone(_find_buddhist_date(_pages(None)))
        self.assertIsNone(_find_buddhist_date(_pages("")))
        self.assertIsNone(_find_buddhist_date([{"fields": {}}]))
        self.assertIsNone(_find_buddhist_date([]))
        self.assertIsNone(_find_buddhist_date(None))

    def test_scans_every_page(self):
        pages = [
            {"fields": {"date": "2026-05-31"}},
            {"fields": {"date": "2569-05-31"}},
        ]
        self.assertEqual(_find_buddhist_date(pages), "2569-05-31")

    def test_tolerates_malformed_page_entries(self):
        self.assertIsNone(_find_buddhist_date(["not-a-dict", None]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

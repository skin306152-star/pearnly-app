"""B · 泰式收据 2 位年(DD/MM/YY)日期消歧。

模型对 2 位年常猜错(真实样本:24/08/25 → 2023,Paypers 读对 2025)。后处理只在
date_raw 是 2 位年时介入,且只重算「年」(保留模型的月/日),取公历 20YY 与 2 位佛历
25YY−543 里最接近今天且不超未来的那个。4 位年/非日期不干预。
"""

import unittest

from services.ocr.schemas_invoice import ThaiInvoice, _fix_two_digit_year_date as fx


class TwoDigitYearTests(unittest.TestCase):
    def test_reported_bug_25_to_2025(self):
        self.assertEqual(fx("24/08/25", "2023-08-24", 2025), "2025-08-24")

    def test_model_already_correct_stays(self):
        self.assertEqual(fx("24/08/25", "2025-08-24", 2025), "2025-08-24")

    def test_two_digit_buddhist_68_to_2025(self):
        # 2 位佛历 68 → 2568 BE → 2025 CE(公历 2068 超未来被排除)。
        self.assertEqual(fx("24/08/68", "2068-08-24", 2025), "2025-08-24")

    def test_four_digit_year_untouched(self):
        self.assertEqual(fx("24/08/2025", "2025-08-24", 2025), "2025-08-24")

    def test_preserves_model_month_day(self):
        self.assertEqual(fx("05/03/24", "2024-03-05", 2025), "2024-03-05")

    def test_dash_and_dot_separators(self):
        self.assertEqual(fx("24-08-25", "2023-08-24", 2025), "2025-08-24")
        self.assertEqual(fx("24.08.25", "2023-08-24", 2025), "2025-08-24")

    def test_non_date_raw_untouched(self):
        self.assertEqual(fx("", "2025-08-24", 2025), "2025-08-24")
        self.assertEqual(fx("invoice no 25", "2025-08-24", 2025), "2025-08-24")

    def test_none_model_date_stays_none(self):
        self.assertIsNone(fx("24/08/25", None, 2025))

    def test_no_plausible_candidate_returns_model(self):
        # 公历 2099 与佛历 25_99-543=2056 都超 (今年+1) → 不动,交还模型。
        self.assertEqual(fx("24/08/99", "2099-08-24", 2025), "2099-08-24")

    def test_validator_applies_on_parse(self):
        inv = ThaiInvoice(date_raw="24/08/25", date="2023-08-24")
        self.assertTrue(inv.date.endswith("-08-24"))
        # 年应被纠到 [今年-? , 今年+1] 内,绝不是 2023。
        self.assertNotEqual(inv.date[:4], "2023")


if __name__ == "__main__":
    unittest.main()

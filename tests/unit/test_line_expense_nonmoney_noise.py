# -*- coding: utf-8 -*-

import unittest

from services.expense import amount_extract
from tests.unit.test_line_expense_thai_nonassertive import _run


class NonMoneyNoiseTests(unittest.TestCase):
    def test_repeated_thai_age_marker_is_not_amount(self):
        self.assertIsNone(amount_extract.extract_amount("อาายุ 25 ปี", None, None))
        out, calls = _run("อาายุ 25 ปี")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])

    def test_repeated_thai_minute_marker_is_not_amount(self):
        self.assertIsNone(amount_extract.extract_amount("รอ 15 นาาที", None, None))
        out, calls = _run("รอ 15 นาาที")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])


if __name__ == "__main__":
    unittest.main()

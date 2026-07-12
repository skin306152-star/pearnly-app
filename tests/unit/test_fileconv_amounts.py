# -*- coding: utf-8 -*-
"""fileconv 金额解析 · 泰式千分位/括号负数/泰数字边框/pdfplumber 数字内空格退化。"""

import unittest
from decimal import Decimal

from services.fileconv.amounts import (
    money_tokens,
    parse_amount,
    repair_number_spaces,
    trailing_money_block,
)


class ParseAmountTests(unittest.TestCase):
    def test_thousands_separator(self):
        self.assertEqual(parse_amount("1,900.00"), Decimal("1900.00"))

    def test_parenthesis_negative(self):
        self.assertEqual(parse_amount("(127,748.49)"), Decimal("-127748.49"))

    def test_leading_minus(self):
        self.assertEqual(parse_amount("-127,748.49"), Decimal("-127748.49"))

    def test_thai_digit_token_converts(self):
        # 已隔离的 token 允许泰数字(边框问题只在整行归一时发生)。
        self.assertEqual(parse_amount("๑,๙๐๐.๐๐"), Decimal("1900.00"))

    def test_garbage_and_empty_return_none(self):
        self.assertIsNone(parse_amount(None))
        self.assertIsNone(parse_amount(""))
        self.assertIsNone(parse_amount("abc"))


class RepairNumberSpacesTests(unittest.TestCase):
    def test_split_integer_digit_merges(self):
        self.assertEqual(repair_number_spaces("10003 4 3.25"), "10003 43.25")

    def test_space_before_comma_merges(self):
        self.assertEqual(repair_number_spaces("1 ,727.46"), "1,727.46")

    def test_three_digit_integer_not_merged(self):
        # '5 100.00' 不是被拆的数字(100 是三位整数),保持原样。
        self.assertEqual(repair_number_spaces("code 5 100.00"), "code 5 100.00")


class MoneyTokensTests(unittest.TestCase):
    def test_thai_numeral_border_not_treated_as_digit(self):
        # ๓ 是 Thai-3 边框,不能被当数字并进 57.00。
        line = repair_number_spaces("๓ คาบริการ ๓ 3.00 ๓ 1,900.00 ๓ 57.00 ๓")
        self.assertEqual(
            money_tokens(line),
            [Decimal("3.00"), Decimal("1900.00"), Decimal("57.00")],
        )

    def test_excludes_tax_id_and_date(self):
        # 税号(13 位无小数)和日期(带斜杠)不是金额。
        line = "3250800171163 07/03/68 คาบริการ 57.00"
        self.assertEqual(money_tokens(line), [Decimal("57.00")])


class TrailingBlockTests(unittest.TestCase):
    def test_contiguous_trailing_three(self):
        line = "01/01/2026 JV001 desc 50.00 0.00 -50.00"
        self.assertEqual(
            trailing_money_block(line),
            [Decimal("50.00"), Decimal("0.00"), Decimal("-50.00")],
        )


if __name__ == "__main__":
    unittest.main()

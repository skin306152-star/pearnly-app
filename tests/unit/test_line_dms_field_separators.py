# -*- coding: utf-8 -*-
"""LINE 一行资料的共用分隔符规则(text_fields)+ 两个解析入口的接线。

用户不会只用 |:全/半角竖线、英文/中文逗号、顿号、全/半角斜杠、居中点、留白点号都可能出现。
规则必须一次只用一种、切完精确等于期望段数,且绝不把账号里的 /、日期 19/09/2569、
时间 14:36、金额 1,000.00 猜着拆开。
"""

import unittest

from services.line_dms.booking_payments import parse_payment_detail
from services.line_dms.text_fields import split_fields


class SplitFieldsTests(unittest.TestCase):
    def test_every_supported_separator_class_yields_the_expected_segments(self):
        for text in (
            "Customer | 123456789 | Bangkok | 14:36",
            "Customer ｜ 123456789 ｜ Bangkok ｜ 14:36",
            "Customer, 123456789, Bangkok, 14:36",
            "Customer，123456789，Bangkok，14:36",
            "Customer、123456789、Bangkok、14:36",
            "Customer/123456789/Bangkok/14:36",
            "Customer／123456789／Bangkok／14:36",
            "Customer · 123456789 · Bangkok · 14:36",
            "Customer . 123456789 . Bangkok . 14:36",
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    split_fields(text, 4),
                    ["Customer", "123456789", "Bangkok", "14:36"],
                )

    def test_only_one_rule_at_a_time_is_applied(self):
        # 竖线在场就先按竖线拆:银行名里的逗号原样保留,不会被下一条规则再切一次。
        self.assertEqual(
            split_fields("KBank Rayong, Main | 1234567890", 2),
            ["KBank Rayong, Main", "1234567890"],
        )
        # 规则优先级固定(逗号先于点号):段数只要刚好,就不再试后面的规则。
        self.assertEqual(split_fields("A . B, C", 2), ["A . B", "C"])

    def test_segment_count_must_match_exactly(self):
        for text, expected in (
            ("Customer | 123456789 | Bangkok", 4),
            ("Customer | 123456789 | Bangkok | 14:36", 3),
            ("Customer 123456789 Bangkok 14:36", 4),
            ("", 4),
            ("   ", 4),
        ):
            with self.subTest(text=text, expected=expected):
                self.assertIsNone(split_fields(text, expected))
        self.assertIsNone(split_fields("A | B", 0))

    def test_empty_segment_is_not_a_field(self):
        self.assertIsNone(split_fields("A |  | C", 3))
        self.assertIsNone(split_fields(", B", 2))

    def test_date_time_and_amount_are_never_guessed_apart(self):
        # 日期:斜杠切出 3 段,期望 2 段 → 不认(而不是把 19 当银行名)。
        self.assertIsNone(split_fields("19/09/2569", 2))
        # 金额:逗号切出 3 段,点号又落在数字之间 → 一条规则都不成立。
        self.assertIsNone(split_fields("1,000.00", 2))
        self.assertIsNone(split_fields("1,000.00", 3))
        # 千位逗号紧夹在数字中间,不是一个分隔符。
        self.assertIsNone(split_fields("1,000", 2))
        # 账号里的斜杠同理(数字/数字紧邻)。
        self.assertIsNone(split_fields("123/456", 2))
        # 时间:冒号不是分隔符。
        self.assertIsNone(split_fields("14:36", 2))
        # 缩写:点号后跟空格(Mr. Somchai)不当分隔符。
        self.assertIsNone(split_fields("Mr. Somchai", 2))
        # 但「点号两边留白」是用户明确的分隔写法,照收。
        self.assertEqual(split_fields("KBank . VISA", 2), ["KBank", "VISA"])


class ParsePaymentDetailSeparatorTests(unittest.TestCase):
    """渠道资料(cheque/cashier/card/transfer)共用同一套分隔规则。"""

    def test_cheque_reference_accepts_common_separators(self):
        for text in ("123456 | 01", "123456, 01", "123456／01", "123456 · 01"):
            with self.subTest(text=text):
                self.assertEqual(
                    parse_payment_detail("cheque", text),
                    {"cheque_no": "123456", "cheque_book_no": "01"},
                )

    def test_cashier_and_card_channels(self):
        self.assertEqual(
            parse_payment_detail("cashier_cheque", "777, 09"),
            {"cashier_no": "777", "cashier_book_no": "09"},
        )
        self.assertEqual(
            parse_payment_detail("card", "KBank、VISA", manual_bank=True),
            {"bank_name": "KBank", "card_type": "VISA"},
        )

    def test_manual_cheque_keeps_bank_name_in_the_last_segment(self):
        for text in ("123456 | 01 | KBank", "123456, 01, KBank", "123456 · 01 · KBank"):
            with self.subTest(text=text):
                self.assertEqual(
                    parse_payment_detail("cheque", text, manual_bank=True),
                    {"cheque_no": "123456", "cheque_book_no": "01", "bank_name": "KBank"},
                )
        self.assertIsNone(parse_payment_detail("cheque", "123456 | 01", manual_bank=True))

    def test_transfer_bank_and_account_are_no_longer_collected(self):
        for text in ("SCB 123/456", "KBank Rayong | 1234567890", "Customer | 999 | Bangkok"):
            self.assertIsNone(parse_payment_detail("transfer", text))

    def test_amount_and_abbreviation_are_not_split_into_two_fields(self):
        self.assertIsNone(parse_payment_detail("cheque", "1,000.00"))
        # 「数字.数字」一律当小数/编号看,不当分隔符(与「能严格得到期望段数」相比,保护优先)。
        self.assertIsNone(parse_payment_detail("cheque", "123456.01"))
        self.assertIsNone(parse_payment_detail("card", "Mr. Somchai", manual_bank=True))

    def test_transfer_source_input_is_not_parsed(self):
        for text in ("SCB 123/456", "KBank Rayong | 1234567890", "Customer | 999 | Bangkok"):
            self.assertIsNone(parse_payment_detail("transfer", text))


if __name__ == "__main__":
    unittest.main()

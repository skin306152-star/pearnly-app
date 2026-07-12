# -*- coding: utf-8 -*-
"""fileconv 台账余额链守恒 · 命中(闭合)与不命中(点名)两态。合成脱敏数据。"""

import unittest
from decimal import Decimal

from services.fileconv.ledger import extract_ledger
from services.fileconv.validate import validate_ledger, ledger_stats
from services.fileconv.model import ISSUE_GL_BALANCE_CHAIN, ISSUE_RUNNING_BALANCE

# 借贷三栏 GL(期初 -100):-100 +50 = -50;-50 -30 = -80。链闭合。
_GL_3COL = """รายงานสมุดแยกประเภท
วันที่ ใบสำคัญ คำอธิบาย เดบิต เครดิต ยอดคงเหลือ
1113-01 เงินฝาก -100.00
01/01/2569 JV JV001 pay 50.00 0.00 -50.00
02/01/2569 JV JV002 fee 0.00 30.00 -80.00"""

# 单金额 + 跑余额两栏(银行):承前 0;+100 →100;−20 →80。链闭合。
_BANK_2COL = """Date Description Debit Credit
01/01/2026 Balance Forward 0.00
02/01/2026 SV001 income 100.00 100.00
03/01/2026 fee 10003 20.00 80.00"""


def _rows(text):
    return extract_ledger([text])


class LedgerThreeColumnTests(unittest.TestCase):
    def test_chain_closes(self):
        rows, opening = _rows(_GL_3COL)
        self.assertEqual(len(rows), 2)
        self.assertEqual(opening["1113-01"], Decimal("-100.00"))
        self.assertEqual(validate_ledger(rows, opening), [])

    def test_buddhist_year_normalized(self):
        rows, _ = _rows(_GL_3COL)
        self.assertEqual(rows[0].date, "01/01/2569")
        self.assertEqual(rows[0].date_ce, "2026-01-01")

    def test_broken_balance_flagged(self):
        broken = _GL_3COL.replace("-80.00", "-79.00")
        rows, opening = _rows(broken)
        issues = validate_ledger(rows, opening)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].kind, ISSUE_GL_BALANCE_CHAIN)
        self.assertEqual(issues[0].expected, "-80.00")
        self.assertEqual(issues[0].actual, "-79.00")

    def test_stats_sums(self):
        rows, opening = _rows(_GL_3COL)
        stats = ledger_stats(rows, opening)
        self.assertEqual(stats["opening_balance"], "-100.00")
        self.assertEqual(stats["closing_balance"], "-80.00")
        self.assertEqual(stats["sum_debit"], "50.00")
        self.assertEqual(stats["sum_credit"], "30.00")


class LedgerTwoColumnTests(unittest.TestCase):
    def test_running_chain_closes(self):
        rows, opening = _rows(_BANK_2COL)
        self.assertEqual(len(rows), 2)
        self.assertEqual(opening[""], Decimal("0.00"))
        self.assertEqual(validate_ledger(rows, opening), [])

    def test_broken_running_flagged(self):
        broken = _BANK_2COL.replace("20.00 80.00", "20.00 85.00")
        rows, opening = _rows(broken)
        issues = validate_ledger(rows, opening)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].kind, ISSUE_RUNNING_BALANCE)
        self.assertEqual(issues[0].expected, "20.00")  # 账面金额
        self.assertEqual(issues[0].actual, "15.00")  # 余额实际变动


class LedgerMultiAccountTests(unittest.TestCase):
    def test_two_accounts_each_chain_from_own_opening(self):
        text = """รายงานสมุดแยกประเภท
1101-00 acct A 0.00
01/01/2026 JV A1 x 10.00 0.00 10.00
2101-00 acct B -5.00
02/01/2026 JV B1 y 0.00 3.00 -8.00"""
        rows, opening = _rows(text)
        self.assertEqual(opening["1101-00"], Decimal("0.00"))
        self.assertEqual(opening["2101-00"], Decimal("-5.00"))
        self.assertEqual(validate_ledger(rows, opening), [])


if __name__ == "__main__":
    unittest.main()

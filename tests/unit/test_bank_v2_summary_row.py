# -*- coding: utf-8 -*-
"""
v118.35.0.60 · 守门测试 · 汇总/合计行识别(_is_summary_row)

真实案例(skin 实测 AM 1-69):底部 "จำนวนเงินฝาก/Total Credit"、"Total Deposit"
汇总行被当成交易行 · 余额对不上被误标 ⚠。这些不是交易 · 应跳过。

锁定契约:识别常见汇总行(Total/รวมรายการ/合计 等)· 不误伤普通交易描述。
"""
import unittest
from bank_recon_v2 import _is_summary_row


class SummaryRowTests(unittest.TestCase):

    def test_summary_rows_detected(self):
        for d in [
            "Total Credit", "Total Deposit", "จำนวนเงินฝาก/Total Credit",
            "Total Withdrawal Transactions", "รวมรายการถอนเงิน", "ยอดรวม",
            "Grand Total", "合计", "总计", "本期合计",
        ]:
            self.assertTrue(_is_summary_row(d), f"应识别为汇总行: {d}")

    def test_normal_transactions_not_flagged(self):
        for d in [
            "รับโอนเงิน", "โอนเงิน", "ฝากเงินสด", "CASH DEPOSIT",
            "PMT APPROVE ONL", "TR fr 9842998258", "SWD", "XDN",
            "AMOUNT TRANFERED FROM/TO C/A", "Interest Charge", "",
        ]:
            self.assertFalse(_is_summary_row(d), f"普通交易不应被当汇总行: {d}")


if __name__ == "__main__":
    unittest.main()

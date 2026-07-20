# -*- coding: utf-8 -*-
"""fileconv 表格合计闭合守恒 · 命中与不命中。右对齐容忍明细多出的前置列。"""

import unittest
from decimal import Decimal

from services.fileconv.tables import extract_tabular, from_grid, reconcile_totals
from services.fileconv.validate import validate_tabular
from services.fileconv.model import ISSUE_FOOTER_TOTAL

# 销项税报表:两行明细,合计闭合(1000+2000=3000,70+140=210)。
_VAT_OK = """รายงานภาษีขาย
01/03/2026 INV001 buyer1 1000.00 70.00
02/03/2026 INV002 buyer2 2000.00 140.00
รวมทั้งสิ้น 3000.00 210.00"""


class FooterTotalTests(unittest.TestCase):
    def test_totals_reconcile(self):
        self.assertEqual(validate_tabular(extract_tabular([_VAT_OK])), [])

    def test_total_mismatch_flagged(self):
        broken = _VAT_OK.replace("3000.00 210.00", "3000.00 200.00")
        issues = validate_tabular(extract_tabular([broken]))
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].kind, ISSUE_FOOTER_TOTAL)
        self.assertEqual(issues[0].expected, "210.00")
        self.assertEqual(issues[0].actual, "200.00")

    def test_right_alignment_ignores_extra_left_column(self):
        # 明细多一个税率列(3.00),合计只两列;右对齐后仍闭合。
        text = """detail table
01 payee 3.00 1000.00 30.00
รวม 1000.00 30.00"""
        self.assertEqual(validate_tabular(extract_tabular([text])), [])

    def test_no_total_row_no_false_issue(self):
        text = """01/03/2026 INV001 1000.00 70.00
02/03/2026 INV002 2000.00 140.00"""
        self.assertEqual(reconcile_totals(extract_tabular([text])), [])


class ColumnIndexedTotalsTests(unittest.TestCase):
    """列位已知时按列下标配对 —— 右对齐配对在缺列行上会报出不存在的差额。"""

    GRID = [
        ["Date", "Qty", "Price", "Subtotal", "VAT", "Total"],
        ["1", "19,220.00", "6.07", "116,665.40", "8,166.58", "124,831.98"],
        ["2", "20,200.00", "6.07", "122,614.00", "8,582.98", "131,196.98"],
        ["31", "", "6.07", "-", "-", "-"],
        ["Total", "", "", "239,279.40", "16,749.56", "256,028.96"],
    ]

    def test_no_sales_day_does_not_fabricate_a_gap(self):
        """无销售日那行只有单价 6.07;按列配对时它落在单价列,不冒充含税总额。"""
        self.assertEqual(validate_tabular(from_grid(self.GRID)), [])

    def test_right_align_pairing_would_have_flagged_it(self):
        """对照组:同一份料走纯文字右对齐路,6.07 被当成含税总额 → 假差额。
        这条锁的是「为什么必须改配对方式」,它变绿反而说明对照失效。"""
        text = "\n".join(" ".join(c for c in row if c) for row in self.GRID)
        issues = validate_tabular(extract_tabular([text]))
        self.assertTrue(issues, "右对齐配对本应在此报出假差额")

    def test_real_mismatch_still_caught_by_column(self):
        broken = [list(r) for r in self.GRID]
        broken[-1][4] = "99,999.00"
        issues = validate_tabular(from_grid(broken))
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].expected, "16749.56")
        self.assertEqual(issues[0].actual, "99999.00")
        self.assertIn("第 5", issues[0].message)

    def test_blank_and_dash_are_missing_not_zero(self):
        lines = from_grid(self.GRID)
        self.assertNotIn(1, lines[3].col_money)  # 空格
        self.assertNotIn(3, lines[3].col_money)  # 破折号
        self.assertEqual(lines[3].col_money[2], Decimal("6.07"))

    def test_column_unreported_by_total_row_is_not_checked(self):
        """合计行没报数量列 → 不拿 0 当合计去比对(否则整列必假红)。"""
        self.assertEqual(validate_tabular(from_grid(self.GRID)), [])


class ThaiBorderSplitTests(unittest.TestCase):
    def test_border_delimited_row_extracts_true_amounts(self):
        # Express ๓ 边框行:金额应为 3.00 / 1,900.00 / 57.00,不被边框污染。
        line = "๓ 1 ๓payee 325 ๓07/03/68๓ service ๓ 3.00 ๓ 1,900.00 ๓ 57.00 ๓ ๓"
        lines = extract_tabular([line])
        self.assertEqual(len(lines), 1)
        self.assertEqual([str(m) for m in lines[0].money], ["3.00", "1900.00", "57.00"])


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""fileconv 表格合计闭合守恒 · 命中与不命中。右对齐容忍明细多出的前置列。"""

import unittest

from services.fileconv.tables import extract_tabular, reconcile_totals
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


class ThaiBorderSplitTests(unittest.TestCase):
    def test_border_delimited_row_extracts_true_amounts(self):
        # Express ๓ 边框行:金额应为 3.00 / 1,900.00 / 57.00,不被边框污染。
        line = "๓ 1 ๓payee 325 ๓07/03/68๓ service ๓ 3.00 ๓ 1,900.00 ๓ 57.00 ๓ ๓"
        lines = extract_tabular([line])
        self.assertEqual(len(lines), 1)
        self.assertEqual([str(m) for m in lines[0].money], ["3.00", "1900.00", "57.00"])


if __name__ == "__main__":
    unittest.main()

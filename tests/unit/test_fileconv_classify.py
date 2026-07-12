# -*- coding: utf-8 -*-
"""fileconv doc_type 识别 · 识别不了诚实落 generic。"""

import unittest

from services.fileconv.classify import classify
from services.fileconv.model import (
    GL_LEDGER,
    BANK_STATEMENT,
    VAT_REPORT,
    GENERIC_TABLE,
)


class ClassifyTests(unittest.TestCase):
    def test_gl_ledger_by_title(self):
        self.assertEqual(classify("รายงานสมุดแยกประเภท\n1113-01"), GL_LEDGER)

    def test_gl_ledger_by_columns(self):
        self.assertEqual(classify("วันที่ เดบิต เครดิต ยอดคงเหลือ"), GL_LEDGER)

    def test_bank_statement_by_balance_forward(self):
        self.assertEqual(
            classify("Date Description Debit Credit\nBalance Forward 0"), BANK_STATEMENT
        )

    def test_vat_report_by_marker(self):
        self.assertEqual(classify("รายงานภาษีขาย ประจำเดือน"), VAT_REPORT)

    def test_unknown_falls_to_generic(self):
        self.assertEqual(classify("some random invoice text 123.45"), GENERIC_TABLE)


if __name__ == "__main__":
    unittest.main()

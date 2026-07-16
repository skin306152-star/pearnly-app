# -*- coding: utf-8 -*-
"""Express GL 适配器单测(services/accounting/express_gl_adapter.py · T4b)。

守恒金标:合成冰厂式 GLJNLIT(TRNTYP 0=借 1=贷,AMOUNT 恒正)经 adapter → GlRow →
Σ借=Σ贷 差 0.00。另覆盖:方向定向、佛历日期解析、utf-8-sig BOM 解码、行级诚实丢弃、
parse_gl_bytes 分流(Express csv 走本适配器,xlsx/非 Express csv 原路不改)。
"""

import unittest
from decimal import Decimal

from services.accounting import express_gl_adapter as adapter
from services.accounting import gl_upload_adapter

# 合成冰厂式 GLJNLIT · 两张凭证各自借贷平(Σ借=Σ贷=2070.50)
_GLJNLIT_CSV = (
    "VOUCHER,TRNDATE,ACCNUM,TRNTYP,AMOUNT,REMARK\r\n"
    "JV001,25620501,11-01-01-01,0,1000.50,รับเงินสด\r\n"
    "JV001,25620501,41-01-01-01,1,934.58,ขายสินค้า\r\n"
    "JV001,25620501,21-05-04-02,1,65.92,ภาษีขาย\r\n"
    "JV002,25620502,11-05-04-01,0,70.00,ภาษีซื้อ\r\n"
    "JV002,25620502,51-01-01-01,0,1000.00,ต้นทุน\r\n"
    "JV002,25620502,11-01-02-01,1,1070.00,จ่ายผ่านธนาคาร\r\n"
).encode("utf-8-sig")


def _dec_sum(rows, field):
    return sum((Decimal(str(getattr(r, field))) for r in rows), Decimal("0"))


class ConservationGoldenTests(unittest.TestCase):
    def test_debit_equals_credit_zero_diff(self):
        rows, issues = adapter.parse_express_gl_csv(_GLJNLIT_CSV, "gljnlit.csv")
        self.assertEqual(issues, [])
        self.assertEqual(len(rows), 6)
        d, c = _dec_sum(rows, "debit"), _dec_sum(rows, "credit")
        self.assertEqual(d, Decimal("2070.50"))
        self.assertEqual(c, Decimal("2070.50"))
        self.assertEqual((d - c).copy_abs(), Decimal("0.00"))


class DirectionAndParseTests(unittest.TestCase):
    def test_trntyp_defines_direction(self):
        rows, _ = adapter.parse_express_gl_csv(_GLJNLIT_CSV, "gl.csv")
        cash = rows[0]  # TRNTYP 0 → 借
        self.assertEqual((cash.debit, cash.credit), (1000.50, 0.0))
        self.assertEqual(cash.account_code, "11-01-01-01")
        self.assertEqual(cash.doc_no, "JV001")
        sales = rows[1]  # TRNTYP 1 → 贷
        self.assertEqual((sales.debit, sales.credit), (0.0, 934.58))

    def test_buddhist_date_parsed(self):
        rows, _ = adapter.parse_express_gl_csv(_GLJNLIT_CSV, "gl.csv")
        self.assertEqual(rows[0].date.isoformat(), "2019-05-01")  # 2562 - 543

    def test_bad_trntyp_dropped_honestly(self):
        bad = (
            "VOUCHER,ACCNUM,TRNTYP,AMOUNT\r\n"
            "JV009,11-01-01-01,2,10.00\r\n"  # TRNTYP 非 0/1
            "JV009,,0,10.00\r\n"  # 无科目码
        ).encode("utf-8-sig")
        rows, issues = adapter.parse_express_gl_csv(bad, "gl.csv")
        self.assertEqual(rows, [])
        self.assertEqual(len(issues), 2)
        self.assertTrue(any("TRNTYP" in i for i in issues))
        self.assertTrue(any("ACCNUM" in i for i in issues))


class DetectionAndRoutingTests(unittest.TestCase):
    def test_is_express_gl_true_for_gljnlit_header(self):
        self.assertTrue(adapter.is_express_gl(_GLJNLIT_CSV, "gljnlit.csv"))

    def test_is_express_gl_false_for_bank_csv(self):
        bank = "Date,Description,Debit,Credit,Balance\r\n01/05/2569,x,10,0,10\r\n".encode(
            "utf-8-sig"
        )
        self.assertFalse(adapter.is_express_gl(bank, "bank_gl.csv"))

    def test_is_express_gl_false_for_xlsx_ext(self):
        self.assertFalse(adapter.is_express_gl(_GLJNLIT_CSV, "book.xlsx"))

    def test_parse_gl_bytes_routes_express_csv(self):
        out = gl_upload_adapter.parse_gl_bytes(_GLJNLIT_CSV, "gljnlit.csv")
        self.assertEqual(len(out["rows"]), 6)
        self.assertEqual(out["rows"][0].account_code, "11-01-01-01")
        self.assertEqual(out["rows"][0].source_file, "gljnlit.csv")


if __name__ == "__main__":
    unittest.main()

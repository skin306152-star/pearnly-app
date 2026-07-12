# -*- coding: utf-8 -*-
"""官方 FORMAT กลาง ภ.ง.ด.1(FormatPND1V2_0)中央格式契约(合成数据)。

字段序/数量逐字段落官方 PDF:HEADER 22 / DETAIL 26;金额 N(15,2) 补 .00;收入码 40(1)→1;
地址无源留空。禁臆造 40(2) 子类型(未知码抛错)。
"""

import datetime as dt
import unittest
from decimal import Decimal

from services.payroll import model
from services.tax import rdprep_pnd1
from services.tax.rdprep import RdPrepFormatError


def _valid_id(prefix12: str) -> str:
    total = sum(int(prefix12[i]) * (13 - i) for i in range(12))
    return prefix12 + str((11 - total % 11) % 10)


_ID = _valid_id("365010069742")


def _row(amount="13000", wht="0", income="40(1)"):
    return model.PayrollRow(
        seq=1,
        employee_id=_ID,
        title="นางสาว",
        first_name="รุ่งนภา",
        last_name="ชุนประวัติ",
        paid_amount=Decimal(amount),
        wht_amount=Decimal(wht),
        paid_date=dt.date(2026, 5, 31),
        income_code=income,
        condition="1",
    )


class CentralFormatTests(unittest.TestCase):
    def test_field_counts_match_official_spec(self):
        self.assertEqual(rdprep_pnd1.HEADER_FIELD_COUNT, 22)
        self.assertEqual(rdprep_pnd1.DETAIL_FIELD_COUNT, 26)

    def test_income_code_maps_to_official_numeric(self):
        self.assertEqual(rdprep_pnd1.income_code_to_official("40(1)"), "1")
        self.assertEqual(rdprep_pnd1.income_code_to_official("1"), "1")

    def test_unknown_income_code_raises_not_guessed(self):
        with self.assertRaises(RdPrepFormatError):
            rdprep_pnd1.income_code_to_official("40(2)")

    def test_detail_has_26_fields_and_two_decimal_amounts(self):
        cells = rdprep_pnd1.build_detail(_row(), branch_no="000000").split("|")
        self.assertEqual(len(cells), 26)
        self.assertEqual(cells[0], "D")
        self.assertEqual(cells[3], _ID)  # PIN
        self.assertEqual(cells[10], "13000.00")  # PAID_AMT N(15,2)
        self.assertEqual(cells[11], "0.00")  # TAX_AMT
        self.assertEqual(cells[12], "1")  # INC_TYPE_PND 40(1)→1
        self.assertEqual(cells[13], "1")  # PAY_CON

    def test_address_fields_empty_when_no_source(self):
        cells = rdprep_pnd1.build_detail(_row(), branch_no="000000").split("|")
        self.assertEqual(cells[23], "")  # AMPHUR 无数据源留空(诚实降级)
        self.assertEqual(cells[24], "")  # PROVINCE
        self.assertEqual(cells[25], "")  # POSTAL_CODE

    def test_header_has_22_fields_and_computed_totals(self):
        text = rdprep_pnd1.build_file(
            {
                "SENDER_NID": _ID,
                "NID": _ID,
                "SENDER_ROLE": "1",
                "BRANCH_NO": "000000",
                "LTO": "0",
                "TAX_MONTH": "05",
                "TAX_YEAR": "2569",
                "FORM_TYPE": "00",
                "USER_ID": "",
                "FORM_FLAG": "2",
            },
            [_row("13000"), _row("12040")],
            branch_no="000000",
        )
        header = text.split("\r\n")[0].split("|")
        self.assertEqual(len(header), 22)
        self.assertEqual(header[0], "H")
        self.assertEqual(header[14], "2")  # TOT_NUM
        self.assertEqual(header[15], "25040.00")  # TOT_AMT = 13000+12040

    def test_effective_rate_zero_when_no_wht(self):
        self.assertEqual(
            rdprep_pnd1.effective_rate(Decimal("12000"), Decimal("0")), Decimal("0.00")
        )

    def test_filename_official_naming(self):
        name = rdprep_pnd1.build_filename(
            nid=_ID, branch_no="000000", tax_year_be="2569", tax_month="05"
        )
        self.assertEqual(name, f"PND1_{_ID}_000000_2569_05_00_00.txt")


if __name__ == "__main__":
    unittest.main()

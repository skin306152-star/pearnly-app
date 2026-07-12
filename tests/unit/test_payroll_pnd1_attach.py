# -*- coding: utf-8 -*-
"""ใบแนบ ภ.ง.ด.1 扁平上传串(金标末列格式 · 合成数据逐字节)。

金标第 1 员工末列 = `40(1)|1|<id>|นางสาว|รุ่งนภา|ชุนประวัติ|31052569|13000|0|1`;真料本地跑
byte-exact(见汇报),此处用合成 id 复现同装配契约:整数金额、CR/LF、禁用字符拦截。
"""

import datetime as dt
import unittest
from decimal import Decimal

from services.payroll import model
from services.tax import pnd1_attach
from services.tax.rdprep import RdPrepFormatError


def _valid_id(prefix12: str) -> str:
    total = sum(int(prefix12[i]) * (13 - i) for i in range(12))
    return prefix12 + str((11 - total % 11) % 10)


_ID = _valid_id("365010069742")


def _row(seq=1, amount="13000", wht="0", first="รุ่งนภา", last="ชุนประวัติ"):
    return model.PayrollRow(
        seq=seq,
        employee_id=_ID,
        title="นางสาว",
        first_name=first,
        last_name=last,
        paid_amount=Decimal(amount),
        wht_amount=Decimal(wht),
        paid_date=dt.date(2026, 5, 31),
        income_code="40(1)",
        condition="1",
    )


class PipeAttachTests(unittest.TestCase):
    def test_pipe_line_matches_golden_format(self):
        expected = f"40(1)|1|{_ID}|นางสาว|รุ่งนภา|ชุนประวัติ|31052569|13000|0|1"
        self.assertEqual(pnd1_attach.build_line(_row()), expected)

    def test_amount_is_integer_not_two_decimals(self):
        line = pnd1_attach.build_line(_row(amount="12040", wht="0"))
        cells = line.split("|")
        self.assertEqual(cells[7], "12040")  # 非 "12040.00"
        self.assertEqual(cells[8], "0")  # 非 "0.00"

    def test_satang_amount_keeps_two_decimals(self):
        # U1:含 satang 无金标样本 → 保留两位诚实输出,不静默丢分。
        self.assertEqual(pnd1_attach.build_line(_row(amount="1234.56")).split("|")[7], "1234.56")

    def test_forbidden_char_in_name_rejected(self):
        with self.assertRaises(RdPrepFormatError):
            pnd1_attach.build_line(_row(first="ชื่อ|แทรก"))

    def test_missing_paid_date_rejected(self):
        row = _row()
        row.paid_date = None
        with self.assertRaises(RdPrepFormatError):
            pnd1_attach.build_line(row)

    def test_attachment_joins_with_crlf_no_trailing(self):
        text = pnd1_attach.build_attachment([_row(1), _row(2)])
        self.assertEqual(len(text.split("\r\n")), 2)
        self.assertFalse(text.endswith("\r\n"))


if __name__ == "__main__":
    unittest.main()

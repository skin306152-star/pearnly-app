# -*- coding: utf-8 -*-
"""进料兼容层:列自动猜测 + 单元格归一 + 员工/合计行切分(批次 H · 合成数据)。

金标真料(7 员工 / Σ78270 / 真身份证)只本地跑,禁入 git —— 此处用合成的、通过 mod-11 的
假身份证复现金标「列布局」,验列猜中 + 佛历日期解析 + 合计行分离。
"""

import datetime as dt
import unittest
from decimal import Decimal

from services.payroll import guess, intake, model


def _valid_id(prefix12: str) -> str:
    """合成一个通过泰国 mod-11 校验位的 13 位号(权重 13..2,校验位=(11-Σ%11)%10)。"""
    total = sum(int(prefix12[i]) * (13 - i) for i in range(12))
    return prefix12 + str((11 - total % 11) % 10)


# 合成金标布局:列序照金标(收入码/序号/付款方/员工证/称谓/名/姓/支付日/金额/扣税/条件)。
_PAYER = _valid_id("010554808241")
_EMP = [_valid_id(p) for p in ("365010069742", "110420000252", "110080066735")]
_HEADER = [
    "รหัสเงินได้",
    "ลำดับที่",
    "ผู้หัก 13 หลัก",
    "เลข 13 หลัก",
    "คำนำหน้า",
    "ชื่อ",
    "นามสกุล",
    "วันที่จ่าย",
    "จำนวนเงิน",
    "ภาษีหัก",
    "เงื่อนไข",
]
_ROWS = [
    ["40(1)", 1, _PAYER, _EMP[0], "นางสาว", "สมหญิง", "ใจดี", 31052569, 13000, 0, 1],
    ["40(1)", 2, _PAYER, _EMP[1], "นาย", "สมชาย", "รักงาน", 31052569, 12040, 0, 1],
    ["40(1)", 3, _PAYER, _EMP[2], "นางสาว", "มานี", "มีสุข", 31052569, 14500, 0, 1],
    [None, None, None, None, None, None, None, None, 39540, None, None],  # 合计行(仅金额)
]


class GuessColumnsTests(unittest.TestCase):
    def setUp(self):
        self.cand = guess.guess_columns(_HEADER, _ROWS)

    def test_guess_columns_golden_layout(self):
        self.assertEqual(self.cand[model.F_EMPLOYEE_ID].column, 3)
        self.assertEqual(self.cand[model.F_EMPLOYEE_ID].confidence, guess.CONF_HIGH)
        self.assertEqual(self.cand[model.F_PAID_AMOUNT].column, 8)
        self.assertEqual(self.cand[model.F_TITLE].column, 4)
        self.assertEqual(self.cand[model.F_INCOME_CODE].column, 0)

    def test_employee_id_not_confused_with_constant_payer(self):
        # 付款方列(全表同值)与员工列(逐行不同)都是 mod-11 合法号:员工=去重多者。
        self.assertNotEqual(self.cand[model.F_EMPLOYEE_ID].column, 2)
        self.assertEqual(guess.find_constant_id_column(_HEADER, _ROWS), 2)

    def test_names_after_title(self):
        self.assertEqual(self.cand[model.F_FIRST_NAME].column, 5)
        self.assertEqual(self.cand[model.F_LAST_NAME].column, 6)


class CellCoerceTests(unittest.TestCase):
    def test_coerce_id_int_to_str(self):
        self.assertEqual(intake.coerce_id(int(_EMP[0])), _EMP[0])

    def test_coerce_id_recovers_lost_leading_zero(self):
        # openpyxl 把首位为 0 的 13 位号读成 12 位 int → 补回。
        self.assertEqual(intake.coerce_id(105548082417), "0105548082417")

    def test_parse_compact_buddhist_date(self):
        self.assertEqual(intake.parse_paid_date(31052569), dt.date(2026, 5, 31))
        self.assertEqual(intake.parse_paid_date("31052569"), dt.date(2026, 5, 31))

    def test_parse_separated_and_native_date(self):
        self.assertEqual(intake.parse_paid_date("01/06/2569"), dt.date(2026, 6, 1))
        self.assertEqual(intake.parse_paid_date(dt.date(2026, 5, 31)), dt.date(2026, 5, 31))
        self.assertEqual(
            intake.parse_paid_date(dt.datetime(2026, 5, 31, 9, 0)), dt.date(2026, 5, 31)
        )

    def test_bad_date_returns_none_not_guess(self):
        self.assertIsNone(intake.parse_paid_date("ไม่ทราบ"))
        self.assertIsNone(intake.parse_paid_date(None))

    def test_parse_amount_decimal_and_thousands(self):
        self.assertEqual(intake.parse_amount("13,000"), Decimal("13000"))
        self.assertEqual(intake.parse_amount(13000), Decimal("13000"))
        self.assertIsNone(intake.parse_amount(""))


class PartitionTests(unittest.TestCase):
    def test_partition_splits_total_row(self):
        cand = guess.guess_columns(_HEADER, _ROWS)
        cmap = {f: c.column for f, c in cand.items()}
        rows = intake.build_rows(_HEADER, _ROWS, cmap)
        employees, declared = intake.partition_rows(rows)
        self.assertEqual(len(employees), 3)
        self.assertEqual(declared, Decimal("39540"))
        self.assertEqual(sum(r.paid_amount for r in employees), Decimal("39540"))

    def test_forgot_id_row_kept_as_employee_not_total(self):
        # 有姓名但漏身份证 → 仍算员工(交 V5 点名),不当合计行丢掉。
        rows = intake.rows_from_manual(
            [{model.F_TITLE: "นาย", model.F_FIRST_NAME: "ก", model.F_PAID_AMOUNT: 100}]
        )
        employees, _ = intake.partition_rows(rows)
        self.assertEqual(len(employees), 1)


if __name__ == "__main__":
    unittest.main()

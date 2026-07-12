# -*- coding: utf-8 -*-
"""五校验(V1-V5 · 只验不算 · 合成数据)。金标 Σ78270/扣税0/mod-11 用合成号复现。"""

import datetime as dt
import unittest
from decimal import Decimal

from services.payroll import model, validate


def _valid_id(prefix12: str) -> str:
    total = sum(int(prefix12[i]) * (13 - i) for i in range(12))
    return prefix12 + str((11 - total % 11) % 10)


def _row(
    seq, emp_id, amount, wht=0, paid_date=dt.date(2026, 5, 31), title="นาย", first="ก", last="ข"
):
    return model.PayrollRow(
        seq=seq,
        employee_id=emp_id,
        title=title,
        first_name=first,
        last_name=last,
        paid_amount=Decimal(str(amount)),
        wht_amount=Decimal(str(wht)),
        paid_date=paid_date,
        raw={"paid_amount": amount, "paid_date": paid_date},
    )


_IDS = [_valid_id(p) for p in ("365010069742", "110420000252", "110080066735")]
_GOOD = [_row(1, _IDS[0], 13000), _row(2, _IDS[1], 12040), _row(3, _IDS[2], 14500)]


class ValidateTests(unittest.TestCase):
    def test_all_good_no_issues(self):
        issues = validate.validate_rows(_GOOD, period="2569-05", declared_total=Decimal("39540"))
        self.assertEqual(issues, [])

    def test_mod11_tampered_id_flagged(self):
        bad = list(_IDS[0])
        bad[-1] = str((int(bad[-1]) + 1) % 10)
        rows = [_row(1, "".join(bad), 13000)]
        kinds = [i.kind for i in validate.validate_rows(rows)]
        self.assertIn(model.ISSUE_INVALID_ID, kinds)

    def test_sum_conservation_mismatch_points_delta(self):
        issues = validate.validate_rows(_GOOD, declared_total=Decimal("40000"))
        sums = [i for i in issues if i.kind == model.ISSUE_SUM_MISMATCH]
        self.assertEqual(len(sums), 1)
        self.assertIsNone(sums[0].row_no)  # 整表级
        self.assertIn("39540", sums[0].value)

    def test_sum_conservation_uses_decimal_exact(self):
        rows = [_row(1, _IDS[0], "0.1"), _row(2, _IDS[1], "0.2")]
        self.assertEqual(validate.total_paid(rows), Decimal("0.3"))
        self.assertEqual(validate.validate_rows(rows, declared_total=Decimal("0.3")), [])

    def test_wht_over_amount_flagged(self):
        rows = [_row(1, _IDS[0], 12000, wht=13000)]
        kinds = [i.kind for i in validate.validate_rows(rows)]
        self.assertIn(model.ISSUE_WHT_OUT_OF_RANGE, kinds)

    def test_negative_wht_flagged(self):
        rows = [_row(1, _IDS[0], 12000, wht=-1)]
        kinds = [i.kind for i in validate.validate_rows(rows)]
        self.assertIn(model.ISSUE_WHT_OUT_OF_RANGE, kinds)

    def test_zero_wht_within_range_ok(self):
        rows = [_row(1, _IDS[0], 12000, wht=0)]
        self.assertEqual(
            [i for i in validate.validate_rows(rows) if i.kind == model.ISSUE_WHT_OUT_OF_RANGE], []
        )

    def test_date_out_of_period_flagged(self):
        rows = [_row(1, _IDS[0], 12000, paid_date=dt.date(2026, 6, 30))]
        kinds = [i.kind for i in validate.validate_rows(rows, period="2569-05")]
        self.assertIn(model.ISSUE_DATE_OUT_OF_PERIOD, kinds)

    def test_missing_required_field_flagged(self):
        rows = [_row(1, _IDS[0], 12000, title="")]
        issues = [i for i in validate.validate_rows(rows) if i.kind == model.ISSUE_MISSING_FIELD]
        self.assertEqual([i.field for i in issues], [model.F_TITLE])

    def test_unparseable_amount_flagged_not_silent(self):
        row = model.PayrollRow(
            seq=1,
            employee_id=_IDS[0],
            title="นาย",
            first_name="ก",
            last_name="ข",
            paid_amount=None,
            wht_amount=Decimal("0"),
            paid_date=dt.date(2026, 5, 31),
            raw={"paid_amount": "abc"},
        )
        kinds = [i.kind for i in validate.validate_rows([row])]
        self.assertIn(model.ISSUE_BAD_AMOUNT, kinds)


if __name__ == "__main__":
    unittest.main()

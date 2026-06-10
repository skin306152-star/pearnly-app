# -*- coding: utf-8 -*-
"""税表汇总引擎守门(docs/tax-filing/02):PP30 销−进(超期剔除/缺税号不计/留抵)·
PND53/3 按收款人税号首位分流 · 6 个月边界。"""

import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

from services.tax import aggregate


class FakeCursor:
    def __init__(self, *, ones=None, alls=None):
        self.executed = []
        self._ones = list(ones or [])
        self._alls = list(alls or [])

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return self._alls.pop(0) if self._alls else []


_MAPPINGS = {"output_vat": "acc-out", "input_vat": "acc-in"}


def _pp30(cur):
    with mock.patch.object(aggregate.acct_store, "resolve_mappings", return_value=_MAPPINGS):
        return aggregate.pp30(cur, tenant_id="t", workspace_client_id=1, period="2026-06")


class ClassifyPayeeTests(unittest.TestCase):
    def test_zero_prefix_is_juristic_others_individual_missing_flagged(self):
        self.assertEqual(aggregate.classify_payee("0105536000011"), ("juristic", False))
        self.assertEqual(aggregate.classify_payee("1234567890123"), ("individual", False))
        self.assertEqual(aggregate.classify_payee(None), ("juristic", True))
        self.assertEqual(aggregate.classify_payee("  "), ("juristic", True))


class Pp30Tests(unittest.TestCase):
    def test_net_excludes_expired_and_missing_tax_id_input(self):
        cur = FakeCursor(
            ones=[{"total": "700", "n": 7}, {"total": "300", "n": 3}],
            alls=[
                [
                    # 2025-10 → 8 个月前 > 6 → 超期剔除
                    {
                        "dr_cr": "debit",
                        "amount": "100",
                        "doc_date": date(2025, 10, 15),
                        "supplier_tax_id": "0105536000011",
                    },
                    # 本月票但供应商缺税号 → 不计抵
                    {
                        "dr_cr": "debit",
                        "amount": "50",
                        "doc_date": date(2026, 6, 1),
                        "supplier_tax_id": None,
                    },
                    # 本月票有税号 → 可抵
                    {
                        "dr_cr": "debit",
                        "amount": "150",
                        "doc_date": date(2026, 6, 2),
                        "supplier_tax_id": "0105536000011",
                    },
                ]
            ],
        )
        agg = _pp30(cur)
        b = agg["breakdown"]
        self.assertEqual(b["output_vat"], Decimal("700"))
        self.assertEqual(b["input_vat_gross"], Decimal("300"))
        self.assertEqual(b["input_vat_excluded_expired"], Decimal("100"))
        self.assertEqual(b["input_vat_excluded_missing_tax_id"], Decimal("50"))
        self.assertEqual(b["input_vat_claimable"], Decimal("150"))
        self.assertEqual(agg["net"], Decimal("550"))

    def test_six_months_boundary_still_claimable(self):
        cur = FakeCursor(
            ones=[{"total": "0", "n": 0}, {"total": "70", "n": 1}],
            alls=[
                [
                    # 2025-12 → 恰好 6 个月 → 仍可抵(超过才剔)
                    {
                        "dr_cr": "debit",
                        "amount": "70",
                        "doc_date": date(2025, 12, 31),
                        "supplier_tax_id": "0105536000011",
                    }
                ]
            ],
        )
        agg = _pp30(cur)
        self.assertEqual(agg["breakdown"]["input_vat_excluded_expired"], Decimal("0"))
        self.assertEqual(agg["net"], Decimal("-70"))
        self.assertEqual(agg["breakdown"]["carry_forward"], Decimal("70"))

    def test_credit_reversal_rows_subtract(self):
        # 红冲(进项税贷方行)记负:可抵 = 100 − 30
        cur = FakeCursor(
            ones=[{"total": "0", "n": 0}, {"total": "70", "n": 2}],
            alls=[
                [
                    {
                        "dr_cr": "debit",
                        "amount": "100",
                        "doc_date": date(2026, 6, 1),
                        "supplier_tax_id": None,
                    },
                    {
                        "dr_cr": "credit",
                        "amount": "30",
                        "doc_date": date(2026, 6, 1),
                        "supplier_tax_id": None,
                    },
                ]
            ],
        )
        agg = _pp30(cur)
        self.assertEqual(agg["breakdown"]["input_vat_excluded_missing_tax_id"], Decimal("70"))

    def test_zero_period_generates_zero_net(self):
        cur = FakeCursor(ones=[{"total": "0", "n": 0}, {"total": "0", "n": 0}], alls=[[]])
        agg = _pp30(cur)
        self.assertEqual(agg["net"], Decimal("0"))
        self.assertEqual(agg["breakdown"]["output_count"], 0)

    def test_unmapped_vat_roles_mean_empty_workspace(self):
        cur = FakeCursor()
        with mock.patch.object(aggregate.acct_store, "resolve_mappings", return_value={}):
            agg = aggregate.pp30(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        self.assertEqual(agg["net"], Decimal("0"))
        self.assertEqual(cur.executed, [])


class PndTests(unittest.TestCase):
    def _row(self, doc_id, tax_id, wht="30", base="1000", rate="3"):
        return {
            "id": doc_id,
            "doc_no": f"PI-{doc_id}",
            "doc_date": date(2026, 6, 5),
            "wht_amount": wht,
            "payee_name": "ผู้รับ",
            "payee_tax_id": tax_id,
            "wht_base": base,
            "wht_rate": rate,
            "cert_url": None,
        }

    def test_split_by_payee_type_and_missing_tax_id_counted(self):
        cur = FakeCursor(
            alls=[
                [
                    self._row("a", "0105536000011"),
                    self._row("b", "1234567890123", wht="50"),
                    self._row("c", None, wht="20"),
                ]
            ]
        )
        out = aggregate.pnd(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        t53, t3 = out["tables"]["pnd53"], out["tables"]["pnd3"]
        self.assertEqual(len(t53["lines"]), 2)  # 法人 + 缺税号默认法人
        self.assertEqual(len(t3["lines"]), 1)
        self.assertEqual(t53["total"], Decimal("50"))
        self.assertEqual(t3["total"], Decimal("50"))
        self.assertEqual(t53["missing_tax_id"], 1)
        self.assertEqual(t53["lines"][1]["cert_status"], "missing_tax_id")
        sql, params = cur.executed[0]
        self.assertIn("workspace_client_id", sql)
        self.assertIn("d.status = 'posted'", sql)
        self.assertIn("d.wht_amount > 0", sql)

    def test_bad_period_rejected(self):
        from core.pos_api import PosError

        with self.assertRaises(PosError):
            aggregate.pnd(FakeCursor(), tenant_id="t", workspace_client_id=1, period="junk")


if __name__ == "__main__":
    unittest.main()

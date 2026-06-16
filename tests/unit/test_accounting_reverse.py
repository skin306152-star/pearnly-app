# -*- coding: utf-8 -*-
"""红冲 reverse_voucher 单测(docs/purchasing/04):已结期凭证 → 当期反向凭证。

验:行借贷对调 + source_type 加 _reversal 后缀;当前期也已结 → acct.no_open_period;
无行(待审壳)/已 void → 不插入。不连真库(insert/get_voucher/settings 全 mock)。
"""

import unittest
from unittest import mock

from core.pos_api import PosError
from services.accounting import posting
from services.accounting import settings as acct_settings
from services.accounting import vouchers as jv


class _Cur:
    def execute(self, *a, **k):
        return None


def _voucher(lines, status="auto_posted"):
    return {
        "id": "v1",
        "status": status,
        "period": "2026-02",
        "source_type": "purchase",
        "source_id": "D",
        "source_ref": "INV-1",
        "voucher_no": "JV2602-1",
        "lines": lines,
    }


def _reverse(voucher):
    return posting.reverse_voucher(
        _Cur(), tenant_id="t", workspace_client_id=1, voucher_id="v1", created_by="u"
    )


class ReverseVoucherTests(unittest.TestCase):
    def test_reverses_lines_and_inserts_in_current_period(self):
        v = _voucher(
            [
                {"account_id": "a", "dr_cr": "debit", "amount": 100, "memo": "进项"},
                {"account_id": "b", "dr_cr": "credit", "amount": 100},
            ]
        )
        captured = {}

        def fake_insert(cur, **k):
            captured.update(k)
            return {"id": "rev1"}

        with (
            mock.patch.object(jv, "get_voucher", return_value=v),
            mock.patch.object(acct_settings, "get_settings", return_value={}),
            mock.patch.object(acct_settings, "is_period_closed", return_value=False),
            mock.patch.object(jv, "insert_voucher", side_effect=fake_insert),
        ):
            res = _reverse(v)
        self.assertEqual(res["id"], "rev1")
        ls = captured["lines"]
        self.assertEqual(ls[0]["dr_cr"], "credit")  # debit → credit
        self.assertEqual(ls[1]["dr_cr"], "debit")  # credit → debit
        self.assertEqual(ls[0]["amount"], 100)  # 金额不变
        self.assertEqual(captured["header"]["source_type"], "purchase_reversal")  # 避唯一约束

    def test_current_period_closed_raises(self):
        v = _voucher([{"account_id": "a", "dr_cr": "debit", "amount": 100}])
        with (
            mock.patch.object(jv, "get_voucher", return_value=v),
            mock.patch.object(acct_settings, "get_settings", return_value={}),
            mock.patch.object(acct_settings, "is_period_closed", return_value=True),
            self.assertRaises(PosError) as e,
        ):
            _reverse(v)
        self.assertEqual(e.exception.code, "acct.no_open_period")

    def test_no_lines_noop(self):
        v = _voucher([])
        with (
            mock.patch.object(jv, "get_voucher", return_value=v),
            mock.patch.object(jv, "insert_voucher") as ins,
        ):
            res = _reverse(v)
        ins.assert_not_called()
        self.assertEqual(res["id"], "v1")

    def test_already_void_noop(self):
        v = _voucher([{"account_id": "a", "dr_cr": "debit", "amount": 100}], status="void")
        with (
            mock.patch.object(jv, "get_voucher", return_value=v),
            mock.patch.object(jv, "insert_voucher") as ins,
        ):
            res = _reverse(v)
        ins.assert_not_called()
        self.assertEqual(res["status"], "void")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""POS 今日交易列表(services/pos/sale.list_today · 退货/作废入口)守门测试。

锁定 voidable 判定镜像 void_sale 边界(单一事实源):
  1. 当前未结班的单 + 未退过 → 可作废;
  2. 已退过(has_refund)→ 不可作废(点了后端也兜 void_not_allowed);
  3. 属别的(已交/别台)班次 → 不可作废;
  4. mixed 由 pay_count>1 标记;method/金额透传成字符串。
"""

import os
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from services.pos import sale as sale_svc


def _row(**over):
    base = {
        "id": "s1",
        "receipt_no": "RCP-001",
        "sold_at": datetime(2026, 7, 11, 9, 16, tzinfo=timezone.utc),
        "grand_total": Decimal("75.00"),
        "shift_id": "sh-open",
        "top_method": "cash",
        "pay_count": 1,
        "has_refund": False,
    }
    base.update(over)
    return base


class ListTodayTests(unittest.TestCase):
    def _run(self, rows, open_shift_id="sh-open"):
        open_shift = {"id": open_shift_id} if open_shift_id else None
        with (
            mock.patch.object(sale_svc.sales_store, "list_today_rows", return_value=rows),
            mock.patch(
                "services.pos.cashier.get_open_shift_for_workspace", return_value=open_shift
            ),
        ):
            return sale_svc.list_today(cur=object(), tenant_id="t", workspace_client_id=1)

    def test_current_shift_not_refunded_is_voidable(self):
        out = self._run([_row()])
        item = out["items"][0]
        self.assertTrue(item["voidable"])
        self.assertEqual(item["grand_total"], "75.00")
        self.assertEqual(item["method"], "cash")
        self.assertFalse(item["mixed"])
        self.assertEqual(item["sold_at"], "2026-07-11T09:16:00+00:00")

    def test_refunded_sale_not_voidable(self):
        out = self._run([_row(has_refund=True)])
        self.assertFalse(out["items"][0]["voidable"])

    def test_other_shift_not_voidable(self):
        out = self._run([_row(shift_id="sh-closed")])
        self.assertFalse(out["items"][0]["voidable"])

    def test_mixed_flag_from_pay_count(self):
        out = self._run([_row(pay_count=2, top_method="card")])
        self.assertTrue(out["items"][0]["mixed"])
        self.assertEqual(out["items"][0]["method"], "card")

    def test_no_open_shift_makes_shifted_sale_unvoidable(self):
        out = self._run([_row()], open_shift_id=None)
        self.assertFalse(out["items"][0]["voidable"])

    def test_null_method_defaults_cash(self):
        out = self._run([_row(top_method=None)])
        self.assertEqual(out["items"][0]["method"], "cash")


if __name__ == "__main__":
    unittest.main()

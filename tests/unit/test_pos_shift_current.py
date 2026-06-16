# -*- coding: utf-8 -*-
"""POS 当前班次(交班屏直查)守门测试。

锁定:current_shift 按套账取未结班次 → 算应有现金(备用金 + 现金收取 − 找零)+ 透出
summary.expected_cash;无班次返 None(屏显诚实空态,不靠前端内存)。"""

import unittest
from datetime import datetime
from decimal import Decimal

from services.pos import shift


class FakeCursor:
    def __init__(self, ones=None, many=None):
        self.calls = []
        self._ones = list(ones or [])
        self._many = list(many or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return self._many.pop(0) if self._many else []


class CurrentShiftTests(unittest.TestCase):
    def test_none_when_no_open_shift(self):
        cur = FakeCursor(ones=[None])
        self.assertIsNone(shift.current_shift(cur, tenant_id="t", workspace_client_id=9))

    def test_returns_shift_with_expected_cash(self):
        opened = datetime(2026, 5, 2, 20, 35)
        cur = FakeCursor(
            # get_open_shift_for_workspace → _summary(head, change)
            ones=[
                {
                    "id": "s1",
                    "terminal_id": 3,
                    "opened_at": opened,
                    "opening_float": Decimal("500"),
                },
                {"n": 4, "gross": Decimal("2000")},
                {"chg": Decimal("50")},
            ],
            # _summary by_method fetchall
            many=[[{"method": "cash", "amt": Decimal("1000")}]],
        )
        out = shift.current_shift(cur, tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["shift"]["id"], "s1")
        self.assertEqual(out["shift"]["terminal_id"], 3)
        self.assertEqual(out["summary"]["sales_count"], 4)
        # 应有现金 = 500 备用金 + 1000 现金收取 − 50 找零
        self.assertEqual(out["summary"]["expected_cash"], 1450.0)


if __name__ == "__main__":
    unittest.main()

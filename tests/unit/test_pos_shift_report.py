# -*- coding: utf-8 -*-
"""钱箱盈亏台账读模型守门(PC-3 · services/pos/shift_report.py)。

断言:① 缺号检测(相邻在场连号断裂 → missing_seqs);② 金额 2 位小数字符串、时间 isoformat、
空值保 None;③ 查询按 tenant + workspace_client_id 隔离;④ 按连号倒序取本账套班次。
"""

import datetime
import unittest
from decimal import Decimal

from services.pos import shift_report as sr

TID = "tenant-1"
WS = 7


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params) if params else []))

    def fetchall(self):
        return self.rows


def _row(seq, diff, status="closed", **kw):
    base = {
        "id": f"s{seq}",
        "shift_seq": seq,
        "cashier_id": "aya",
        "cashier_name": "Aya",
        "opened_at": datetime.datetime(2026, 7, 11, 8, 0, tzinfo=datetime.timezone.utc),
        "closed_at": datetime.datetime(2026, 7, 11, 20, 0, tzinfo=datetime.timezone.utc),
        "opening_float": Decimal("500"),
        "expected_cash": Decimal("1450"),
        "counted_cash": Decimal("1400"),
        "cash_diff": Decimal(str(diff)),
        "status": status,
    }
    base.update(kw)
    return base


class ShiftReportTests(unittest.TestCase):
    def test_detects_missing_seq_gap(self):
        # 连号 5,3,2 → 4 断裂 = 某张班被删的信号。
        cur = FakeCursor([_row(5, -50), _row(3, 0), _row(2, 20)])
        out = sr.list_shifts(cur, tenant_id=TID, workspace_client_id=WS)
        self.assertEqual(out["missing_seqs"], [4])

    def test_no_gap_when_contiguous(self):
        cur = FakeCursor([_row(3, 0), _row(2, 0), _row(1, 0)])
        out = sr.list_shifts(cur, tenant_id=TID, workspace_client_id=WS)
        self.assertEqual(out["missing_seqs"], [])

    def test_money_and_time_serialized(self):
        cur = FakeCursor([_row(5, -50)])
        out = sr.list_shifts(cur, tenant_id=TID, workspace_client_id=WS)
        s = out["shifts"][0]
        self.assertEqual(s["cash_diff"], "-50.00")
        self.assertEqual(s["expected_cash"], "1450.00")
        self.assertEqual(s["counted_cash"], "1400.00")
        self.assertTrue(s["opened_at"].startswith("2026-07-11"))
        self.assertEqual(s["shift_seq"], 5)
        self.assertEqual(s["status"], "closed")

    def test_open_shift_null_cash_fields_stay_none(self):
        cur = FakeCursor(
            [
                _row(
                    6,
                    0,
                    status="open",
                    closed_at=None,
                    expected_cash=None,
                    counted_cash=None,
                    cash_diff=None,
                )
            ]
        )
        out = sr.list_shifts(cur, tenant_id=TID, workspace_client_id=WS)
        s = out["shifts"][0]
        self.assertIsNone(s["closed_at"])
        self.assertIsNone(s["expected_cash"])
        self.assertIsNone(s["cash_diff"])

    def test_scoped_and_ordered(self):
        cur = FakeCursor([_row(1, 0)])
        sr.list_shifts(cur, tenant_id=TID, workspace_client_id=WS)
        sql, params = cur.calls[0]
        self.assertIn("sh.tenant_id = %s", sql)
        self.assertIn("sh.workspace_client_id = %s", sql)
        self.assertIn("ORDER BY sh.shift_seq DESC", sql)
        self.assertEqual(params[0], TID)
        self.assertEqual(params[1], WS)


if __name__ == "__main__":
    unittest.main()

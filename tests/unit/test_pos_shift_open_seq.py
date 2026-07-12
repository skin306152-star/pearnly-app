# -*- coding: utf-8 -*-
"""开班连号赋号守门(PC-3 · services/pos/shift.open_shift)。

锁定:① shift_seq = 本 (tenant,ws) MAX+1,与 insert 同事务;② 并发撞唯一约束时经 SAVEPOINT
重取一次(不 poison 外层交易事务);③ 返回体带 shift_seq。对账公式与 close 不动(见 test_pos_shift_current)。
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest import mock

import psycopg2

from core.pos_api import PosError
from services.pos import shift

OPENED = datetime(2026, 7, 11, 8, 0)


class OpenCursor:
    """按 SQL 特征分派:开班占用检查(空)/MAX+1/INSERT RETURNING/SAVEPOINT 等控制语句。
    fail_inserts=N 让前 N 次 INSERT 抛唯一冲突(模拟并发撞号)。"""

    def __init__(self, seqs, insert_rows, fail_inserts=0):
        self.seqs = list(seqs)
        self.insert_rows = list(insert_rows)
        self.fail_inserts = fail_inserts
        self.calls = []
        self._pending = None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "FROM pos_terminals" in sql:
            self._pending = {"id": 3, "is_active": True}
        elif "FROM pos_cashiers" in sql:
            self._pending = {"id": "c1", "is_active": True}
        elif sql.strip().startswith("INSERT INTO pos_shifts"):
            if self.fail_inserts > 0:
                self.fail_inserts -= 1
                raise psycopg2.errors.UniqueViolation("dup shift_seq")
            self._pending = self.insert_rows.pop(0)
        elif "COALESCE(MAX(shift_seq)" in sql:
            self._pending = self.seqs.pop(0)
        else:
            self._pending = None  # 开班占用检查 / SAVEPOINT / ROLLBACK / RELEASE

    def fetchone(self):
        return self._pending


def _insert_row(seq):
    return {"id": "s1", "opened_at": OPENED, "opening_float": Decimal("500"), "shift_seq": seq}


class OpenShiftSeqTests(unittest.TestCase):
    def test_assigns_max_plus_one_and_returns_seq(self):
        cur = OpenCursor(seqs=[{"n": 4}], insert_rows=[_insert_row(4)])
        out = shift.open_shift(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            terminal_id=3,
            cashier_id="c1",
            opening_float=500,
        )
        self.assertEqual(out["shift_seq"], 4)
        insert = next(c for c in cur.calls if c[0].strip().startswith("INSERT"))
        self.assertEqual(insert[1][-1], 4)  # 最后一个参数 = shift_seq

    def test_retries_once_on_unique_violation(self):
        # 首次 INSERT 撞唯一约束 → ROLLBACK TO SAVEPOINT + 重取 MAX+1 再插。
        cur = OpenCursor(seqs=[{"n": 4}, {"n": 4}], insert_rows=[_insert_row(4)], fail_inserts=1)
        out = shift.open_shift(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            terminal_id=3,
            cashier_id="c1",
            opening_float=500,
        )
        self.assertEqual(out["shift_seq"], 4)
        self.assertTrue(any("ROLLBACK TO SAVEPOINT" in c[0] for c in cur.calls))
        inserts = [c for c in cur.calls if c[0].strip().startswith("INSERT")]
        self.assertEqual(len(inserts), 2)  # 撞一次 + 重试一次

    def test_terminal_unique_conflict_returns_pos_error(self):
        cur = OpenCursor(seqs=[{"n": 4}], insert_rows=[], fail_inserts=1)
        with (
            mock.patch.object(shift, "_terminal_open_conflict", return_value=True),
            self.assertRaises(PosError) as ctx,
        ):
            shift.open_shift(
                cur,
                tenant_id="t",
                workspace_client_id=9,
                terminal_id=3,
                cashier_id="c1",
                opening_float=500,
            )
        self.assertEqual(ctx.exception.code, "pos.shift_already_open")
        inserts = [c for c in cur.calls if c[0].strip().startswith("INSERT")]
        self.assertEqual(len(inserts), 1)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""Pearnly Voice 每日上限:n<CAP 放行、达上限拦、配额故障不挡闲聊(异常 → True)。"""

import unittest
from unittest import mock

from services.expense import line_voice_quota as Q


class _Cur:
    def __init__(self, row=None, raise_on_exec=False):
        self._row = row
        self._raise = raise_on_exec

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a):
        if self._raise:
            raise RuntimeError("db down")

    def fetchone(self):
        return self._row


class WithinCapTests(unittest.TestCase):
    def test_under_cap_true(self):
        with mock.patch("core.db.get_cursor", return_value=_Cur(row={"n": Q.DAILY_CAP - 1})):
            self.assertTrue(Q.within_cap("U1", "T1"))

    def test_no_row_true(self):
        with mock.patch("core.db.get_cursor", return_value=_Cur(row=None)):
            self.assertTrue(Q.within_cap("U1", "T1"))

    def test_at_cap_false(self):
        with mock.patch("core.db.get_cursor", return_value=_Cur(row={"n": Q.DAILY_CAP})):
            self.assertFalse(Q.within_cap("U1", "T1"))

    def test_over_cap_false(self):
        with mock.patch("core.db.get_cursor", return_value=_Cur(row={"n": Q.DAILY_CAP + 5})):
            self.assertFalse(Q.within_cap("U1", "T1"))

    def test_exception_returns_true(self):
        with mock.patch("core.db.get_cursor", return_value=_Cur(raise_on_exec=True)):
            self.assertTrue(Q.within_cap("U1", "T1"))

    def test_no_user_true(self):
        self.assertTrue(Q.within_cap("", "T1"))


class BumpTests(unittest.TestCase):
    def test_bump_executes_upsert(self):
        cur = _Cur()
        with (
            mock.patch("core.db.get_cursor", return_value=cur),
            mock.patch.object(cur, "execute", wraps=cur.execute) as ex,
        ):
            Q.bump("U1", "T1")
        ex.assert_called_once()
        self.assertIn("ON CONFLICT", ex.call_args[0][0])

    def test_bump_swallows_exception(self):
        with mock.patch("core.db.get_cursor", return_value=_Cur(raise_on_exec=True)):
            Q.bump("U1", "T1")  # 不抛

    def test_no_user_noop(self):
        with mock.patch("core.db.get_cursor") as gc:
            Q.bump("", "T1")
            gc.assert_not_called()


if __name__ == "__main__":
    unittest.main()

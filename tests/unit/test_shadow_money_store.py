# -*- coding: utf-8 -*-
"""shadow_money_store 守门:insert 走 RLS 游标且列序对齐、aggregate 不一致率算对、
表缺失时 _with_heal 自愈重试一次。core.db 全 mock,不连真库。"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from unittest import mock

from services.ocr import shadow_money_store as st


def _fake_cursor(fetchone=None):
    cur = mock.MagicMock()
    cur.fetchone.return_value = fetchone

    @contextmanager
    def _cm(*a, **k):
        yield cur

    return cur, _cm


class InsertTests(unittest.TestCase):
    def test_insert_uses_rls_cursor_and_values(self):
        cur, cm = _fake_cursor()
        fake_db = mock.MagicMock()
        fake_db.get_cursor_rls = cm
        with mock.patch("core.db", fake_db, create=True):
            st.insert(
                "t1",
                "h1",
                values={
                    "total": (1780.0, 1780.0),
                    "vat": (116.0, 116.0),
                    "discount": (None, None),
                    "subtotal": (1664.0, 1664.0),
                },
                matches={"total": True, "vat": True, "discount": True, "subtotal": True},
                match_all=True,
                b_confidence="high",
                status="ok",
            )
        sql = cur.execute.call_args.args[0]
        params = cur.execute.call_args.args[1]
        self.assertIn("INSERT INTO shadow_money_log", sql)
        self.assertEqual(params[0], "t1")
        self.assertEqual(params[1], "h1")
        self.assertEqual(params[-1], "ok")  # status 末列
        self.assertIn(True, params)  # match 布尔进参

    def test_insert_swallows_errors(self):
        fake_db = mock.MagicMock()
        fake_db.get_cursor_rls.side_effect = RuntimeError("connection lost")
        with mock.patch("core.db", fake_db, create=True):
            # 不抛(影子绝不反噬);表名不在异常里 → _with_heal 直接上抛后被外层 try 吞
            st.insert(
                "t1",
                "h1",
                values={k: (None, None) for k in ("total", "vat", "discount", "subtotal")},
                matches={k: None for k in ("total", "vat", "discount", "subtotal")},
                match_all=None,
                b_confidence="",
                status="failed",
            )


class AggregateTests(unittest.TestCase):
    def test_rate_math(self):
        cur, cm = _fake_cursor(fetchone={"total": 100, "mism": 6})
        fake_db = mock.MagicMock()
        fake_db.get_cursor = cm
        with mock.patch("core.db", fake_db, create=True):
            out = st.aggregate(days=30)
        self.assertEqual(out["total"], 100)
        self.assertEqual(out["mismatches"], 6)
        self.assertAlmostEqual(out["rate"], 0.06)
        self.assertEqual(out["days"], 30)

    def test_zero_total_no_div_by_zero(self):
        cur, cm = _fake_cursor(fetchone={"total": 0, "mism": 0})
        fake_db = mock.MagicMock()
        fake_db.get_cursor = cm
        with mock.patch("core.db", fake_db, create=True):
            out = st.aggregate()
        self.assertEqual(out["rate"], 0.0)

    def test_aggregate_failure_returns_empty(self):
        fake_db = mock.MagicMock()
        fake_db.get_cursor.side_effect = RuntimeError("boom")
        with mock.patch("core.db", fake_db, create=True):
            out = st.aggregate()
        self.assertEqual(out["total"], 0)
        self.assertEqual(out["rate"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

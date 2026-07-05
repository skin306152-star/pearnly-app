# -*- coding: utf-8 -*-
"""LINE 获客漏斗打点(line_funnel)契约。

铁三条:① mark best-effort 绝不抛(打点炸不许挡欢迎/主路径);② 重复事件
ON CONFLICT 无声跳过(每人每级只记首次);③ 表不存在首用自愈重试一次。
"""

import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from services.line_binding import line_funnel


@contextmanager
def _cm(cur):
    yield cur


class TestMark(unittest.TestCase):
    def test_inserts_with_conflict_skip(self):
        cur = MagicMock()
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            line_funnel.mark("follow", "U1")
        sql, params = cur.execute.call_args.args
        self.assertIn("ON CONFLICT (line_user_id, event) DO NOTHING", sql)
        self.assertEqual(params, ("U1", "follow"))

    def test_no_line_user_skips_db(self):
        with patch("core.db.get_cursor") as g:
            line_funnel.mark("follow", None)
        g.assert_not_called()

    def test_db_failure_never_raises(self):
        with patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            line_funnel.mark("follow", "U1")  # 不抛 = 通过

    def test_missing_table_heals_and_retries(self):
        calls = []

        def flaky_cursor(**k):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError('relation "line_funnel_events" does not exist')
            return _cm(MagicMock())

        with (
            patch("core.db.get_cursor", flaky_cursor),
            patch.object(line_funnel, "ensure_table") as ens,
        ):
            line_funnel.mark("follow", "U1")
        ens.assert_called_once()
        self.assertEqual(len(calls), 2)  # 自愈后重试


class TestFunnelStats(unittest.TestCase):
    def test_shape(self):
        cur = MagicMock()
        cur.fetchone.side_effect = [
            {"n": 30},
            {"n": 12},
            {"used": 9, "recorded": 5},
        ]
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            out = line_funnel.funnel_stats(days=7)
        self.assertEqual(
            out, {"days": 7, "follows": 30, "binds": 12, "agent_used": 9, "recorded": 5}
        )


if __name__ == "__main__":
    unittest.main()

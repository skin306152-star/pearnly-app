# -*- coding: utf-8 -*-
"""LINE webhook 事件去重(webhookEventId 幂等·at-most-once)契约。

铁三条:① 首见事件放行 + 落表抢占;② 重投(冲突插不进)整个事件跳过;
③ 无 id / 表故障一律放行——去重是增强不是闸,绝不许挡正常消息。
"""

import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from services.line_binding import line_webhook_dedup as dd


def _cursor(rowcount):
    cur = MagicMock()
    cur.rowcount = rowcount
    return cur


@contextmanager
def _cm(cur):
    yield cur


class TestSeenBefore(unittest.TestCase):
    def test_fresh_event_processes_and_cleans(self):
        cur = _cursor(rowcount=1)
        with (
            patch("core.db.get_cursor", lambda **k: _cm(cur)),
            patch.object(dd.random, "random", return_value=0.0),  # 命中采样 → 必跑清理
        ):
            self.assertFalse(dd.seen_before("evt-1"))
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(any("ON CONFLICT (event_id) DO NOTHING" in s for s in sqls))
        self.assertTrue(any("DELETE FROM line_webhook_events" in s for s in sqls))  # 采样清老行

    def test_cleanup_is_sampled_not_every_event(self):
        # 热路径:未命中采样时只 INSERT,不为"几乎总删空"的 DELETE 买单。
        cur = _cursor(rowcount=1)
        with (
            patch("core.db.get_cursor", lambda **k: _cm(cur)),
            patch.object(dd.random, "random", return_value=0.99),
        ):
            self.assertFalse(dd.seen_before("evt-2"))
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertFalse(any("DELETE" in s for s in sqls))

    def test_redelivery_is_skipped(self):
        cur = _cursor(rowcount=0)  # 冲突插不进 = 处理过
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            self.assertTrue(dd.seen_before("evt-1"))

    def test_missing_id_never_blocks(self):
        # 老格式无 webhookEventId:放行且不碰库(宁可重复处理,不许误吞)。
        with patch("core.db.get_cursor") as g:
            self.assertFalse(dd.seen_before(None))
            self.assertFalse(dd.seen_before(""))
        g.assert_not_called()

    def test_store_failure_fails_open(self):
        with patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            self.assertFalse(dd.seen_before("evt-1"))

    def test_ensure_table_disables_rls(self):
        # 非租户表必须显式 DISABLE RLS(防托管库自动开成 deny-all 孤儿)。
        cur = _cursor(rowcount=0)
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            dd.ensure_table()
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(any("DISABLE ROW LEVEL SECURITY" in s for s in sqls))


if __name__ == "__main__":
    unittest.main()

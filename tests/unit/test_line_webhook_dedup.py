# -*- coding: utf-8 -*-
"""LINE webhook 事件幂等状态机(claim / mark_done / mark_failed)契约。

铁四条:① 首见事件放行 + 落 processing 占坑;② 已 done / 正在处理 / 已 failed 一律跳过
(failed 绝不自动重跑——handler 可能已部分写库,重放=重复入账);③ processing 超时残留
只补跑一次,且抢占条件全写在 WHERE 里,并发只有一家赢;④ 无 id / 表故障一律放行——
去重是增强不是闸,绝不许挡正常消息。
"""

import json
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from services.line_binding import line_webhook_dedup as dd


class _Cursor:
    """按 execute 次序吐 rowcount 的假游标。

    claim 一次事务里最多跑两条语句(INSERT 占坑 → 抢占 UPDATE),两条的 rowcount 含义
    不同,故不能用单值 MagicMock.rowcount。
    """

    def __init__(self, *rowcounts):
        self._pending = list(rowcounts)
        self.rowcount = 0
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if self._pending:
            self.rowcount = self._pending.pop(0)

    @property
    def sqls(self):
        return [sql for sql, _ in self.calls]


@contextmanager
def _cm(cur):
    yield cur


def _patch_db(cur):
    return patch("core.db.get_cursor", lambda **k: _cm(cur))


class ClaimTests(unittest.TestCase):
    def test_fresh_event_takes_the_slot_as_processing(self):
        cur = _Cursor(1)  # INSERT 插进去了 = 首见
        with _patch_db(cur), patch.object(dd.random, "random", return_value=0.99):
            self.assertEqual(dd.claim("evt-1", source="line"), dd.CLAIM_FRESH)
        sql, params = cur.calls[0]
        self.assertIn("ON CONFLICT (event_id) DO NOTHING", sql)
        self.assertIn("'processing'", sql)  # 占坑态,不是直接 done
        self.assertEqual(params, ("evt-1", "line"))

    def test_fresh_event_samples_cleanup(self):
        cur = _Cursor(1)
        with _patch_db(cur), patch.object(dd.random, "random", return_value=0.0):
            dd.claim("evt-1")
        self.assertTrue(any("DELETE FROM line_webhook_events" in s for s in cur.sqls))

    def test_cleanup_is_sampled_not_every_event(self):
        # 热路径:未命中采样时不为"几乎总删空"的 DELETE 买单。
        cur = _Cursor(1)
        with _patch_db(cur), patch.object(dd.random, "random", return_value=0.99):
            dd.claim("evt-2")
        self.assertFalse(any("DELETE" in s for s in cur.sqls))

    def test_done_event_is_skipped(self):
        # INSERT 冲突 + 抢占 UPDATE 一行没中(status='done' 不在谓词内)→ 跳过。
        cur = _Cursor(0, 0)
        with _patch_db(cur):
            self.assertEqual(dd.claim("evt-1"), dd.CLAIM_SKIP)

    def test_failed_event_is_never_auto_retried(self):
        """failed 行不在抢占谓词内 → 恒 skip。重投的路是让用户重发,不是机器重放。"""
        cur = _Cursor(0, 0)
        with _patch_db(cur):
            self.assertEqual(dd.claim("evt-1"), dd.CLAIM_SKIP)
        reclaim_sql = cur.sqls[1]
        self.assertIn("status = 'processing'", reclaim_sql)
        self.assertNotIn("'failed'", reclaim_sql)

    def test_in_flight_processing_is_skipped(self):
        """处理中(未超时)→ UPDATE 的 updated_at 谓词不成立 → 0 行 → 跳过,不并发双跑。"""
        cur = _Cursor(0, 0)
        with _patch_db(cur):
            self.assertEqual(dd.claim("evt-1"), dd.CLAIM_SKIP)
        sql, params = cur.calls[1]
        self.assertIn("updated_at < now() - make_interval(mins => %s)", sql)
        self.assertEqual(params, ("evt-1", dd._MAX_ATTEMPTS, dd._STALE_MINUTES))

    def test_stale_processing_is_reclaimed_once(self):
        cur = _Cursor(0, 1)  # 插不进,但抢占 UPDATE 中了一行 = 崩溃残留
        with _patch_db(cur):
            self.assertEqual(dd.claim("evt-1"), dd.CLAIM_RECLAIM)
        self.assertIn("attempts < %s", cur.sqls[1])  # 只补跑一次的闸

    def test_concurrent_reclaim_only_one_wins(self):
        """两个投递同时撞残留行:抢占条件全在 WHERE,UPDATE 到行的才算,另一个 0 行 → skip。"""
        winner, loser = _Cursor(0, 1), _Cursor(0, 0)
        with _patch_db(winner):
            self.assertEqual(dd.claim("evt-1"), dd.CLAIM_RECLAIM)
        with _patch_db(loser):
            self.assertEqual(dd.claim("evt-1"), dd.CLAIM_SKIP)

    def test_missing_id_never_blocks(self):
        # 老格式无 webhookEventId:放行且不碰库(宁可重复处理,不许误吞)。
        with patch("core.db.get_cursor") as g:
            self.assertEqual(dd.claim(None), dd.CLAIM_FRESH)
            self.assertEqual(dd.claim(""), dd.CLAIM_FRESH)
        g.assert_not_called()

    def test_store_failure_fails_open(self):
        with patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            self.assertEqual(dd.claim("evt-1"), dd.CLAIM_FRESH)


class MarkTests(unittest.TestCase):
    def test_mark_done_clears_payload(self):
        cur = _Cursor(1)
        with _patch_db(cur):
            dd.mark_done("evt-1")
        sql, params = cur.calls[0]
        self.assertIn("status = 'done'", sql)
        self.assertIn("payload = NULL", sql)  # 消息内容没有长期留存的理由
        self.assertEqual(params, ("evt-1",))

    def test_mark_failed_stores_error_and_payload(self):
        cur = _Cursor(1)
        ev = {"webhookEventId": "evt-1", "type": "message", "message": {"text": "กาแฟ 50"}}
        with _patch_db(cur):
            dd.mark_failed("evt-1", "ValueError: boom", ev)
        sql, params = cur.calls[0]
        self.assertIn("status = 'failed'", sql)
        self.assertEqual(params[0], "ValueError: boom")
        self.assertIn("กาแฟ 50", params[1])  # 原始事件留库供人工排查
        self.assertEqual(params[2], "evt-1")

    def test_mark_failed_truncates_oversized_payload_into_valid_json(self):
        # 截断的 JSON 不是合法 jsonb,超长必须整体换成包装对象。
        cur = _Cursor(1)
        big = {"text": "x" * (dd._MAX_PAYLOAD_CHARS + 10)}
        with _patch_db(cur):
            dd.mark_failed("evt-1", "boom", big)
        parsed = json.loads(cur.calls[0][1][1])
        self.assertTrue(parsed["truncated"])

    def test_mark_never_raises_into_caller(self):
        # 事件已经在出错路径上,记账簿写不进去不该再掀翻路由。
        with patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            dd.mark_done("evt-1")
            dd.mark_failed("evt-1", "boom", {"a": 1})

    def test_mark_ignores_empty_id(self):
        with patch("core.db.get_cursor") as g:
            dd.mark_done(None)
            dd.mark_failed("", "boom")
        g.assert_not_called()


class EnsureTableTests(unittest.TestCase):
    def test_legacy_rows_default_to_done(self):
        """建列前的存量行语义 = 已处理完;DEFAULT 'done' 就地钉住,不因加列被重跑。"""
        cur = MagicMock()
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            dd.ensure_table()
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(any("status text NOT NULL DEFAULT 'done'" in s for s in sqls))

    def test_adds_all_state_columns_idempotently(self):
        cur = MagicMock()
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            dd.ensure_table()
        sqls = " ".join(c.args[0] for c in cur.execute.call_args_list)
        for col in ("status", "source", "attempts", "last_error", "payload", "updated_at"):
            self.assertIn(f"ADD COLUMN IF NOT EXISTS {col}", sqls)

    def test_ensure_table_disables_rls(self):
        # 非租户表必须显式 DISABLE RLS(防托管库自动开成 deny-all 孤儿)。
        cur = MagicMock()
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            dd.ensure_table()
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(any("DISABLE ROW LEVEL SECURITY" in s for s in sqls))


if __name__ == "__main__":
    unittest.main()

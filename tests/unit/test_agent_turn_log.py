# -*- coding: utf-8 -*-
"""Agent 轮级审计(agent_turn_logs)契约。

铁三条:① record best-effort 绝不挡对话(DB 炸只记日志);② crash 落行必打
[agent-alarm] error 标记(prod 日志侧聚合告警);③ bridge 每轮出口都留痕
(loop 结局带 trace/工具轨迹,异常路也落 crash 行)。
"""

import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from services.agent import turn_log


@contextmanager
def _cm(cur):
    yield cur


class TestRecord(unittest.TestCase):
    def _record(self, cur, kind="reply"):
        with patch("core.db.get_cursor_rls", lambda tid, **k: _cm(cur)):
            turn_log.record(
                tenant_id="t1",
                user_id="u1",
                line_user_id="U1",
                trace_id="tr1",
                lang="th",
                user_text="ยอดเงิน" * 200,
                result_kind=kind,
                tool_trace=[{"tool": "balance", "ok": True, "error": None}],
                elapsed_ms=1234,
            )

    def test_inserts_row_and_cleans_retention(self):
        cur = MagicMock()
        self._record(cur)
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(any("INSERT INTO agent_turn_logs" in s for s in sqls))
        self.assertTrue(any("DELETE FROM agent_turn_logs" in s for s in sqls))  # 90d 写时顺清
        ins = next(c for c in cur.execute.call_args_list if "INSERT" in c.args[0])
        self.assertLessEqual(len(ins.args[1][5]), turn_log._TEXT_MAX)  # user_text 截断

    def test_crash_logs_alarm_marker(self):
        cur = MagicMock()
        with self.assertLogs("services.agent.turn_log", level="ERROR") as logs:
            self._record(cur, kind="crash")
        self.assertTrue(any("[agent-alarm]" in m for m in logs.output))

    def test_db_failure_never_raises(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            turn_log.record(
                tenant_id="t1",
                user_id="u1",
                line_user_id="U1",
                trace_id="tr1",
                lang="th",
                user_text="x",
                result_kind="reply",
                tool_trace=[],
                elapsed_ms=1,
            )  # 不抛 = 通过

    def test_no_tenant_skips_db(self):
        with patch("core.db.get_cursor_rls") as g:
            turn_log.record(
                tenant_id=None,
                user_id=None,
                line_user_id="U1",
                trace_id=None,
                lang="th",
                user_text="x",
                result_kind="reply",
                tool_trace=[],
                elapsed_ms=1,
            )
        g.assert_not_called()

    def test_stats_shape(self):
        cur = MagicMock()
        cur.fetchall.return_value = [
            {"result_kind": "reply", "n": 8, "avg_ms": 900},
            {"result_kind": "crash", "n": 2, "avg_ms": 1500},
        ]
        with patch("core.db.get_cursor", lambda **k: _cm(cur)):
            out = turn_log.stats(hours=24)
        self.assertEqual(out["total"], 10)
        self.assertEqual(out["crash_rate"], 0.2)
        self.assertEqual(out["by_kind"]["reply"]["count"], 8)

    def test_ensure_table_applies_rls(self):
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", lambda **k: _cm(cur)),
            patch("core.rls.apply_tenant_rls") as rls,
        ):
            turn_log.ensure_table()
        rls.assert_called_once_with(cur, "agent_turn_logs")


class TestBridgeAudit(unittest.TestCase):
    def test_loop_turn_recorded_with_trace(self):
        from services.agent.loop import TurnResult
        from services.line_binding import line_agent_bridge as bridge

        rec = {}

        def fake_record(**kw):
            rec.update(kw)

        def fake_handle_turn(text, ctx, **kw):
            ctx.trace_id = "tr-9"
            ctx.tool_trace.append({"tool": "balance", "ok": True, "error": None})
            return TurnResult("reply", "58")

        with (
            patch("core.feature_flags.agent_enabled_for", return_value=True),
            patch("core.feature_flags.agent_write_enabled_for", return_value=False),
            patch("services.agent.confirm_machine.try_resume", return_value=False),
            patch("services.agent.recon_intake.try_text", return_value=False),
            patch("services.agent.loop.handle_turn", fake_handle_turn),
            patch("services.agent.turn_log.record", fake_record),
        ):
            res = bridge.try_agent_turn(
                {"id": "u1", "tenant_id": "t1"}, "ยอดเงิน", "th", "t1", 1, "U1", []
            )
        self.assertEqual(res.kind, "reply")
        self.assertEqual(rec["result_kind"], "reply")
        self.assertEqual(rec["trace_id"], "tr-9")
        self.assertEqual(rec["tool_trace"], [{"tool": "balance", "ok": True, "error": None}])
        self.assertGreaterEqual(rec["elapsed_ms"], 0)

    def test_exception_path_records_crash(self):
        from services.line_binding import line_agent_bridge as bridge

        kinds = []
        with (
            patch("core.feature_flags.agent_enabled_for", return_value=True),
            patch("core.feature_flags.agent_write_enabled_for", return_value=False),
            patch("services.agent.confirm_machine.try_resume", return_value=False),
            patch("services.agent.recon_intake.try_text", return_value=False),
            patch("services.agent.loop.handle_turn", side_effect=RuntimeError("boom")),
            patch(
                "services.agent.turn_log.record",
                lambda **kw: kinds.append(kw["result_kind"]),
            ),
        ):
            res = bridge.try_agent_turn(
                {"id": "u1", "tenant_id": "t1"}, "hi", "th", "t1", 1, "U1", []
            )
        self.assertEqual(res.kind, "crash")
        self.assertEqual(kinds, ["crash"])


if __name__ == "__main__":
    unittest.main()

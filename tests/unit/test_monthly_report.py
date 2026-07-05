# -*- coding: utf-8 -*-
"""月报卡(monthly_report · W4-1)契约。

花钱面铁六条:① 窗口外(4 日起)零发送;② 退订标记跳过;③ 闸关跳过;④ 台账
去重每用户每期恰一条;⑤ 上月零单不发(没数字的月报是噪音);⑥ 卡带看明细 uri +
退订 postback,退订回执幂等。
"""

import unittest
from contextlib import contextmanager
from datetime import date
from unittest.mock import MagicMock, patch

import core.db  # noqa: F401  # 先于 notification 域导入,防 dal_reexports 单头循环
from services.notification import monthly_report


@contextmanager
def _cm(cur):
    yield cur


def _rows(**over):
    row = {
        "user_id": "u1",
        "line_user_id": "U1",
        "tenant_id": "t1",
        "preferred_lang": "th",
        "monthly_report_opt_out": False,
    }
    row.update(over)
    return [row]


def _patched(rows, *, flag=True, dup=False, stats=None, pushed=None, logged=None):
    pushed = pushed if pushed is not None else []
    logged = logged if logged is not None else []
    return (
        patch.object(monthly_report, "_recipients", return_value=rows),
        patch("core.feature_flags.agent_monthly_report_enabled_for", return_value=flag),
        patch.object(monthly_report, "_already_sent", return_value=dup),
        patch.object(monthly_report, "_month_stats", return_value=stats),
        patch("services.expense.line_lang.card_lang", return_value="th"),
        patch(
            "services.line_binding.line_reply.push_messages_context",
            lambda luid, msgs, **k: pushed.append(msgs) or True,
        ),
        patch(
            "services.notification.store.log_notification",
            lambda *a, **k: logged.append(a),
        ),
    )


_STATS = {"n": 42, "total": 58240.0, "prior": 52000.0, "cats": ["วัตถุดิบ", "ค่าขนส่ง"]}


class TestSend(unittest.TestCase):
    def _send(self, rows=None, *, day=2, **kw):
        pushed, logged = [], []
        ps = _patched(rows if rows is not None else _rows(), pushed=pushed, logged=logged, **kw)
        with ps[0], ps[1], ps[2], ps[3], ps[4], ps[5], ps[6]:
            n = monthly_report.send_monthly_reports(date(2026, 7, day))
        return n, pushed, logged

    def test_outside_window_sends_nothing(self):
        n, pushed, _ = self._send(day=4, stats=_STATS)
        self.assertEqual((n, pushed), (0, []))

    def test_opted_out_skipped(self):
        n, pushed, _ = self._send(_rows(monthly_report_opt_out=True), stats=_STATS)
        self.assertEqual((n, pushed), (0, []))

    def test_gate_closed_skipped(self):
        n, pushed, _ = self._send(flag=False, stats=_STATS)
        self.assertEqual((n, pushed), (0, []))

    def test_dedup_skipped(self):
        n, pushed, _ = self._send(dup=True, stats=_STATS)
        self.assertEqual((n, pushed), (0, []))

    def test_zero_docs_not_sent(self):
        n, pushed, _ = self._send(stats={"n": 0, "total": 0.0, "prior": 0.0})
        self.assertEqual((n, pushed), (0, []))

    def test_sends_card_with_detail_and_unsub(self):
        n, pushed, logged = self._send(stats=_STATS)
        self.assertEqual(n, 1)
        tpl = pushed[0][0]["template"]
        self.assertIn("42", tpl["text"])
        self.assertIn("58,240", tpl["text"])
        kinds = [a["type"] for a in tpl["actions"]]
        self.assertEqual(kinds, ["uri", "postback"])
        self.assertIn("mrep_unsub", tpl["actions"][1]["data"])
        self.assertEqual(logged[0][3], monthly_report.TEMPLATE_CODE)

    def test_delta_positive_in_text(self):
        _, pushed, _ = self._send(stats=_STATS)
        self.assertIn("+12%", pushed[0][0]["template"]["text"])


class TestUnsub(unittest.TestCase):
    def test_sets_flag_and_confirms(self):
        says = []
        with (
            patch.object(monthly_report, "set_opt_out", return_value=True) as so,
            patch(
                "services.line_binding.line_reply.reply_text_context",
                lambda rt, body, **k: says.append(body),
            ),
        ):
            monthly_report.handle_unsub({"line_user_id": "U1", "tenant_id": "t1"}, "rt", "th")
        so.assert_called_once_with("U1", True)
        self.assertIn(says[0], monthly_report._UNSUB_OK.values())

    def test_opt_out_write_failure_still_replies(self):
        says = []
        with (
            patch.object(monthly_report, "set_opt_out", side_effect=RuntimeError("db")),
            patch(
                "services.line_binding.line_reply.reply_text_context",
                lambda rt, body, **k: says.append(body),
            ),
        ):
            monthly_report.handle_unsub({"line_user_id": "U1", "tenant_id": None}, "rt", "zh")
        self.assertTrue(says)

    def test_missing_column_heals_on_set(self):
        calls = []

        def flaky(**k):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError('column "monthly_report_opt_out" does not exist')
            cur = MagicMock()
            cur.rowcount = 1
            return _cm(cur)

        with (
            patch("core.db.get_cursor", flaky),
            patch.object(monthly_report, "_ensure_opt_out_column") as ens,
        ):
            ok = monthly_report.set_opt_out("U1", True)
        ens.assert_called_once()
        self.assertTrue(ok)


class TestPeriods(unittest.TestCase):
    def test_prev_periods_cross_year(self):
        self.assertEqual(monthly_report._prev_period(date(2026, 1, 2)), "2025-12")
        self.assertEqual(monthly_report._prev_prev_period(date(2026, 1, 2)), "2025-11")
        self.assertEqual(monthly_report._prev_prev_period(date(2026, 2, 2)), "2025-12")
        self.assertEqual(monthly_report._prev_period(date(2026, 7, 1)), "2026-06")
        self.assertEqual(monthly_report._prev_prev_period(date(2026, 7, 1)), "2026-05")


if __name__ == "__main__":
    unittest.main()

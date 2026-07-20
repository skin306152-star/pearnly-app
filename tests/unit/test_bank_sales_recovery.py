# -*- coding: utf-8 -*-
"""银行倒推大脑失败批自动收尾守门(services/workorder/bank_sales_recovery.py · D6-4)。

锁定:① 候选 SQL 只认 review/stuck 且「最近终态是 failed」(failed 事件晚于最新 finished);
② 自动重试次数只数 trigger=recovery 的 failed 事件(manual 不计);③ 逐单:pending>0 + 预算
未耗尽 + 租约抢到才起后台重跑;④ finished/pending 空/预算耗尽/租约被占均不重跑;⑤ 闸关跳过。
"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from unittest import mock

from services.workorder import bank_sales_recovery as recovery
from services.workorder.steps import bank_sales_brain as brain
from tests.unit.test_workorder_store import FakeCursor


def _failed(eid, trigger):
    return {"id": eid, "event_type": brain.EVT_BRAIN_FAILED, "payload": {"trigger": trigger}}


def _finished(eid):
    return {"id": eid, "event_type": brain.EVT_BRAIN_FINISHED, "payload": {"trigger": "manual"}}


class AutoRetryCountTests(unittest.TestCase):
    def test_counts_only_recovery_triggered_failures(self):
        events = [
            _failed(1, brain.TRIGGER_MANUAL),
            _failed(2, brain.TRIGGER_RECOVERY),
            _finished(3),
            _failed(4, brain.TRIGGER_RECOVERY),
        ]
        self.assertEqual(recovery.auto_retry_count(events), 2)

    def test_zero_when_only_manual(self):
        self.assertEqual(recovery.auto_retry_count([_failed(1, brain.TRIGGER_MANUAL)]), 0)


class ResumeOneTests(unittest.TestCase):
    def setUp(self):
        self._events = [_failed(9, brain.TRIGGER_MANUAL)]

    @contextmanager
    def _patched(self, *, pending, retry, owner, events=None):
        thread = mock.MagicMock()

        @contextmanager
        def fake_cursor(commit=False):
            yield object()

        with (
            mock.patch.object(recovery.db, "get_cursor", fake_cursor),
            mock.patch.object(recovery.store, "list_events", return_value=events or self._events),
            mock.patch.object(recovery.suggest, "pending_rows", return_value=pending),
            mock.patch.object(recovery, "auto_retry_count", return_value=retry),
            mock.patch.object(recovery.brain, "begin_run", return_value=owner) as begin_run,
            mock.patch.object(recovery.threading, "Thread", return_value=thread) as th,
        ):
            yield begin_run, th, thread

    def test_resumes_when_pending_and_budget_and_lease(self):
        with self._patched(pending=[{}, {}], retry=1, owner="owner-x") as (begin_run, th, thread):
            self.assertTrue(recovery._resume_one("t-1", "wo-1"))
        begin_run.assert_called_once_with("t-1", "wo-1", 2)
        kwargs = th.call_args.kwargs["kwargs"]
        self.assertEqual(kwargs["trigger"], brain.TRIGGER_RECOVERY)
        self.assertEqual(kwargs["lease_owner"], "owner-x")
        self.assertTrue(kwargs["claimed"])
        thread.start.assert_called_once()

    def test_skips_when_no_pending_rows(self):
        with self._patched(pending=[], retry=0, owner="owner-x") as (begin_run, th, _):
            self.assertFalse(recovery._resume_one("t-1", "wo-1"))
        begin_run.assert_not_called()

    def test_skips_when_retry_budget_exhausted(self):
        with self._patched(pending=[{}], retry=recovery.AUTO_RETRY_LIMIT, owner="o") as (bg, th, _):
            self.assertFalse(recovery._resume_one("t-1", "wo-1"))
        bg.assert_not_called()

    def test_skips_when_lease_taken(self):
        with self._patched(pending=[{}], retry=0, owner=None) as (begin_run, th, _):
            self.assertFalse(recovery._resume_one("t-1", "wo-1"))
        begin_run.assert_called_once()
        th.assert_not_called()


class ScanAndResumeTests(unittest.TestCase):
    @contextmanager
    def _patched(self, *, candidates, flag_on, resume_ret=True):
        with (
            mock.patch.object(recovery.store, "ensure_runtime"),
            mock.patch.object(recovery, "_find_candidates", return_value=candidates),
            mock.patch.object(
                recovery.feature_flags,
                "pearnly_ai_bank_sales_suggest_enabled_for",
                return_value=flag_on,
            ),
            mock.patch.object(recovery, "_resume_one", return_value=resume_ret) as resume,
        ):

            @contextmanager
            def fake_cursor(commit=False):
                yield object()

            with mock.patch.object(recovery.db, "get_cursor", fake_cursor):
                yield resume

    def test_resumes_each_gated_candidate(self):
        cands = [
            {"tenant_id": "t-1", "work_order_id": "wo-1"},
            {"tenant_id": "t-2", "work_order_id": "wo-2"},
        ]
        with self._patched(candidates=cands, flag_on=True) as resume:
            self.assertEqual(recovery.scan_and_resume(), 2)
        self.assertEqual(resume.call_count, 2)

    def test_skips_when_flag_off(self):
        cands = [{"tenant_id": "t-1", "work_order_id": "wo-1"}]
        with self._patched(candidates=cands, flag_on=False) as resume:
            self.assertEqual(recovery.scan_and_resume(), 0)
        resume.assert_not_called()


class FindCandidatesSqlTests(unittest.TestCase):
    """finished 后不触发 = SQL 只选「failed 事件 id 大于最新 finished 事件 id」的 review/stuck 单。"""

    def test_query_shape_excludes_finished_and_filters_status(self):
        cur = FakeCursor([])
        recovery._find_candidates(cur, limit=20)
        sql, params = cur.calls[0]
        self.assertIn("work_order_events", sql)
        self.assertIn("wo.status IN", sql)
        self.assertIn("e.id > COALESCE(", sql)  # failed 晚于最新 finished
        self.assertEqual(
            params,
            (
                brain.EVT_BRAIN_FAILED,
                "review",
                "stuck",
                brain.EVT_BRAIN_FINISHED,
                20,
            ),
        )


if __name__ == "__main__":
    unittest.main()

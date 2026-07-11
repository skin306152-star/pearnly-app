# -*- coding: utf-8 -*-
"""LINE 待问客户池 · 周期催办 + 关闭清扫(services/line_binding/line_client_dunning)
· D2-S6 契约(主窗修正 1②)。

钉死:①3 天内不催/超 3 天起催 ②同批同周连跑两次 tick 只发一封(already_sent 去重)
③窗口外/闸关 → 0 发 0 副作用 ④票有后置裁决 → 清成 resolved_internally 且不再被催
(先扫后催的调用顺序)⑤工单 archive(状态词 import engine.STATUS_ARCHIVE,非字面量)
→ 问题 cancelled ⑥某批发送抛异常不影响下一批 ⑦发送失败落台账 failed。
"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_dunning as dunning
from services.workorder import engine as wo_engine

_TENANT = "5b7f9b2a-11a1-4a1a-9a1a-0f0f0f0f0f01"
_WORK_ORDER = "9f0f9b2a-22a2-4a2a-9a2a-0f0f0f0f0f02"
_ITEM = "aa0f9b2a-33a3-4a3a-9a3a-0f0f0f0f0f03"


def _cm(value):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=value)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _question(qid=1, status=vocab.PENDING, **overrides):
    base = {
        "id": qid,
        "tenant_id": _TENANT,
        "workspace_client_id": 84,
        "work_order_id": _WORK_ORDER,
        "item_id": _ITEM,
        "period": "2026-07",
        "question_type": vocab.QUESTION_DIRECTION,
        "question_payload": {"supplier": "ร้าน A", "invno": "INV-001"},
        "status": status,
        "batch_id": "b1c1e1a1-44a4-4a4a-9a4a-0f0f0f0f0f04",
        "answer_raw": None,
        "resolution": None,
        "created_by": "user:1",
        "created_at": datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        "sent_at": datetime(2026, 7, 1, 9, 5, tzinfo=timezone.utc),
        "answered_at": None,
        "closed_at": None,
        "updated_at": None,
    }
    base.update(overrides)
    return base


class WindowTests(unittest.TestCase):
    def test_window_boundaries(self):
        self.assertFalse(dunning._in_window(datetime(2026, 7, 11, 9, 59)))
        self.assertTrue(dunning._in_window(datetime(2026, 7, 11, 10, 0)))
        self.assertTrue(dunning._in_window(datetime(2026, 7, 11, 17, 59)))
        self.assertFalse(dunning._in_window(datetime(2026, 7, 11, 18, 0)))


class SweepOneTests(unittest.TestCase):
    """规则 1(后置裁决)/ 规则 2(工单归档)的单条判定。"""

    def setUp(self):
        patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True).start()
        patch("core.db.get_cursor", return_value=_cm(MagicMock())).start()
        self.transition = patch("services.line_binding.line_client_pool_store.transition").start()
        self.addCleanup(patch.stopall)

    def test_disabled_tenant_touches_nothing(self):
        """断言③(逐 tenant 粒度):闸关 → 连工单读侧都不碰,transition 未调用。"""
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=False),
            patch("core.db.get_cursor") as get_cursor,
        ):
            out = dunning._sweep_one(_question(), datetime(2026, 7, 11, 12))
        self.assertFalse(out)
        get_cursor.assert_not_called()
        self.transition.assert_not_called()

    def test_decided_after_question_created_closes_resolved_internally(self):
        """断言④:该票在问题创建之后已有人工裁决 → resolved_internally。"""
        decided_at = _question()["created_at"] + timedelta(hours=2)
        with (
            patch(
                "services.workorder.store.get_work_order",
                return_value={"status": wo_engine.STATUS_REVIEW},
            ),
            patch("services.workorder.store.list_events", return_value=[]),
            patch(
                "services.workorder.evidence.replay_items_by_type",
                return_value={_ITEM: {"at": decided_at, "payload": {}}},
            ),
        ):
            out = dunning._sweep_one(_question(status=vocab.PENDING), datetime(2026, 7, 11, 12))
        self.assertTrue(out)
        self.transition.assert_called_once_with(_TENANT, 1, vocab.RESOLVED_INTERNALLY)

    def test_decided_after_on_manual_review_falls_back_to_cancelled(self):
        """MANUAL_REVIEW 无法直转 resolved_internally(client_pool_vocab.LEGAL_TRANSITIONS
        不许,S1 契约钉死),退而求其次转 cancelled,同样封口不再被催/复核。"""
        decided_at = _question()["created_at"] + timedelta(hours=2)
        with (
            patch(
                "services.workorder.store.get_work_order",
                return_value={"status": wo_engine.STATUS_REVIEW},
            ),
            patch("services.workorder.store.list_events", return_value=[]),
            patch(
                "services.workorder.evidence.replay_items_by_type",
                return_value={_ITEM: {"at": decided_at, "payload": {}}},
            ),
        ):
            out = dunning._sweep_one(
                _question(status=vocab.MANUAL_REVIEW), datetime(2026, 7, 11, 12)
            )
        self.assertTrue(out)
        self.transition.assert_called_once_with(_TENANT, 1, vocab.CANCELLED)

    def test_decision_before_question_created_does_not_close(self):
        """裁决早于问题创建(反常序)→ 不是"后置"裁决,不关闭。"""
        decided_at = _question()["created_at"] - timedelta(hours=2)
        with (
            patch(
                "services.workorder.store.get_work_order",
                return_value={"status": wo_engine.STATUS_REVIEW},
            ),
            patch("services.workorder.store.list_events", return_value=[]),
            patch(
                "services.workorder.evidence.replay_items_by_type",
                return_value={_ITEM: {"at": decided_at, "payload": {}}},
            ),
        ):
            out = dunning._sweep_one(_question(), datetime(2026, 7, 11, 12))
        self.assertFalse(out)
        self.transition.assert_not_called()

    def test_no_decision_and_not_archived_does_not_close(self):
        with (
            patch(
                "services.workorder.store.get_work_order",
                return_value={"status": wo_engine.STATUS_REVIEW},
            ),
            patch("services.workorder.store.list_events", return_value=[]),
            patch("services.workorder.evidence.replay_items_by_type", return_value={}),
        ):
            out = dunning._sweep_one(_question(), datetime(2026, 7, 11, 12))
        self.assertFalse(out)
        self.transition.assert_not_called()

    def test_archived_work_order_closes_cancelled(self):
        """断言⑤:工单已 archive(状态词 import engine.STATUS_ARCHIVE,非字面量)→ cancelled。"""
        with patch(
            "services.workorder.store.get_work_order",
            return_value={"status": wo_engine.STATUS_ARCHIVE},
        ):
            out = dunning._sweep_one(
                _question(status=vocab.MANUAL_REVIEW), datetime(2026, 7, 11, 12)
            )
        self.assertTrue(out)
        self.transition.assert_called_once_with(_TENANT, 1, vocab.CANCELLED)

    def test_missing_work_order_does_not_close(self):
        with patch("services.workorder.store.get_work_order", return_value=None):
            out = dunning._sweep_one(_question(), datetime(2026, 7, 11, 12))
        self.assertFalse(out)
        self.transition.assert_not_called()

    def test_concurrent_close_is_not_double_counted(self):
        """latest-wins 竞态:transition 期间已被别处并发关闭 → IllegalTransitionError 静默,
        本条不计入本轮新关闭。"""
        from services.line_binding import line_client_pool_store as pool_store

        self.transition.side_effect = pool_store.IllegalTransitionError(
            vocab.RESOLVED_INTERNALLY, vocab.CANCELLED
        )
        with patch(
            "services.workorder.store.get_work_order",
            return_value={"status": wo_engine.STATUS_ARCHIVE},
        ):
            out = dunning._sweep_one(_question(), datetime(2026, 7, 11, 12))
        self.assertFalse(out)


class SweepActiveQuestionsTests(unittest.TestCase):
    def test_one_failing_row_does_not_block_others(self):
        """逐条 try/except 不连坐:第 1 条抛异常,第 2 条仍正常关闭并计数。"""
        rows = [_question(qid=1), _question(qid=2)]
        with (
            patch(
                "services.line_binding.line_client_pool_store.list_active_all",
                return_value=rows,
            ),
            patch.object(dunning, "_sweep_one", side_effect=[RuntimeError("boom"), True]),
        ):
            closed = dunning._sweep_active_questions(datetime(2026, 7, 11, 12))
        self.assertEqual(closed, 1)


class ChaseOneBatchTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 11, 12, tzinfo=timezone.utc)
        self.contact = {
            "tenant_id": _TENANT,
            "workspace_client_id": 84,
            "line_user_id": "U163",
            "preferred_lang": "th",
        }
        patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True).start()
        patch("services.notification.store.already_sent", return_value=False).start()
        patch(
            "services.line_binding.line_client_contact.get_contact", return_value=self.contact
        ).start()
        patch("services.expense.line_lang.card_lang", return_value="th").start()
        self.push = patch(
            "services.line_binding.line_reply.push_text_context", return_value=True
        ).start()
        self.log = patch("services.notification.store.log_notification").start()
        self.addCleanup(patch.stopall)

    def _batch_id(self):
        return "b1c1e1a1-44a4-4a4a-9a4a-0f0f0f0f0f04"

    def test_disabled_tenant_skips_with_zero_side_effects(self):
        """断言③:闸关 → 结构化 skip,不查台账/联系人/不推送。"""
        with patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=False):
            out = dunning._chase_one_batch(_TENANT, 84, self._batch_id(), [_question()], self.now)
        self.assertEqual(out, "skip:disabled")
        self.push.assert_not_called()
        self.log.assert_not_called()

    def test_already_sent_this_iso_week_skips_no_resend(self):
        """断言②:同批同周去重 → 不重发,event_ref 含 batch_id + ISO 周。"""
        with patch("services.notification.store.already_sent", return_value=True) as sent_fn:
            out = dunning._chase_one_batch(_TENANT, 84, self._batch_id(), [_question()], self.now)
        self.assertEqual(out, "skip:already_sent")
        self.push.assert_not_called()
        iso_year, iso_week, _ = self.now.isocalendar()
        expected_ref = f"{self._batch_id()}:{iso_year}-W{iso_week:02d}"
        self.assertEqual(sent_fn.call_args.args[3], expected_ref)

    def test_not_bound_skips_without_push(self):
        with patch("services.line_binding.line_client_contact.get_contact", return_value=None):
            out = dunning._chase_one_batch(_TENANT, 84, self._batch_id(), [_question()], self.now)
        self.assertEqual(out, "skip:not_bound")
        self.push.assert_not_called()

    def test_success_logs_sent(self):
        out = dunning._chase_one_batch(_TENANT, 84, self._batch_id(), [_question()], self.now)
        self.assertEqual(out, "sent")
        self.assertEqual(self.log.call_args.args[3], dunning.TEMPLATE_CODE)
        self.assertEqual(self.log.call_args.args[7], "sent")
        self.assertIn("1", self.push.call_args.args[1])  # n=1 融进文案

    def test_push_returns_false_logs_failed(self):
        """断言⑦:push 结构化返回失败 → 台账落 failed。"""
        self.push.return_value = False
        out = dunning._chase_one_batch(_TENANT, 84, self._batch_id(), [_question()], self.now)
        self.assertEqual(out, "failed")
        self.assertEqual(self.log.call_args.args[7], "failed")

    def test_push_raises_logs_failed(self):
        """断言⑦变体:push 抛异常同样按失败落台账,不向上穿透。"""
        self.push.side_effect = RuntimeError("LINE API down")
        out = dunning._chase_one_batch(_TENANT, 84, self._batch_id(), [_question()], self.now)
        self.assertEqual(out, "failed")
        self.assertEqual(self.log.call_args.args[7], "failed")


class ChasePendingTests(unittest.TestCase):
    def test_threshold_is_three_days_before_now(self):
        """断言①:3 天内不催、超 3 天起催——由 store.list_pending_for_dunning(sent_before=
        now-3天) 承担 SQL 过滤,这里钉死调用方传对了阈值。"""
        now = datetime(2026, 7, 11, 12, tzinfo=timezone.utc)
        with patch(
            "services.line_binding.line_client_pool_store.list_pending_for_dunning",
            return_value=[],
        ) as list_fn:
            dunning._chase_pending(now)
        list_fn.assert_called_once_with(sent_before=now - timedelta(days=3))

    def test_one_batch_exception_does_not_block_next_batch(self):
        """断言⑥:批 1 抛异常,批 2 仍正常处理并计数。"""
        rows = [
            _question(qid=1, batch_id="batch-1"),
            _question(qid=2, batch_id="batch-2"),
        ]
        with (
            patch(
                "services.line_binding.line_client_pool_store.list_pending_for_dunning",
                return_value=rows,
            ),
            patch.object(
                dunning, "_chase_one_batch", side_effect=[RuntimeError("boom"), "sent"]
            ) as chase_fn,
        ):
            sent, failed = dunning._chase_pending(datetime(2026, 7, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(sent, 1)
        self.assertEqual(failed, 0)
        self.assertEqual(chase_fn.call_count, 2)

    def test_row_missing_batch_id_is_skipped(self):
        rows = [_question(qid=1, batch_id=None)]
        with (
            patch(
                "services.line_binding.line_client_pool_store.list_pending_for_dunning",
                return_value=rows,
            ),
            patch.object(dunning, "_chase_one_batch") as chase_fn,
        ):
            sent, failed = dunning._chase_pending(datetime(2026, 7, 11, 12, tzinfo=timezone.utc))
        self.assertEqual((sent, failed), (0, 0))
        chase_fn.assert_not_called()


class RunDunningAndSweepTests(unittest.TestCase):
    def test_outside_window_zero_side_effects(self):
        """断言③:窗口外 → 不碰任何 store 读口(0 副作用,不止 0 发送)。"""
        with (
            patch("services.line_binding.line_client_pool_store.list_active_all") as list_active,
            patch(
                "services.line_binding.line_client_pool_store.list_pending_for_dunning"
            ) as list_pending,
        ):
            out = dunning.run_dunning_and_sweep(datetime(2026, 7, 11, 3, tzinfo=timezone.utc))
        self.assertEqual(out, {"closed": 0, "sent": 0, "failed": 0})
        list_active.assert_not_called()
        list_pending.assert_not_called()

    def test_sweep_runs_before_chase(self):
        """先扫后催:清扫顺带把已裁决的问题关掉,催办才不会追一个已处理的问题。"""
        order = []
        with (
            patch.object(
                dunning,
                "_sweep_active_questions",
                side_effect=lambda now: order.append("sweep") or 1,
            ),
            patch.object(
                dunning,
                "_chase_pending",
                side_effect=lambda now: order.append("chase") or (0, 0),
            ),
        ):
            out = dunning.run_dunning_and_sweep(datetime(2026, 7, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(order, ["sweep", "chase"])
        self.assertEqual(out["closed"], 1)


class RunTickTests(unittest.TestCase):
    def setUp(self):
        dunning._last_run = 0.0
        self.addCleanup(setattr, dunning, "_last_run", 0.0)

    def test_process_throttle_blocks_rapid_reruns(self):
        import asyncio
        import time

        dunning._last_run = time.monotonic()
        with patch.object(dunning, "run_dunning_and_sweep") as core:
            out = asyncio.run(dunning.run_tick())
        self.assertEqual(out, 0)
        core.assert_not_called()

    def test_outside_window_returns_zero(self):
        import asyncio

        with (
            patch(
                "services.sales.dates.bangkok_now",
                return_value=datetime(2026, 7, 11, 3, tzinfo=timezone.utc),
            ),
            patch.object(dunning, "run_dunning_and_sweep") as core,
        ):
            out = asyncio.run(dunning.run_tick())
        self.assertEqual(out, 0)
        core.assert_not_called()

    def test_in_window_runs_core_and_returns_sent_count(self):
        import asyncio

        with (
            patch(
                "services.sales.dates.bangkok_now",
                return_value=datetime(2026, 7, 11, 12, tzinfo=timezone.utc),
            ),
            patch.object(
                dunning,
                "run_dunning_and_sweep",
                return_value={"closed": 2, "sent": 3, "failed": 1},
            ),
        ):
            out = asyncio.run(dunning.run_tick())
        self.assertEqual(out, 3)


if __name__ == "__main__":
    unittest.main()

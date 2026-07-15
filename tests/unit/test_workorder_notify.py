# -*- coding: utf-8 -*-
"""工单跑批收尾通知会计守门(services/notification/workorder_notify.py · IN-0c)。

脱库:注入假游标(按调用顺序回放 fetchone),验证①闸关零动作(零查库零发送零台账)
②无 LINE 绑定 log 后静默跳过③跑完发 done 模板④终态 stuck 发 stuck 模板(缺料/异常两态
不同原因短语)⑤同一次 run 重复调用靠 notification_logs 去重台账恰发一条⑥重跑(新
run_event_id)可再发⑦推送/查库内部抛错不冒泡出 notify_run_outcome⑧四语文案不带金额
数字(LINE 是外部通道的钱数边界)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.notification import workorder_notify as wn
from services.workorder import engine

_TENANT = "t-1"
_WOID = "wo-1"


def _order(status, *, current_step=None, workspace_client_id=1, period="2569-06"):
    return {
        "tenant_id": _TENANT,
        "id": _WOID,
        "status": status,
        "current_step": current_step,
        "workspace_client_id": workspace_client_id,
        "period": period,
    }


class _FakeCursor:
    """按 execute() 调用顺序回放预置 fetchone() 结果(不断言具体 SQL,只驱动分支)。"""

    def __init__(self, results):
        self._results = list(results)
        self.execute_count = 0

    def execute(self, *_a, **_k):
        self.execute_count += 1

    def fetchone(self):
        return self._results.pop(0) if self._results else None


class _FakeCM:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *_a):
        return False


def _patch_cursor(results):
    cur = _FakeCursor(results)
    return mock.patch("core.db.get_cursor", return_value=_FakeCM(cur)), cur


class NotifyRunOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(mock.patch.stopall)
        self.gate = mock.patch(
            "core.feature_flags.pearnly_ai_run_notify_enabled_for", return_value=True
        ).start()
        self.log = mock.patch("services.notification.store.log_notification").start()
        self.already_sent = mock.patch(
            "services.notification.store.already_sent", return_value=False
        ).start()
        self.push = mock.patch(
            "services.line_binding.line_reply.push_text_context", return_value=True
        ).start()
        self.card_lang = mock.patch(
            "services.expense.line_lang.card_lang", return_value="zh"
        ).start()

    def test_gate_off_is_zero_action(self):
        self.gate.return_value = False
        db_patch = mock.patch("core.db.get_cursor", side_effect=AssertionError("闸关不该查库"))
        db_patch.start()
        wn.notify_run_outcome(_order(engine.STATUS_REVIEW), 10)
        self.log.assert_not_called()
        self.push.assert_not_called()
        self.already_sent.assert_not_called()

    def test_no_binding_logs_skip_and_sends_nothing(self):
        patch_ctx, _cur = _patch_cursor(
            [
                {"actor": "user:u1"},  # requester
                None,  # line_binding: 无绑定
                {"name": "ACME"},  # client_name
            ]
        )
        with patch_ctx:
            wn.notify_run_outcome(_order(engine.STATUS_REVIEW), 10)
        self.push.assert_not_called()
        self.log.assert_called_once()
        args = self.log.call_args.args
        self.assertEqual(args[3], wn.TEMPLATE_DONE)
        self.assertIsNone(args[6])  # line_user_id
        self.assertEqual(args[7], "skipped")

    def test_non_human_actor_has_no_notify_target(self):
        # reaper 自动续跑 / LINE 客户答题自驱都不是会计账号,无通知对象、连日志都不写。
        patch_ctx, _cur = _patch_cursor([{"actor": "system:reaper"}])
        with patch_ctx:
            wn.notify_run_outcome(_order(engine.STATUS_REVIEW), 10)
        self.log.assert_not_called()
        self.push.assert_not_called()

    def test_done_status_sends_done_template(self):
        patch_ctx, _cur = _patch_cursor(
            [
                {"actor": "user:u1"},
                {"line_user_id": "Uabc", "preferred_lang": "zh"},
                {"name": "ACME"},
            ]
        )
        with patch_ctx:
            wn.notify_run_outcome(_order(engine.STATUS_REVIEW, period="2569-06"), 10)
        self.push.assert_called_once()
        text = self.push.call_args.args[1]
        self.assertIn("ACME", text)
        self.assertIn("2569-06", text)
        self.assertEqual(self.log.call_args.args[3], wn.TEMPLATE_DONE)
        self.assertEqual(self.log.call_args.args[6], "Uabc")  # line_user_id
        self.assertEqual(self.log.call_args.args[7], "sent")

    def test_stuck_status_needs_reason(self):
        patch_ctx, _cur = _patch_cursor(
            [
                {"actor": "user:u1"},
                {"line_user_id": "Uabc", "preferred_lang": "zh"},
                {"name": "ACME"},
                {"event_type": engine.EVT_NEEDS},
            ]
        )
        with patch_ctx:
            wn.notify_run_outcome(_order(engine.STATUS_STUCK, current_step="reconcile"), 11)
        text = self.push.call_args.args[1]
        self.assertIn("缺料", text)
        self.assertEqual(self.log.call_args.args[3], wn.TEMPLATE_STUCK)

    def test_stuck_status_internal_error_reason(self):
        patch_ctx, _cur = _patch_cursor(
            [
                {"actor": "user:u1"},
                {"line_user_id": "Uabc", "preferred_lang": "zh"},
                {"name": "ACME"},
                {"event_type": engine.EVT_STUCK},
            ]
        )
        with patch_ctx:
            wn.notify_run_outcome(_order(engine.STATUS_STUCK, current_step="package"), 12)
        text = self.push.call_args.args[1]
        self.assertIn("异常", text)

    def test_duplicate_call_same_run_sends_once(self):
        # 同一次 run(同 run_event_id → 同 event_ref)恰发一条:第二次 already_sent 命中即跳过。
        self.already_sent.side_effect = [False, True]
        for _ in range(2):
            patch_ctx, _cur = _patch_cursor(
                [
                    {"actor": "user:u1"},
                    {"line_user_id": "Uabc", "preferred_lang": "zh"},
                    {"name": "ACME"},
                ]
            )
            with patch_ctx:
                wn.notify_run_outcome(_order(engine.STATUS_REVIEW), 10)
        self.assertEqual(self.push.call_count, 1)
        self.assertEqual(self.log.call_count, 1)

    def test_rerun_new_run_event_id_can_resend(self):
        # 重跑产生新 run_event_id → 新 event_ref → already_sent 各自判 False → 都能发。
        for run_event_id in (10, 20):
            patch_ctx, _cur = _patch_cursor(
                [
                    {"actor": "user:u1"},
                    {"line_user_id": "Uabc", "preferred_lang": "zh"},
                    {"name": "ACME"},
                ]
            )
            with patch_ctx:
                wn.notify_run_outcome(_order(engine.STATUS_REVIEW), run_event_id)
        self.assertEqual(self.push.call_count, 2)
        refs = {c.args[3] for c in self.already_sent.call_args_list}
        self.assertEqual(refs, {f"{_WOID}:10", f"{_WOID}:20"})

    def test_internal_exception_does_not_raise(self):
        self.push.side_effect = RuntimeError("LINE 挂了")
        patch_ctx, _cur = _patch_cursor(
            [
                {"actor": "user:u1"},
                {"line_user_id": "Uabc", "preferred_lang": "zh"},
                {"name": "ACME"},
            ]
        )
        with patch_ctx:
            wn.notify_run_outcome(_order(engine.STATUS_REVIEW), 10)  # 不许抛出

    def test_query_failure_does_not_raise(self):
        with mock.patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            wn.notify_run_outcome(_order(engine.STATUS_REVIEW), 10)  # 不许抛出
        self.push.assert_not_called()


class CopyLocalizationTests(unittest.TestCase):
    """四语文案不带金额/税号数字(LINE 是外部通道,钱数只在站内看)。"""

    _MONEY_PATTERNS = ("฿", ",000", ".00")

    def test_done_copy_has_no_money_pattern(self):
        for lang, tpl in wn._COPY_DONE.items():
            text = tpl.format(client="ACME", period="2569-06")
            for pat in self._MONEY_PATTERNS:
                self.assertNotIn(pat, text, msg=f"{lang} done 文案疑似带金额: {text}")

    def test_stuck_copy_has_no_money_pattern(self):
        for lang in ("zh", "th", "en", "ja"):
            for kind in ("needs", "stuck"):
                reason = wn._reason_phrase(lang, "reconcile", kind)
                text = wn._COPY_STUCK[lang].format(client="ACME", period="2569-06", reason=reason)
                for pat in self._MONEY_PATTERNS:
                    self.assertNotIn(pat, text, msg=f"{lang}/{kind} stuck 文案疑似带金额: {text}")
                self.assertFalse(
                    any(ch.isdigit() for ch in reason),
                    msg=f"{lang}/{kind} 原因短语带数字: {reason}",
                )


if __name__ == "__main__":
    unittest.main()

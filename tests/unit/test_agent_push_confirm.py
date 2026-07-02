# -*- coding: utf-8 -*-
"""推 ERP confirm-first 全链(备料 → 确认卡 → postback 消费 → 执行 → 结果诚实)。

钱路红线:工具备料绝不执行推送;未点确认按钮 = 零推送调用;三层幂等
(nonce 一次性 / has_recent_successful_push / erp_push_logs 唯一源);失败绝不谎报成功。
"""

import json
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from services.agent import push_confirm
from services.agent.contracts import AgentContext
from services.agent.executor import AgentToolset
from services.line_binding import line_postback

_CTX = AgentContext(user={"id": "u1", "tenant_id": "t1", "plan": "pro"}, tenant_id="t1")
_BOUND = {"id": "u1", "tenant_id": "t1", "plan": "pro", "line_user_id": "U1"}


@contextmanager
def _fake_cursor(*a, **k):
    yield MagicMock()


def _perms(on=True):
    return patch(
        "services.agent.executor._plan_permissions",
        return_value={"can_push_erp": on, "can_view_history": True, "history_retention_days": 365},
    )


class TestPrepare(unittest.TestCase):
    """executor.push_to_erp 只备料:任何分支都不许触发真推送。"""

    def setUp(self):
        patch("core.db.get_visible_client_ids_for_user", return_value=None).start()
        self.addCleanup(patch.stopall)

    def _hist(self, n=1):
        return {
            "items": [
                {"id": f"h{i}", "seller_name": "7-11", "total_amount": 120, "invoice_no": f"IV{i}"}
                for i in range(n)
            ],
            "total": n,
        }

    def test_prepare_ok_payload(self):
        with (
            _perms(),
            patch("core.db.list_ocr_history", return_value=self._hist()),
            patch(
                "core.db.list_erp_endpoints",
                return_value=[{"id": "e1", "name": "MR.ERP", "enabled": True}],
            ),
            patch("core.db.has_recent_successful_push", return_value=None),
        ):
            res = AgentToolset().push_to_erp(_CTX, doc_keyword="7-11")
        self.assertTrue(res.ok)
        push = res.data["push"]
        self.assertEqual(push["history_id"], "h0")
        self.assertEqual(push["endpoint_name"], "MR.ERP")

    def test_prepare_already_pushed_honest(self):
        with (
            _perms(),
            patch("core.db.list_ocr_history", return_value=self._hist()),
            patch(
                "core.db.list_erp_endpoints",
                return_value=[{"id": "e1", "name": "MR.ERP", "enabled": True}],
            ),
            patch("core.db.has_recent_successful_push", return_value={"id": "log1"}),
        ):
            res = AgentToolset().push_to_erp(_CTX)
        self.assertEqual(res.error_code, "already_pushed")
        self.assertEqual(res.data["pushed_endpoint"], "MR.ERP")

    def test_prepare_no_endpoint_lists_names(self):
        with (
            _perms(),
            patch("core.db.list_ocr_history", return_value=self._hist()),
            patch("core.db.list_erp_endpoints", return_value=[]),
        ):
            res = AgentToolset().push_to_erp(_CTX)
        self.assertEqual(res.error_code, "no_endpoint")
        self.assertEqual(res.data["endpoints"], [])

    def test_prepare_endpoint_by_name(self):
        with (
            _perms(),
            patch("core.db.list_ocr_history", return_value=self._hist()),
            patch(
                "core.db.list_erp_endpoints",
                return_value=[
                    {"id": "e1", "name": "MR.ERP", "enabled": True},
                    {"id": "e2", "name": "Express", "enabled": True},
                ],
            ),
            patch("core.db.has_recent_successful_push", return_value=None),
        ):
            res = AgentToolset().push_to_erp(_CTX, endpoint_name="express")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["push"]["endpoint_id"], "e2")

    def test_prepare_ambiguous_docs(self):
        with _perms(), patch("core.db.list_ocr_history", return_value=self._hist(3)):
            res = AgentToolset().push_to_erp(_CTX, doc_keyword="บิล")
        self.assertEqual(res.error_code, "ambiguous_doc")

    def test_prepare_forbidden(self):
        with _perms(False):
            res = AgentToolset().push_to_erp(_CTX)
        self.assertEqual(res.error_code, "forbidden")


class TestConfirmCard(unittest.TestCase):
    def test_card_has_nonce_buttons_and_no_execution(self):
        sent = []
        with (
            patch("core.db.get_cursor_rls", _fake_cursor),
            patch("services.line_binding.line_action_nonce.mint", return_value="TOK1"),
            patch(
                "services.line_binding.line_reply.reply_messages_context",
                lambda rt, msgs, **k: sent.append(msgs),
            ),
            patch("services.erp.erp_push.push_to_endpoint") as pusher,
        ):
            ok = push_confirm.send_confirm_card(
                _BOUND,
                "rt",
                {
                    "history_id": "h1",
                    "endpoint_id": "e1",
                    "endpoint_name": "MR.ERP",
                    "invoice_no": "IV1",
                    "amount": 120,
                },
                "th",
                "t1",
                1,
                "U1",
            )
        self.assertTrue(ok)
        pusher.assert_not_called()  # 出卡 ≠ 推送
        actions = sent[0][0]["template"]["actions"]
        self.assertIn("TOK1", actions[0]["data"])
        self.assertEqual(
            line_postback.parse(actions[0]["data"])["action"],
            line_postback.ACTION_AGENT_PUSH_CONFIRM,
        )
        self.assertEqual(
            line_postback.parse(actions[1]["data"])["action"],
            line_postback.ACTION_AGENT_PUSH_CANCEL,
        )

    def test_mint_failure_returns_false(self):
        with (
            patch("core.db.get_cursor_rls", _fake_cursor),
            patch("services.line_binding.line_action_nonce.mint", return_value=""),
        ):
            ok = push_confirm.send_confirm_card(
                _BOUND, "rt", {"history_id": "h1", "endpoint_id": "e1"}, "th", "t1", 1, "U1"
            )
        self.assertFalse(ok)


class TestPostback(unittest.TestCase):
    def _ref(self):
        return json.dumps({"kind": "agent_push", "history_id": "h1", "endpoint_id": "e1"})

    def _run(self, action, consume, *, plan_ok=True, runner=None):
        says = []
        ran = []
        runner = runner or (lambda fn: ran.append(fn))
        with (
            patch("core.db.get_cursor_rls", _fake_cursor),
            patch("services.line_binding.line_action_nonce.consume", return_value=consume),
            patch(
                "services.line_binding.line_reply.reply_text_context",
                lambda rt, body, **k: says.append(body),
            ),
            patch(
                "services.line_binding.line_client.t_line",
                lambda lang, key, **k: f"[{key}]",
            ),
            patch(
                "core.route_helpers._plan_permissions",
                return_value={"can_push_erp": plan_ok},
            ),
        ):
            push_confirm.handle_postback(_BOUND, "rt", action, "TOK1", "th", runner=runner)
        return says, ran

    def test_confirm_acks_and_schedules_execution(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_PUSH_CONFIRM, {"status": "ok", "action_ref": self._ref()}
        )
        self.assertEqual(len(ran), 1)  # 执行进了后台 runner
        self.assertIn(says[0], push_confirm._ACK.values())

    def test_cancel_never_executes(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_PUSH_CANCEL, {"status": "ok", "action_ref": self._ref()}
        )
        self.assertEqual(ran, [])
        self.assertTrue(says)  # 已取消回执

    def test_double_click_used_is_idempotent(self):
        with patch("core.db.has_recent_successful_push", return_value={"id": "log1"}):
            with patch("core.db.get_erp_endpoint", return_value={"name": "MR.ERP"}):
                says, ran = self._run(
                    line_postback.ACTION_AGENT_PUSH_CONFIRM,
                    {"status": "used", "action_ref": self._ref()},
                )
        self.assertEqual(ran, [])  # 重放绝不二次执行
        self.assertIn("MR.ERP", says[0])  # 诚实告知已推过

    def test_expired_token(self):
        says, ran = self._run(line_postback.ACTION_AGENT_PUSH_CONFIRM, {"status": "expired"})
        self.assertEqual(ran, [])
        self.assertEqual(says, ["[card_action_expired]"])

    def test_forged_token_missing(self):
        says, ran = self._run(line_postback.ACTION_AGENT_PUSH_CONFIRM, {"status": "missing"})
        self.assertEqual(ran, [])
        self.assertEqual(says, ["[card_action_stale]"])

    def test_no_permission_blocks_execution(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_PUSH_CONFIRM,
            {"status": "ok", "action_ref": self._ref()},
            plan_ok=False,
        )
        self.assertEqual(ran, [])

    def test_bad_ref_stale(self):
        says, ran = self._run(
            line_postback.ACTION_AGENT_PUSH_CONFIRM, {"status": "ok", "action_ref": "not-json"}
        )
        self.assertEqual(ran, [])
        self.assertEqual(says, ["[card_action_stale]"])


class TestExecute(unittest.TestCase):
    """_execute_push 镜像手动推送编排:日志/统计/状态/重试一个不少,结果诚实。"""

    def _base_patches(self, result):
        return (
            patch(
                "core.db.get_ocr_history_detail",
                return_value={"invoice_no": "IV1", "seller_name": "7-11", "total_amount": 120},
            ),
            patch(
                "core.db.get_erp_endpoint",
                return_value={"id": "e1", "name": "MR.ERP", "enabled": True, "adapter": "mrerp"},
            ),
            patch("core.db.has_recent_successful_push", return_value=None),
            patch("services.erp.erp_push.push_to_endpoint", return_value=result),
            patch("core.db.insert_push_log", return_value="log1"),
            patch("core.db.update_endpoint_stats"),
            patch("core.db.update_history_push_status"),
            patch("core.db.is_user_data_error", return_value=False),
            patch("core.db.get_erp_retry_delay_sec", return_value=None),
        )

    def test_success_path(self):
        result = {"success": True, "http_status": 200, "elapsed_ms": 10}
        patches = self._base_patches(result)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3] as pusher,
            patches[4] as logger_,
            patches[5] as stats,
            patches[6] as hist_status,
            patches[7],
            patches[8],
            patch("core.db.classify_push_status", return_value="success"),
            patch("core.db.counts_as_endpoint_success", return_value=True),
        ):
            out = push_confirm._execute_push(_BOUND, "t1", "h1", "e1")
        self.assertEqual(out["kind"], "ok")
        pusher.assert_called_once()
        self.assertEqual(logger_.call_args.kwargs["trigger"], "line_agent")
        stats.assert_called_once()
        hist_status.assert_called_once()

    def test_dup_precheck_skips_push(self):
        with (
            patch(
                "core.db.get_ocr_history_detail",
                return_value={"invoice_no": "IV1", "seller_name": "7-11", "total_amount": 120},
            ),
            patch(
                "core.db.get_erp_endpoint",
                return_value={"id": "e1", "name": "MR.ERP", "enabled": True, "adapter": "mrerp"},
            ),
            patch(
                "core.db.has_recent_successful_push",
                return_value={"id": "log0", "response_body": "{}"},
            ),
            patch("services.erp.erp_push.push_to_endpoint") as pusher,
            patch("core.db.insert_push_log", return_value="log1") as logw,
        ):
            out = push_confirm._execute_push(_BOUND, "t1", "h1", "e1")
        self.assertEqual(out["kind"], "dup")
        pusher.assert_not_called()  # 层 2 幂等:已成功过绝不重推
        self.assertEqual(logw.call_args.kwargs["status"], "skipped_dup")

    def test_failed_is_honest_and_schedules_retry(self):
        result = {"success": False, "error_msg": "ERR_NO_CLIENT", "http_status": 500}
        patches = self._base_patches(result)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
            patches[6],
            patch("core.db.is_user_data_error", return_value=False),
            patch("core.db.get_erp_retry_delay_sec", return_value=60),
            patch("core.db.schedule_log_retry") as retry,
            patch("core.db.classify_push_status", return_value="failed"),
            patch("core.db.counts_as_endpoint_success", return_value=False),
        ):
            out = push_confirm._execute_push(_BOUND, "t1", "h1", "e1")
        self.assertEqual(out["kind"], "failure")
        retry.assert_called_once()

    def test_result_text_failure_never_says_success(self):
        text = push_confirm._result_text(
            {"kind": "failure", "code": "push_failed", "error": "ERR_X"}, "zh"
        )
        self.assertIn("失败", text)
        self.assertNotIn("成功", text)

    def test_history_gone_honest(self):
        with patch("core.db.get_ocr_history_detail", return_value=None):
            out = push_confirm._execute_push(_BOUND, "t1", "h1", "e1")
        self.assertEqual(out, {"kind": "failure", "code": "history_not_found"})


class TestLoopPushGate(unittest.TestCase):
    def test_push_hidden_without_flag(self):
        names = {
            t.name
            for t in __import__("services.agent.loop", fromlist=["x"])._visible_tools(
                frozenset({"write", "m3"})
            )
        }
        self.assertNotIn("push_to_erp", names)

    def test_push_visible_with_flag(self):
        from services.agent import loop

        names = {t.name for t in loop._visible_tools(frozenset({"write", "m3", "push"}))}
        self.assertIn("push_to_erp", names)

    def test_hard_call_without_flag_gets_not_available(self):
        from services.agent import loop

        steps = [
            loop.LoopStep(kind="tool", tool="push_to_erp", args={}),
            loop.LoopStep(kind="reply", message="เรื่องส่ง ERP ทำในแอปได้เลยค่ะ"),
        ]
        seen_obs = []

        def decide(user_text, history, *, observations, **kw):
            seen_obs.append(list(observations))
            return steps.pop(0)

        res = loop.handle_turn(
            "ส่งใบล่าสุดเข้า ERP",
            _CTX,
            decide=decide,
            history=[],
            allow_write=True,
            allow_m3=True,
            allow_push=False,
            write_sink=lambda ctx, tool, data, say="": "card_sent",
        )
        self.assertEqual(res.kind, "reply")
        self.assertEqual(seen_obs[1][0]["error"], "not_available_yet")


if __name__ == "__main__":
    unittest.main()

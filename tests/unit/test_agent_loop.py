"""agent 循环:回复/defer/工具→喂回→成文/未知工具/编造丢弃/步数用尽。"""

import unittest
from contextlib import contextmanager
from decimal import Decimal

from services.agent import loop, manifest
from services.agent.contracts import AgentContext, SlotSpec, ToolResult, ToolSpec
from services.expense.expense_draft import ExpenseDraft

_CTX = AgentContext(user={"id": "u1"}, tenant_id="t1")


def _script(*steps):
    """按顺序吐 LoopStep,模拟模型多步决策(tool→...→reply)。"""
    it = iter(steps)

    def decide(user_text, history, *, today, observations, **kw):
        return next(it)

    return decide


class _FakeToolset:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def get_balance(self, ctx, **kw):
        self.calls.append(("get_balance", kw))
        return self._result

    def probe_handler(self, ctx, **kw):
        self.calls.append(("probe_handler", kw))
        return self._result


@contextmanager
def _temp_tool(spec):
    manifest.TOOLS_BY_NAME[spec.name] = spec
    try:
        yield
    finally:
        manifest.TOOLS_BY_NAME.pop(spec.name, None)


class TestAgentLoop(unittest.TestCase):
    def test_reply_returned_verbatim(self):
        # 模型直接回话(闲聊/产品问题)→ 返模型原文,不套模板。
        out = loop.handle_turn(
            "สวัสดี",
            _CTX,
            decide=_script(loop.LoopStep("reply", message="ยินดีช่วยครับ")),
            history=[],
        )
        self.assertEqual(out, "ยินดีช่วยครับ")

    def test_defer_returns_none(self):
        # 记账/改错/超范围 → defer(None),交旧确定性路。
        out = loop.handle_turn("กาแฟ 50", _CTX, decide=_script(loop.LoopStep("defer")), history=[])
        self.assertIsNone(out)

    def test_tool_then_reply_uses_observation(self):
        ts = _FakeToolset(ToolResult(ok=True, data={"balance_thb": 58.02}))
        out = loop.handle_turn(
            "ยอดเงิน",
            _CTX,
            decide=_script(
                loop.LoopStep("tool", tool="balance", args={}),
                loop.LoopStep("reply", message="เครดิตคงเหลือ 58.02 บาท"),
            ),
            toolset=ts,
            history=[],
        )
        self.assertEqual(out, "เครดิตคงเหลือ 58.02 บาท")
        self.assertEqual(ts.calls[0][0], "get_balance")

    def test_unknown_tool_defers(self):
        out = loop.handle_turn(
            "x", _CTX, decide=_script(loop.LoopStep("tool", tool="ghost", args={})), history=[]
        )
        self.assertIsNone(out)

    def test_fabricated_optional_slot_dropped_not_executed_with_it(self):
        # status 源=user_text;文本没提 → 编造被丢弃,工具仍以可信参数(无 status)执行。
        spec = ToolSpec(
            name="probe",
            bucket="A",
            title_th="",
            desc_th="",
            slots=(SlotSpec("status", False, "user_text", "", ""),),
            handler="probe_handler",
            confirm=False,
        )
        ts = _FakeToolset(ToolResult(ok=True, data={}))
        with _temp_tool(spec):
            out = loop.handle_turn(
                "สวัสดี",
                _CTX,
                decide=_script(
                    loop.LoopStep("tool", tool="probe", args={"status": "failed"}),
                    loop.LoopStep("reply", message="ok"),
                ),
                toolset=ts,
                history=[],
            )
        self.assertEqual(out, "ok")
        self.assertEqual(ts.calls, [("probe_handler", {})])  # 不带编造 status

    def test_missing_required_slot_not_executed(self):
        # 必填槽没接地 → 不执行该工具;模型收到缺口后改口回复。
        spec = ToolSpec(
            name="probe",
            bucket="A",
            title_th="",
            desc_th="",
            slots=(SlotSpec("status", True, "user_text", "", ""),),
            handler="probe_handler",
            confirm=False,
        )
        ts = _FakeToolset(ToolResult(ok=True, data={}))
        with _temp_tool(spec):
            out = loop.handle_turn(
                "สวัสดี",
                _CTX,
                decide=_script(
                    loop.LoopStep("tool", tool="probe", args={"status": "failed"}),
                    loop.LoopStep("reply", message="ขอสถานะหน่อยครับ"),
                ),
                toolset=ts,
                history=[],
            )
        self.assertEqual(out, "ขอสถานะหน่อยครับ")
        self.assertEqual(ts.calls, [])  # 必填缺失绝不执行

    def test_steps_exhausted_defers(self):
        ts = _FakeToolset(ToolResult(ok=True, data={"balance_thb": 1}))
        steps = [loop.LoopStep("tool", tool="balance", args={}) for _ in range(loop._MAX_STEPS)]
        out = loop.handle_turn("x", _CTX, decide=_script(*steps), toolset=ts, history=[])
        self.assertIsNone(out)


class _RecToolset:
    def __init__(self, result):
        self._result = result

    def record_expense(self, ctx, **kw):
        return self._result


class TestConfirmFlow(unittest.TestCase):
    """M3 记账:模型提议→接地建草稿→record_sink 出富卡(确认走现成卡按钮+postback);
    写关/无出卡器则 defer;金额没接地则大脑文字追问(不出卡)。"""

    def _draft(self):
        return ExpenseDraft(amount=Decimal("50"), vendor_name="cafe", note="coffee")

    def test_record_sink_emits_card_and_consumes_turn(self):
        sunk = []
        ts = _RecToolset(ToolResult(ok=True, data={"draft": self._draft()}))
        out = loop.handle_turn(
            "咖啡 50",
            _CTX,
            decide=_script(
                loop.LoopStep(
                    "tool", tool="record_expense", args={"amount": "50", "note": "coffee"}
                ),
            ),
            toolset=ts,
            history=[],
            allow_write=True,
            record_sink=lambda ctx, draft: sunk.append(draft),
        )
        self.assertEqual(out, loop.RECORD_CARD_SENT)  # 卡即回复:消费本轮,别再发文字
        self.assertEqual(len(sunk), 1)  # 走出卡回调
        self.assertEqual(sunk[0].amount, Decimal("50"))  # 接地好的真实草稿

    def test_confirm_tool_deferred_when_write_off(self):
        # 写关:record_expense 一律 defer 回旧路(记账走旧乐观路,现状不变)。
        out = loop.handle_turn(
            "咖啡 50",
            _CTX,
            decide=_script(loop.LoopStep("tool", tool="record_expense", args={"amount": "50"})),
            toolset=_RecToolset(ToolResult(ok=True, data={"draft": self._draft()})),
            history=[],
            allow_write=False,
        )
        self.assertIsNone(out)

    def test_no_record_sink_defers(self):
        out = loop.handle_turn(
            "咖啡 50",
            _CTX,
            decide=_script(loop.LoopStep("tool", tool="record_expense", args={"amount": "50"})),
            toolset=_RecToolset(ToolResult(ok=True, data={"draft": self._draft()})),
            history=[],
            allow_write=True,
            record_sink=None,
        )
        self.assertIsNone(out)

    def test_amount_ungrounded_asks_not_sinks(self):
        sunk = []
        ts = _RecToolset(ToolResult(ok=False, error_code="amount_ungrounded"))
        out = loop.handle_turn(
            "咖啡",
            _CTX,
            decide=_script(
                loop.LoopStep("tool", tool="record_expense", args={"note": "coffee"}),
                loop.LoopStep("reply", message="金额多少?"),
            ),
            toolset=ts,
            history=[],
            allow_write=True,
            record_sink=lambda ctx, draft: sunk.append(draft),
        )
        self.assertEqual(out, "金额多少?")
        self.assertEqual(sunk, [])  # 没接地绝不出卡

    def test_visible_tools_hides_confirm_when_write_off(self):
        off = {t.name for t in loop._visible_tools(False)}
        on = {t.name for t in loop._visible_tools(True)}
        self.assertNotIn("record_expense", off)
        self.assertIn("record_expense", on)


class TestObservePayload(unittest.TestCase):
    def test_notifications_count_from_list(self):
        # list_notification_logs 返回的 result.data 是 list;count 必须按真实条数,不能恒 0。
        obs = loop._observe_payload(
            "list_notifications", ToolResult(ok=True, data=[{"id": 1}, {"id": 2}, {"id": 3}])
        )
        self.assertEqual(obs, {"ok": True, "count": 3})

    def test_notifications_empty_list(self):
        obs = loop._observe_payload("list_notifications", ToolResult(ok=True, data=[]))
        self.assertEqual(obs, {"ok": True, "count": 0})

    def test_grounded_fallback_notifications_some(self):
        msg = loop._grounded_fallback([{"tool": "list_notifications", "count": 2}], "zh")
        self.assertEqual(msg, "有 2 条通知。")

    def test_grounded_fallback_notifications_zero(self):
        msg = loop._grounded_fallback([{"tool": "list_notifications", "count": 0}], "en")
        self.assertEqual(msg, "No new notifications.")


if __name__ == "__main__":
    unittest.main()

"""agent 循环:回复/defer/工具→喂回→成文/未知工具/编造丢弃/步数用尽。"""

import unittest
from contextlib import contextmanager

from services.agent import loop, manifest
from services.agent.contracts import AgentContext, SlotSpec, ToolResult, ToolSpec

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


if __name__ == "__main__":
    unittest.main()

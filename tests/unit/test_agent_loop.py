"""单轮编排分支:超范围/闲聊/反问/执行/编造拦截/B 档确认。"""

import unittest
from contextlib import contextmanager

from services.agent import loop, manifest
from services.agent.contracts import AgentAction, AgentContext, SlotSpec, ToolResult, ToolSpec

_CTX = AgentContext(user={"id": "u1"}, tenant_id="t1")


def _decide(action):
    return lambda user_text, history, *, today: action


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
    def test_out_of_scope(self):
        out = loop.handle_turn(
            "อากาศวันนี้", _CTX, decide=_decide(AgentAction(kind="out_of_scope")), history=[]
        )
        self.assertTrue(out.startswith("agent.oos."))

    def test_chat(self):
        out = loop.handle_turn("สวัสดี", _CTX, decide=_decide(AgentAction(kind="chat")), history=[])
        self.assertTrue(out.startswith("agent.chat."))

    def test_ask(self):
        out = loop.handle_turn(
            "ดูบิล",
            _CTX,
            decide=_decide(AgentAction(kind="ask", ask_field="keyword")),
            history=[],
        )
        self.assertTrue(out.startswith("agent.ask."))

    def test_tool_happy_path_runs_handler(self):
        ts = _FakeToolset(ToolResult(ok=True, receipt="RECEIPT_OK"))
        out = loop.handle_turn(
            "ยอดเงิน",
            _CTX,
            decide=_decide(AgentAction(kind="tool", tool="balance", args={})),
            toolset=ts,
            history=[],
        )
        self.assertEqual(out, "RECEIPT_OK")
        self.assertEqual(ts.calls[0][0], "get_balance")

    def test_unknown_tool_is_out_of_scope(self):
        out = loop.handle_turn(
            "x",
            _CTX,
            decide=_decide(AgentAction(kind="tool", tool="ghost", args={})),
            history=[],
        )
        self.assertTrue(out.startswith("agent.oos."))

    def test_fabricated_required_slot_triggers_ask(self):
        spec = ToolSpec(
            name="probe",
            bucket="A",
            title_th="",
            desc_th="",
            slots=(SlotSpec("status", True, "user_text", "", ""),),
            handler="probe_handler",
            confirm=False,
        )
        ts = _FakeToolset(ToolResult(ok=True, receipt="SHOULD_NOT_RUN"))
        with _temp_tool(spec):
            out = loop.handle_turn(
                "สวัสดี",  # 不含 "failed" → status 编造
                _CTX,
                decide=_decide(AgentAction(kind="tool", tool="probe", args={"status": "failed"})),
                toolset=ts,
                history=[],
            )
        self.assertTrue(out.startswith("agent.ask."))
        self.assertEqual(ts.calls, [])  # 绝不带编造值执行

    def test_b_bucket_requires_confirmation(self):
        spec = ToolSpec(
            name="probe",
            bucket="B",
            title_th="",
            desc_th="",
            slots=(),
            handler="probe_handler",
            confirm=True,
        )
        action = AgentAction(kind="tool", tool="probe", args={})
        ts_unconfirmed = _FakeToolset(ToolResult(ok=True, receipt="EXECUTED"))
        ts_confirmed = _FakeToolset(ToolResult(ok=True, receipt="EXECUTED"))
        with _temp_tool(spec):
            unconfirmed = loop.handle_turn(
                "ทำเลย", _CTX, decide=_decide(action), toolset=ts_unconfirmed, history=[]
            )
            confirmed = loop.handle_turn(
                "ยืนยัน", _CTX, decide=_decide(action), toolset=ts_confirmed, history=[]
            )
        self.assertTrue(unconfirmed.startswith("agent.confirm."))
        self.assertEqual(ts_unconfirmed.calls, [])  # 未确认不执行
        self.assertEqual(confirmed, "EXECUTED")  # 确认词后执行

    def test_failed_result_renders_failure(self):
        ts = _FakeToolset(ToolResult(ok=False, error_code="query_failed"))
        out = loop.handle_turn(
            "ยอดเงิน",
            _CTX,
            decide=_decide(AgentAction(kind="tool", tool="balance", args={})),
            toolset=ts,
            history=[],
        )
        self.assertTrue(out.startswith("agent.failure."))


if __name__ == "__main__":
    unittest.main()

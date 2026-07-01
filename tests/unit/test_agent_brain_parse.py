"""大脑解析:JSON 动作 → AgentAction,失败/非法一律兜底 chat(不抛、不执行)。"""

import unittest

from services.agent import brain, manifest
from services.ai_gateway.tasks import ProviderOutcome


def _out(data, ok=True):
    return ProviderOutcome(ok=ok, data=data)


class TestAgentBrainParse(unittest.TestCase):
    def test_tool_action(self):
        a = brain._parse_action(_out({"kind": "tool", "tool": "balance", "args": {}}))
        self.assertEqual(a.kind, "tool")
        self.assertEqual(a.tool, "balance")

    def test_ask_action(self):
        a = brain._parse_action(_out({"kind": "ask", "ask_field": "keyword"}))
        self.assertEqual(a.kind, "ask")
        self.assertEqual(a.ask_field, "keyword")

    def test_out_of_scope(self):
        a = brain._parse_action(_out({"kind": "out_of_scope", "message": "ไปที่แอป"}))
        self.assertEqual(a.kind, "out_of_scope")

    def test_tool_without_name_becomes_out_of_scope(self):
        a = brain._parse_action(_out({"kind": "tool", "tool": "", "args": {}}))
        self.assertEqual(a.kind, "out_of_scope")

    def test_invalid_kind_falls_back_to_chat(self):
        a = brain._parse_action(_out({"kind": "delete_everything"}))
        self.assertEqual(a.kind, "chat")

    def test_provider_failure_falls_back_to_chat(self):
        a = brain._parse_action(_out(None, ok=False))
        self.assertEqual(a.kind, "chat")

    def test_non_dict_data_falls_back_to_chat(self):
        a = brain._parse_action(_out("not json"))
        self.assertEqual(a.kind, "chat")

    def test_args_non_dict_coerced_empty(self):
        a = brain._parse_action(_out({"kind": "tool", "tool": "balance", "args": "oops"}))
        self.assertEqual(a.args, {})

    def test_prompt_lists_every_tool(self):
        prompt = brain.build_prompt(manifest.TOOLS, "ดูยอดเงิน", [], "2026-06-30")
        for t in manifest.TOOLS:
            self.assertIn(t.name, prompt)
        self.assertIn("ดูยอดเงิน", prompt)  # 用户消息折进提示词(transport 无独立 text 形参)

    def test_decide_uses_gateway(self):
        # decide 走真实 transport;注入桩 outcome 验证编排不依赖真网络。
        import services.ai_gateway.transport as transport

        original = transport.text_to_json
        transport.text_to_json = lambda *a, **k: _out(
            {"kind": "tool", "tool": "balance", "args": {}}
        )
        try:
            a = brain.decide("ยอดเงินเหลือเท่าไหร่", [], today="2026-06-30")
        finally:
            transport.text_to_json = original
        self.assertEqual(a.tool, "balance")

    def test_decide_passes_brain_backend(self):
        # AGENT_BRAIN_BACKEND 未设 → backend=None(跟随全局);设 selfhost → 透传给网关。
        import os

        import services.ai_gateway.transport as transport

        seen = {}
        original = transport.text_to_json

        def _stub(*a, **k):
            seen["backend"] = k.get("backend")
            return _out({"kind": "tool", "tool": "balance", "args": {}})

        transport.text_to_json = _stub
        try:
            os.environ.pop("AGENT_BRAIN_BACKEND", None)
            brain.decide("hi", [], today="2026-06-30")
            self.assertIsNone(seen["backend"])
            os.environ["AGENT_BRAIN_BACKEND"] = "selfhost"
            brain.decide("hi", [], today="2026-06-30")
            self.assertEqual(seen["backend"], "selfhost")
        finally:
            transport.text_to_json = original
            os.environ.pop("AGENT_BRAIN_BACKEND", None)


if __name__ == "__main__":
    unittest.main()

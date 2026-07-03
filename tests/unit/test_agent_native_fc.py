# -*- coding: utf-8 -*-
"""原生 function-calling(P2)契约。

铁四条:① manifest → 声明映射保真(slots/required/array·无参不带 parameters·defer 恒附);
② loop 双通道:闸开走 text_to_action(FC 协议尾),unsupported/闸关回落 JSON 路(行为零损失);
③ defer 工具映射回 defer 裁决(与 JSON 协议同一条出路);④ vertex 归一:functionCall→tool、
纯文本→reply、空→parse(绝不吐半结构)。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.agent import loop, manifest, native_fc
from services.agent.contracts import AgentContext


class TestDeclarations(unittest.TestCase):
    def test_manifest_tools_map_to_declarations(self):
        decls = native_fc.declarations(manifest.TOOLS)
        by_name = {d["name"]: d for d in decls}
        self.assertIn("defer", by_name)  # defer 恒附(FC 模式的 defer 出路)
        lh = by_name["list_history"]
        self.assertEqual(lh["parameters"]["properties"]["keyword"]["type"], "string")
        self.assertIsNone(by_name["balance"].get("parameters"))  # 无参不带(空 OBJECT 拒收)
        goals = by_name["plan_incoming_doc"]["parameters"]["properties"]["goals"]
        self.assertEqual(goals["type"], "array")  # SlotSpec.kind=array
        self.assertIn("goals", by_name["plan_incoming_doc"]["parameters"]["required"])
        self.assertEqual(by_name["switch_workspace"]["parameters"]["required"], ["name"])

    def test_defer_declaration_shape(self):
        reason = native_fc.DEFER["parameters"]["properties"]["reason"]
        self.assertEqual(reason["enum"], ["record", "edit"])


class TestParseStepDeferTool(unittest.TestCase):
    def test_defer_tool_maps_to_defer_verdict(self):
        out = MagicMock(ok=True, data={"kind": "tool", "tool": "defer", "args": {"reason": "edit"}})
        step = loop._parse_step(out)
        self.assertEqual((step.kind, step.reason), ("defer", "edit"))

    def test_defer_tool_missing_reason_defaults_record(self):
        out = MagicMock(ok=True, data={"kind": "tool", "tool": "defer", "args": {}})
        step = loop._parse_step(out)
        self.assertEqual((step.kind, step.reason), ("defer", "record"))


class TestLoopNativeChannel(unittest.TestCase):
    def _ctx(self):
        return AgentContext(user={"id": "u1"}, tenant_id="t1")

    def test_flag_on_uses_native_channel_with_fc_protocol(self):
        seen = {}

        def fake_action(prompt, **kw):
            seen["prompt"] = prompt
            seen.update(kw)
            return MagicMock(ok=True, data={"kind": "reply", "message": "hi"}, error_kind=None)

        with (
            patch("core.feature_flags.agent_native_fc_enabled_for", return_value=True),
            patch("services.ai_gateway.transport.text_to_action", fake_action),
            patch("services.ai_gateway.transport.text_to_json") as tj,
        ):
            step = loop._decide_step("สวัสดี", [], today="t", observations=[], ctx=self._ctx())
        tj.assert_not_called()
        self.assertEqual((step.kind, step.message), ("reply", "hi"))
        self.assertNotIn("ONE line of JSON", seen["prompt"])  # FC 协议尾顶替 JSON 尾
        self.assertIn("Never write JSON", seen["prompt"])
        self.assertTrue(any(d["name"] == "defer" for d in seen["tools"]))

    def test_unsupported_backend_falls_back_to_json(self):
        with (
            patch("core.feature_flags.agent_native_fc_enabled_for", return_value=True),
            patch(
                "services.ai_gateway.transport.text_to_action",
                return_value=MagicMock(ok=False, error_kind="unsupported"),
            ),
            patch(
                "services.ai_gateway.transport.text_to_json",
                return_value=MagicMock(ok=True, data={"kind": "reply", "message": "ok"}),
            ) as tj,
        ):
            step = loop._decide_step("hi", [], today="t", observations=[], ctx=self._ctx())
        tj.assert_called_once()
        self.assertEqual(step.message, "ok")
        self.assertIn("ONE line of JSON", tj.call_args.args[0])  # 回落路仍 JSON 协议尾

    def test_flag_off_never_touches_native(self):
        with (
            patch("core.feature_flags.agent_native_fc_enabled_for", return_value=False),
            patch("services.ai_gateway.transport.text_to_action") as ta,
            patch(
                "services.ai_gateway.transport.text_to_json",
                return_value=MagicMock(ok=True, data={"kind": "reply", "message": "ok"}),
            ),
        ):
            loop._decide_step("hi", [], today="t", observations=[], ctx=self._ctx())
        ta.assert_not_called()

    def test_native_crash_error_does_not_fall_back(self):
        # 非 unsupported 的故障(quota/timeout)不二次烧钱重试 JSON 路 → 正常 crash 兜底口径。
        with (
            patch("core.feature_flags.agent_native_fc_enabled_for", return_value=True),
            patch(
                "services.ai_gateway.transport.text_to_action",
                return_value=MagicMock(ok=False, error_kind="quota", data=None, raw=""),
            ),
            patch("services.ai_gateway.transport.text_to_json") as tj,
        ):
            step = loop._decide_step("hi", [], today="t", observations=[], ctx=self._ctx())
        tj.assert_not_called()
        self.assertEqual((step.kind, step.reason), ("defer", "crash"))


class TestVertexActionNormalization(unittest.TestCase):
    def _resp(self, fcs=None, text=""):
        r = MagicMock()
        r.function_calls = fcs
        r.text = text
        r.usage_metadata = None
        return r

    def _run(self, resp, tools=None):
        from services.ai_gateway.providers import vertex

        client = MagicMock()
        client.models.generate_content.return_value = resp
        with (
            patch.object(vertex, "_client", return_value=client),
            patch.object(vertex, "_resolve_model", return_value="m"),
        ):
            return vertex.text_to_action("p", tools=tools or [{"name": "t"}])

    def test_function_call_normalized_to_tool_action(self):
        fc = MagicMock()
        fc.name = "list_history"
        fc.args = {"keyword": "7-11"}
        out = self._run(self._resp(fcs=[fc]))
        self.assertTrue(out.ok)
        self.assertEqual(
            out.data, {"kind": "tool", "tool": "list_history", "args": {"keyword": "7-11"}}
        )

    def test_plain_text_normalized_to_reply(self):
        out = self._run(self._resp(text="สวัสดีค่ะ"))
        self.assertTrue(out.ok)
        self.assertEqual(out.data, {"kind": "reply", "message": "สวัสดีค่ะ"})

    def test_empty_response_is_parse_error(self):
        out = self._run(self._resp())
        self.assertFalse(out.ok)
        self.assertEqual(out.error_kind, "parse")

    def test_schema_conversion_object_array(self):
        try:
            from google.genai import types
        except Exception:  # pragma: no cover — 本地无 SDK 时跳过(CI/prod 都装)
            self.skipTest("google-genai not installed")
        from services.ai_gateway.providers import vertex

        sch = vertex._fc_schema(
            {
                "type": "object",
                "properties": {"goals": {"type": "array", "items": {"type": "string"}}},
                "required": ["goals"],
            }
        )
        self.assertEqual(sch.type, types.Type.OBJECT)
        self.assertEqual(sch.properties["goals"].type, types.Type.ARRAY)
        self.assertIsNone(vertex._fc_schema(None))  # 无参工具

    def test_stub_backends_return_unsupported(self):
        from services.ai_gateway.providers import aistudio, selfhost

        self.assertEqual(aistudio.text_to_action("p", tools=[]).error_kind, "unsupported")
        self.assertEqual(selfhost.text_to_action("p", tools=[]).error_kind, "unsupported")


if __name__ == "__main__":
    unittest.main()

"""参数确定性闸:接地放行,编造拦下(M1 安全核心验收)。"""

import unittest

from services.agent import slots
from services.agent.contracts import AgentAction, AgentContext, SlotSpec, ToolSpec

_CTX = AgentContext(user={"id": "u1"}, tenant_id="t1")


def _spec(*slot_specs) -> ToolSpec:
    return ToolSpec(
        name="probe",
        bucket="A",
        title_th="",
        desc_th="",
        slots=slot_specs,
        handler="x",
        confirm=False,
    )


class TestAgentSlots(unittest.TestCase):
    def test_freeform_keyword_passes(self):
        action = AgentAction(kind="tool", tool="probe", args={"keyword": "7-eleven"})
        spec = _spec(SlotSpec("keyword", False, "model_freeform", "", ""))
        chk = slots.check_slots(action, user_text="ดูบิล", history=[], ctx=_CTX, spec=spec)
        self.assertTrue(chk.ok)
        self.assertEqual(chk.grounded["keyword"], "7-eleven")

    def test_required_user_text_fabricated_goes_missing(self):
        # 模型给的值不在用户原话 → 必填→反问(不执行)。
        action = AgentAction(kind="tool", tool="probe", args={"status": "failed"})
        spec = _spec(SlotSpec("status", True, "user_text", "", ""))
        chk = slots.check_slots(action, user_text="สวัสดี", history=[], ctx=_CTX, spec=spec)
        self.assertFalse(chk.ok)
        self.assertIn("status", chk.missing)
        self.assertIn("status", chk.rejected)

    def test_optional_fabricated_dropped_not_executed(self):
        action = AgentAction(kind="tool", tool="probe", args={"status": "failed"})
        spec = _spec(SlotSpec("status", False, "user_text", "", ""))
        chk = slots.check_slots(action, user_text="สวัสดี", history=[], ctx=_CTX, spec=spec)
        self.assertTrue(chk.ok)  # 选填,可继续
        self.assertNotIn("status", chk.grounded)  # 但绝不带编造值
        self.assertIn("status", chk.rejected)

    def test_user_text_grounded_in_history(self):
        action = AgentAction(kind="tool", tool="probe", args={"status": "failed"})
        spec = _spec(SlotSpec("status", False, "user_text", "", ""))
        chk = slots.check_slots(
            action,
            user_text="แล้วอันที่ failed ล่ะ",
            history=[{"role": "user", "content": "ก่อนหน้านี้"}],
            ctx=_CTX,
            spec=spec,
        )
        self.assertTrue(chk.ok)
        self.assertEqual(chk.grounded["status"], "failed")

    def test_anchor_without_context_rejected(self):
        action = AgentAction(kind="tool", tool="probe", args={"doc_id": "abc"})
        spec = _spec(SlotSpec("doc_id", True, "anchor", "", ""))
        chk = slots.check_slots(action, user_text="ตัวนี้", history=[], ctx=_CTX, spec=spec)
        self.assertFalse(chk.ok)
        self.assertEqual(chk.rejected["doc_id"], "no_anchor")

    def test_anchor_resolves_from_ctx(self):
        ctx = AgentContext(user={"id": "u1"}, tenant_id="t1", anchors={"doc_id": 42})
        action = AgentAction(kind="tool", tool="probe", args={"doc_id": "model-said-99"})
        spec = _spec(SlotSpec("doc_id", True, "anchor", "", ""))
        chk = slots.check_slots(action, user_text="ตัวนี้", history=[], ctx=ctx, spec=spec)
        self.assertTrue(chk.ok)
        self.assertEqual(chk.grounded["doc_id"], 42)  # 用锚点值,不信模型说的 99

    def test_unknown_tool_spec_fails(self):
        action = AgentAction(kind="tool", tool="does_not_exist", args={})
        chk = slots.check_slots(action, user_text="x", history=[], ctx=_CTX)
        self.assertFalse(chk.ok)


if __name__ == "__main__":
    unittest.main()

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

    def test_number_with_thousand_separator_grounds(self):
        # 会计打「10,700 含税的」,模型交回 10700:逐字比会判成编造,按数值比才认得出。
        action = AgentAction(kind="tool", tool="probe", args={"amount": "10700"})
        spec = _spec(SlotSpec("amount", True, "user_text", "", ""))
        chk = slots.check_slots(
            action, user_text="10,700 含税的,税前多少", history=[], ctx=_CTX, spec=spec
        )
        self.assertTrue(chk.ok)
        self.assertEqual(chk.grounded["amount"], "10700")

    def test_number_equal_value_different_form_grounds(self):
        action = AgentAction(kind="tool", tool="probe", args={"amount": "1200.50"})
        spec = _spec(SlotSpec("amount", True, "user_text", "", ""))
        chk = slots.check_slots(
            action, user_text="จ่ายไป 1,200.5 บาท", history=[], ctx=_CTX, spec=spec
        )
        self.assertTrue(chk.ok)

    def test_percent_rate_grounds_against_bare_digits(self):
        action = AgentAction(kind="tool", tool="probe", args={"wht_rate": "3%"})
        spec = _spec(SlotSpec("wht_rate", False, "user_text", "", ""))
        chk = slots.check_slots(
            action, user_text="หัก ณ ที่จ่าย 3 เปอร์เซ็นต์", history=[], ctx=_CTX, spec=spec
        )
        self.assertTrue(chk.ok)
        self.assertEqual(chk.grounded["wht_rate"], "3%")

    def test_fabricated_number_still_rejected(self):
        action = AgentAction(kind="tool", tool="probe", args={"amount": "88888"})
        spec = _spec(SlotSpec("amount", True, "user_text", "", ""))
        chk = slots.check_slots(action, user_text="10,700 含税的", history=[], ctx=_CTX, spec=spec)
        self.assertFalse(chk.ok)
        self.assertEqual(chk.rejected["amount"], "not_in_user_text")

    def test_adjacent_numbers_not_merged_across_space(self):
        """「1 ใบ 200 บาท」里没有 1200 这个数——空白两侧的数字绝不粘成一个。"""
        action = AgentAction(kind="tool", tool="probe", args={"amount": "1200"})
        spec = _spec(SlotSpec("amount", True, "user_text", "", ""))
        chk = slots.check_slots(action, user_text="1 ใบ 200 บาท", history=[], ctx=_CTX, spec=spec)
        self.assertFalse(chk.ok)

    def test_non_numeric_value_keeps_literal_grounding(self):
        action = AgentAction(kind="tool", tool="probe", args={"keyword": "7-eleven"})
        spec = _spec(SlotSpec("keyword", True, "user_text", "", ""))
        chk = slots.check_slots(action, user_text="บิล 7-eleven", history=[], ctx=_CTX, spec=spec)
        self.assertTrue(chk.ok)

    def test_negative_amount_grounds_literally(self):
        """退货/贷记单的负数照旧走字面接地(数值面不认符号,不能因此把真值判成编造)。"""
        action = AgentAction(kind="tool", tool="probe", args={"amount": "-500"})
        spec = _spec(SlotSpec("amount", True, "user_text", "", ""))
        chk = slots.check_slots(action, user_text="คืนของ -500", history=[], ctx=_CTX, spec=spec)
        self.assertTrue(chk.ok)

    def test_unknown_tool_spec_fails(self):
        action = AgentAction(kind="tool", tool="does_not_exist", args={})
        chk = slots.check_slots(action, user_text="x", history=[], ctx=_CTX)
        self.assertFalse(chk.ok)


if __name__ == "__main__":
    unittest.main()

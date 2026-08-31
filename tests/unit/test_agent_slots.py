"""参数确定性闸:接地放行,编造拦下(M1 安全核心验收)。"""

import unittest

from services.steward import slots
from services.steward.contracts import AgentAction, AgentContext, SlotSpec, ToolSpec

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


# 真语料出处(不是编的例子):
#   税号 0105535134278 = Express 事务所 6 家账套 / Moritomo_58MORI / ISVAT.csv 对手方税号(出现 3716 次)
#   金额 2,008.39 与 140.59 = 同一行的税前与税额
#   单号 SI690531-005 / VAT 号 690531-005 / 2,336.45 / 163.55 = SM 销项税登记簿 acvatsaled 5 月
#   进项票号 10104022610000581 = SM 采购费用_明细头 doc_id=43(17 位,里面正好含 13 位数字)
#   卖家名 ชาร์ม คอสเมท จำกัด 与金额 54,240.00 = 同表 doc_id=76
_TAX_ID = "0105535134278"
_TAX_ID_DASHED = "0-1055-35134-27-8"
_VAT_DOC_NO = "10104022610000581"


def _grounds(value: str, said: str) -> bool:
    """把一个值丢给接地闸:True=闸认了这个值来自用户原话。"""
    action = AgentAction(kind="tool", tool="probe", args={"v": value})
    spec = _spec(SlotSpec("v", True, "user_text", "", ""))
    return slots.check_slots(action, user_text=said, history=[], ctx=_CTX, spec=spec).ok


class NumberShavingTests(unittest.TestCase):
    """该拦的:模型削掉几位就得到一个用户从没说过的数,子串比会当它已接地。"""

    def test_a_shorter_number_cannot_shave_a_real_amount(self):
        self.assertFalse(_grounds("107", "โอนไป 10700 บาท"))

    def test_a_number_cannot_be_cut_at_the_thousand_separator(self):
        self.assertFalse(_grounds("500", "ยอด 2,500.00 บาท"))

    def test_dropping_the_satang_is_not_the_same_amount(self):
        self.assertFalse(_grounds("2336", "ภาษีขาย 2,336.45"))

    def test_a_trailing_digit_cannot_be_dropped(self):
        self.assertFalse(_grounds("63,413.8", "ซื้อของ 63,413.83 บาท"))

    def test_a_tax_id_cannot_be_shaved_off_a_longer_tax_id(self):
        self.assertFalse(_grounds("010553513427", f"เลขภาษี {_TAX_ID}"))

    def test_a_tax_id_cannot_be_sliced_out_of_a_tax_invoice_number(self):
        """真票号 10104022610000581 里排在前面的 13 位数字不是谁的税号。"""
        self.assertFalse(_grounds("1010402261000", f"ใบกำกับเลขที่ {_VAT_DOC_NO}"))

    def test_a_doc_number_cannot_be_shaved(self):
        self.assertFalse(_grounds("SI690531-00", "ใบ SI690531-005 ยังไม่ได้ลง"))

    def test_a_value_starting_at_the_decimal_point_is_not_grounded(self):
        """真语料扫出来的边角:「9.00」削成「.00」时端点是小数点,左边界照样得管。"""
        self.assertFalse(_grounds(".00", "ค่าส่ง 9.00 บาท"))

    def test_a_date_is_not_an_identifier(self):
        """31/05/2569 是日期不是标识符:凑出来的 8 位数字不许当一个号接地。"""
        self.assertFalse(_grounds("31052569", "ลงวันที่ 31/05/2569"))


class NoFalseAlarmTests(unittest.TestCase):
    """不该拦的:误伤会把会计真说过的数判成编造,比放过更难被发现。"""

    def test_a_real_amount_grounds_across_formatting(self):
        self.assertTrue(_grounds("2336.45", "ภาษีขาย 2,336.45"))

    def test_a_real_amount_grounds_verbatim(self):
        self.assertTrue(_grounds("2,008.39", "ยอดก่อนภาษี 2,008.39 บาท"))

    def test_a_full_stop_after_the_amount_does_not_break_it(self):
        self.assertTrue(_grounds("140.59", "ภาษีซื้อใบนี้ 140.59."))

    def test_a_real_doc_number_grounds(self):
        self.assertTrue(_grounds("SI690531-005", "ใบ SI690531-005 ยังไม่ได้ลง"))

    def test_the_vat_number_inside_the_doc_number_grounds(self):
        """690531-005 是 SI690531-005 的一整段数字,不是从某个数中间切出来的。"""
        self.assertTrue(_grounds("690531-005", "ใบ SI690531-005 ยังไม่ได้ลง"))

    def test_a_dashed_tax_id_grounds_once_the_model_normalises_it(self):
        self.assertTrue(_grounds(_TAX_ID, f"เลขภาษี {_TAX_ID_DASHED}"))

    def test_a_plain_tax_id_grounds_when_the_model_writes_it_dashed(self):
        self.assertTrue(_grounds(_TAX_ID_DASHED, f"เลขภาษี {_TAX_ID}"))

    def test_a_real_vendor_name_still_grounds_by_substring(self):
        self.assertTrue(_grounds("ชาร์ม คอสเมท", "ใบของ ชาร์ม คอสเมท จำกัด 54,240.00"))

    def test_a_real_purchase_amount_grounds_across_formatting(self):
        self.assertTrue(_grounds("54240", "ใบของ ชาร์ม คอสเมท จำกัด 54,240.00"))


if __name__ == "__main__":
    unittest.main()

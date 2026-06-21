# -*- coding: utf-8 -*-
"""大脑路径金额接地守卫:LLM 不编金额。

真机事故:发「接触绑定」(无数字)→ 大脑(Gemini)凭空返 record amount=50 → 被记成 50 THB 咖啡。
根因 = to_draft 采信 LLM 的 amount,绕过「金额永不信 LLM」铁律。修 = 金额必须在用户原文里有对应
数字才保留,不接地则置空 → has_amount() 转假 → 缺金额追问,绝不凭空入账。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.expense import line_l2
from services.line_binding import line_expense as le


class AmountGroundedTests(unittest.TestCase):
    def _g(self, text, amount, qty=None, unit_price=None):
        dec = lambda v: Decimal(str(v)) if v is not None else None  # noqa: E731
        return line_l2.amount_grounded(dec(amount), dec(qty), dec(unit_price), text)

    def test_amount_present_in_text_is_grounded(self):
        self.assertTrue(self._g("ค่าอาหารกลางวัน 150 บาท", 150))

    def test_amount_absent_from_text_is_not_grounded(self):
        # 「接触绑定」无任何数字 → LLM 编的 50 不接地。
        self.assertFalse(self._g("接触绑定", 50))

    def test_no_digit_at_all_rejects_any_amount(self):
        self.assertFalse(self._g("买点东西", 99))

    def test_qty_times_unit_price_grounded(self):
        # 「买2杯共120」:120 在原文 → 接地。
        self.assertTrue(self._g("买2杯咖啡共120", 120, qty=2, unit_price=60))

    def test_qty_price_product_grounded_when_total_absent(self):
        # 总额 100 未直接出现,但 qty=2、单价=50 都在原文且乘积=100 → 确定性可复算,接地。
        self.assertTrue(self._g("2 ชิ้น ชิ้นละ 50", 100, qty=2, unit_price=50))

    def test_hallucinated_total_from_partial_numbers_not_grounded(self):
        # 原文有 3,但 LLM 编出 300(非接地、非 qty×price)→ 拒。
        self.assertFalse(self._g("买了3个", 300))

    def test_none_amount_not_grounded(self):
        self.assertFalse(self._g("咖啡", None))


class ToDraftGroundingTests(unittest.TestCase):
    def test_to_draft_drops_ungrounded_amount(self):
        u = {"intent": "record", "amount": 50, "note": "咖啡"}
        draft = line_l2.to_draft(u, "接触绑定")
        self.assertIsNone(draft.amount)
        self.assertFalse(draft.has_amount())

    def test_to_draft_keeps_grounded_amount(self):
        u = {"intent": "record", "amount": 88, "note": "ของ"}
        draft = line_l2.to_draft(u, "จ่ายค่าของ 88")
        self.assertEqual(draft.amount, Decimal("88"))


class _CM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _dispatch(text, understood):
    """直接驱动大脑分发 _dispatch_agent → 断言是否落 _do_record。"""
    from core import db
    from services.expense import conversation
    from services.line_binding import line_client, line_expense_qa, line_reply

    calls = {"record": [], "pool": [], "say": []}
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM()),
        mock.patch.object(conversation, "save_pending"),
        mock.patch.object(
            le, "_do_record", side_effect=lambda *a, **k: calls["record"].append(a) or True
        ),
        mock.patch.object(
            line_expense_qa,
            "reply_pool",
            side_effect=lambda rt, kind, *a, **k: calls["pool"].append(kind),
        ),
        mock.patch.object(
            line_reply, "reply_text_context", side_effect=lambda *a, **k: calls["say"].append(a)
        ),
        mock.patch.object(line_client, "t_line", return_value="MSG"),
    ):
        out = le._dispatch_agent(
            {"tenant_id": "T1", "id": "u"}, "rt", "U1", text, "th", "T1", "WS1", understood, None
        )
    return out, calls


class BrainHallucinationGuardTests(unittest.TestCase):
    def test_bind_command_not_recorded_as_expense(self):
        # 「接触绑定」+ 大脑编出 record/amount=50 → 绝不入账(核心事故)→ 落缺金额追问。
        u = {"intent": "record", "speech_act": "statement", "amount": 50, "note": "咖啡"}
        out, calls = _dispatch("接触绑定", u)
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])  # 没有凭空建单
        self.assertTrue(calls["say"])  # 改成追问

    def test_grounded_brain_amount_records(self):
        # 大脑给的金额确在原文 → 正常入账(守卫不误伤真记账)。
        u = {"intent": "record", "speech_act": "statement", "amount": 88, "note": "ของ"}
        out, calls = _dispatch("จ่ายค่าของ 88", u)
        self.assertTrue(out)
        self.assertEqual(len(calls["record"]), 1)


if __name__ == "__main__":
    unittest.main()

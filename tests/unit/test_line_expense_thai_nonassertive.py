# -*- coding: utf-8 -*-
"""泰语问句/假设/否定不被 L1 快路记成支出(反推自场景表 F 类·读码即断的伤账漏洞)。

根因:is_question 原只认 ?/吗呢嘛,不认泰语 ไหม/มั้ย/เหรอ;detect_smalltalk 也不兜。
→「เมื่อกี้จ่าย 50 ใช่ไหม」(问句)、「ถ้าซื้อกาแฟ 100」(假设)走到 L1 快路被直记。
修:is_question 补多语疑问词 + is_nonassertive(假设/否定),一起进 isq 闸,L1 见到不快路记。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.expense import line_quick_entry as lqe
from services.line_binding import line_expense as le


class QuestionDetectTests(unittest.TestCase):
    def test_thai_final_particle_is_question(self):
        for t in ["เมื่อกี้จ่าย 50 ใช่ไหม", "อันนี้แพงมั้ย", "จ่ายไปแล้วเหรอ", "ใช่ไหมคะ"]:
            self.assertTrue(lqe.is_question(t), t)

    def test_thai_interrogative_is_question(self):
        for t in ["เดือนนี้ใช้เท่าไหร่", "ทำไมแพงจัง", "ซื้อที่ไหนดี"]:
            self.assertTrue(lqe.is_question(t), t)

    def test_plain_record_not_question(self):
        for t in ["กาแฟ 65", "ค่าไฟ 500", "咖啡 65"]:
            self.assertFalse(lqe.is_question(t), t)

    def test_legacy_markers_still_work(self):
        self.assertTrue(lqe.is_question("我刚不是花了50吗"))
        self.assertTrue(lqe.is_question("how much?"))


class NonassertiveDetectTests(unittest.TestCase):
    def test_hypothetical(self):
        for t in ["ถ้าซื้อกาแฟ 100 จะเหลือเท่าไหร่", "สมมติว่าจ่าย 200", "如果买100"]:
            self.assertTrue(lqe.is_nonassertive(t), t)

    def test_negation(self):
        for t in ["ไม่ต้องบันทึก 100", "ไม่เอาอันนี้", "别记 50"]:
            self.assertTrue(lqe.is_nonassertive(t), t)

    def test_plain_record_is_assertive(self):
        for t in ["กาแฟ 65", "ซื้อของ 3 อย่าง รวม 250", "ค่าน้ำ 120"]:
            self.assertFalse(lqe.is_nonassertive(t), t)


class _CM:
    def __init__(self, val=None):
        self.val = val

    def __enter__(self):
        return self.val

    def __exit__(self, *a):
        return False


def _run(text):
    """驱动文本路·_do_record 探针·断言 L1 是否误记(无 key → 不进大脑)。"""
    from core import db, workspace_context
    from services.expense import conversation, line_correct_flow, line_l2
    from services.line_binding import line_chat_memory, line_expense_qa, line_reply
    from services.purchase import intake as intake_svc

    calls = {"record": []}
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM(object())),
        mock.patch.object(line_chat_memory, "recent", return_value=[]),
        mock.patch.object(line_chat_memory, "note"),
        mock.patch.object(intake_svc, "line_expense_gate_open", return_value=True),
        mock.patch.object(workspace_context, "default_workspace_id", return_value="WS1"),
        mock.patch.object(line_correct_flow, "route", return_value=False),
        mock.patch.object(conversation, "pop_pending", return_value=None),
        mock.patch.object(conversation, "save_pending"),
        mock.patch.object(line_l2, "resolve_api_key", return_value=None),  # 无 key·不进大脑
        mock.patch.object(line_expense_qa, "reply_summary"),
        mock.patch.object(line_expense_qa, "reply_question"),
        mock.patch.object(line_expense_qa, "reply_pool"),
        mock.patch.object(line_reply, "reply_text_context"),
        mock.patch.object(
            le, "_do_record", side_effect=lambda *a, **k: calls["record"].append(a) or True
        ),
    ):
        out = le.handle_expense_text({"tenant_id": "T1", "id": "u"}, "rt", "U1", text, "th")
    return out, calls


class L1NoFalseRecordTests(unittest.TestCase):
    def test_thai_question_with_amount_not_recorded(self):
        out, calls = _run("เมื่อกี้จ่าย 50 ใช่ไหม")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])  # 问句含 50·不记

    def test_hypothetical_with_amount_not_recorded(self):
        out, calls = _run("ถ้าซื้อกาแฟ 100 จะเหลือเท่าไหร่")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])

    def test_negation_with_amount_not_recorded(self):
        out, calls = _run("ไม่ต้องบันทึก 100")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])

    def test_real_record_still_records(self):
        out, calls = _run("กาแฟ 65")
        self.assertTrue(out)
        self.assertEqual(len(calls["record"]), 1)  # 真记账不回归


if __name__ == "__main__":
    unittest.main()

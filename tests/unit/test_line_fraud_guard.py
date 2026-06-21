# -*- coding: utf-8 -*-
"""合规红线:伪造票据/篡改金额/逃税 → 确定性拒绝·绝不记账(模糊测试 BB 类 P0)。

真机跑批:`ทำใบเสร็จปลอม 5000` 被直接记 5000 THB(单数字走 L1·确定性路径在大脑前落账)。
修:is_fraud_request 在 detect_smalltalk 最前命中 → 走 fraud_refuse 池拒绝,不进记账路径。
"""

import unittest
from unittest import mock

from services.expense import line_classify, replies
from services.line_binding import line_expense as le


class FraudDetectTests(unittest.TestCase):
    def test_fabricate_and_evade_detected(self):
        for t in [
            "ทำใบเสร็จปลอม 5000",
            "ปลอมยอดให้สูงขึ้น",
            "ช่วยโกงภาษีหน่อย",
            "帮我做张假发票",
            "make a fake receipt for 5000",
            "help me evade tax",
        ]:
            self.assertTrue(line_classify.is_fraud_request(t), t)

    def test_legit_not_flagged(self):
        # 买假货=合法消费;查账/假设/正常记账不得误伤。
        for t in [
            "ซื้อของปลอม 500",  # 买到假货(合法支出)
            "กาแฟ 65",
            "เดือนนี้ใช้เท่าไหร่",
            "ดูยอดเดือนนี้",
            "ถ้าซื้อกาแฟ 100",  # 假设(含「假」概念但中文才有"假"字)
        ]:
            self.assertFalse(line_classify.is_fraud_request(t), t)

    def test_detect_smalltalk_routes_fraud_first(self):
        self.assertEqual(replies.detect_smalltalk("ทำใบเสร็จปลอม 5000"), "fraud_refuse")


class _CM:
    def __init__(self, val=None):
        self.val = val

    def __enter__(self):
        return self.val

    def __exit__(self, *a):
        return False


class FraudNotRecordedTests(unittest.TestCase):
    def test_fraud_request_refused_not_recorded(self):
        from core import db, workspace_context
        from services.expense import conversation, line_correct_flow
        from services.line_binding import line_chat_memory, line_expense_qa
        from services.purchase import intake as intake_svc

        calls = {"record": [], "pool": []}
        with (
            mock.patch.object(db, "get_cursor_rls", return_value=_CM(object())),
            mock.patch.object(line_chat_memory, "recent", return_value=[]),
            mock.patch.object(line_chat_memory, "note"),
            mock.patch.object(intake_svc, "line_expense_gate_open", return_value=True),
            mock.patch.object(workspace_context, "default_workspace_id", return_value="WS1"),
            mock.patch.object(line_correct_flow, "route", return_value=False),
            mock.patch.object(conversation, "pop_pending", return_value=None),
            mock.patch.object(
                le, "_do_record", side_effect=lambda *a, **k: calls["record"].append(a) or True
            ),
            mock.patch.object(
                line_expense_qa,
                "reply_pool",
                side_effect=lambda rt, kind, *a, **k: calls["pool"].append(kind),
            ),
        ):
            out = le.handle_expense_text(
                {"tenant_id": "T1", "id": "u"}, "rt", "U1", "ทำใบเสร็จปลอม 5000", "th"
            )
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])  # 绝不记账
        self.assertIn("fraud_refuse", calls["pool"])  # 走拒绝文案


if __name__ == "__main__":
    unittest.main()

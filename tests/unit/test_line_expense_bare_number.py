# -*- coding: utf-8 -*-
"""L1 快路:只发裸数字(「1」)不入账问记啥;有物品名照常记;补答缺金额仍合并入账。

真机 bug:只打「1」「2」「3」各记了 1/2/3 THB 垃圾费用条目。修=裸数字无物品/卖家且非补答缺金额 →
澄清不入账。`_do_record` 在测试里 patch 成探针,隔离路由决策与入账机器。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.expense.expense_draft import ExpenseDraft
from services.line_binding import line_expense as le


class _CM:
    def __init__(self, val=None):
        self.val = val

    def __enter__(self):
        return self.val

    def __exit__(self, *a):
        return False


def _run(text, pend=None):
    from core import db, workspace_context
    from services.expense import conversation, line_correct_flow
    from services.line_binding import line_chat_memory, line_expense_qa
    from services.purchase import intake as intake_svc

    calls = {"record": [], "pool": [], "save": []}
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM(object())),
        mock.patch.object(line_chat_memory, "recent", return_value=[]),
        mock.patch.object(line_chat_memory, "note"),
        mock.patch.object(intake_svc, "line_expense_gate_open", return_value=True),
        mock.patch.object(workspace_context, "default_workspace_id", return_value="WS1"),
        mock.patch.object(line_correct_flow, "route", return_value=False),
        mock.patch.object(conversation, "pop_pending", return_value=pend),
        mock.patch.object(
            conversation, "save_pending", side_effect=lambda *a, **k: calls["save"].append(k)
        ),
        mock.patch.object(
            le, "_do_record", side_effect=lambda *a, **k: calls["record"].append(a) or True
        ),
        mock.patch.object(
            line_expense_qa,
            "reply_pool",
            side_effect=lambda rt, kind, *a, **k: calls["pool"].append(kind),
        ),
    ):
        out = le.handle_expense_text({"tenant_id": "T1", "id": "u"}, "rt", "U1", text, "th")
    return out, calls


class BareNumberTests(unittest.TestCase):
    def test_bare_number_not_recorded_asks_what(self):
        out, calls = _run("1")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])  # 不建单
        self.assertIn("amount_no_item", calls["pool"])

    def test_item_with_amount_records(self):
        out, calls = _run("咖啡 65")
        self.assertTrue(out)
        self.assertEqual(len(calls["record"]), 1)
        self.assertEqual(calls["pool"], [])

    def test_item_without_amount_saves_pending(self):
        out, calls = _run("กาแฟ")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])
        self.assertIn("amount_missing", calls["pool"])
        self.assertEqual(calls["save"][0]["missing"], "amount")
        self.assertEqual(calls["save"][0]["draft"].note, "กาแฟ")

    def test_pending_amount_then_bare_number_merges(self):
        # 缺金额追问后用户补「65」→ 合并入账(draft.amount=65),不被裸数字拦截。
        draft = ExpenseDraft(note="กาแฟ")
        pend = {"missing": "amount", "draft": draft}
        out, calls = _run("65", pend=pend)
        self.assertTrue(out)
        self.assertEqual(len(calls["record"]), 1)
        self.assertEqual(calls["record"][0][5].amount, Decimal("65"))  # 第6位=draft


if __name__ == "__main__":
    unittest.main()

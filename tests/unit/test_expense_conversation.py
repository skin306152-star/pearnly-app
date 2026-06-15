# -*- coding: utf-8 -*-
"""线 B 批3 · 多轮澄清会话态 + 可学习词典(doc 10 §4.3/§4.4)。"""

import unittest
from decimal import Decimal

from services.expense import conversation as conv
from services.expense.expense_draft import ExpenseDraft


class _FakeCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self.calls = []
        self._one = fetchone
        self._all = fetchall or []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class DraftJsonRoundtripTests(unittest.TestCase):
    def test_decimal_survives_roundtrip(self):
        d = ExpenseDraft(amount=Decimal("60.50"), qty=Decimal("3"), category="ค่าอาหาร")
        back = conv._draft_from_json(conv._draft_to_json(d))
        self.assertEqual(back.amount, Decimal("60.50"))
        self.assertEqual(back.qty, Decimal("3"))
        self.assertEqual(back.category, "ค่าอาหาร")


class PendingTests(unittest.TestCase):
    def test_save_scoped_and_upsert(self):
        cur = _FakeCursor()
        conv.save_pending(
            cur,
            line_user_id="U1",
            tenant_id="t1",
            workspace_client_id=7,
            draft=ExpenseDraft(category="ค่าอาหาร"),
            missing="amount",
        )
        sql, params = cur.calls[0]
        self.assertIn("ON CONFLICT (line_user_id) DO UPDATE", sql)
        self.assertEqual(params[0], "U1")
        self.assertEqual(params[1], "t1")
        self.assertEqual(params[2], 7)

    def test_pop_fresh_returns_draft(self):
        draft_json = conv._draft_to_json(ExpenseDraft(category="ค่าอาหาร"))
        cur = _FakeCursor(
            fetchone={
                "tenant_id": "t1",
                "workspace_client_id": 7,
                "draft": draft_json,
                "missing": "amount",
                "fresh": True,
            }
        )
        out = conv.pop_pending(cur, line_user_id="U1")
        self.assertEqual(out["workspace_client_id"], 7)
        self.assertEqual(out["draft"].category, "ค่าอาหาร")
        self.assertEqual(out["missing"], "amount")
        self.assertIn("DELETE FROM line_pending_entry", cur.calls[0][0])

    def test_pop_expired_returns_none(self):
        cur = _FakeCursor(
            fetchone={"tenant_id": "t1", "workspace_client_id": 7, "draft": "{}", "fresh": False}
        )
        self.assertIsNone(conv.pop_pending(cur, line_user_id="U1"))

    def test_pop_missing_returns_none(self):
        self.assertIsNone(conv.pop_pending(_FakeCursor(fetchone=None), line_user_id="U1"))


class LearnedTests(unittest.TestCase):
    def test_lookup_matches_keyword_in_text(self):
        cur = _FakeCursor(
            fetchall=[
                {
                    "keyword": "สตาร์บัคส์",
                    "category_id": "p1",
                    "subcategory_id": "c1",
                    "category_name": "ค่าอาหารและรับรอง",
                    "subcategory_name": "ค่าอาหาร/เครื่องดื่ม",
                },
            ]
        )
        out = conv.lookup_learned(cur, tenant_id="t", workspace_client_id=1, text="สตาร์บัคส์ 120")
        self.assertEqual(out["category_id"], "p1")
        self.assertEqual(out["subcategory_name"], "ค่าอาหาร/เครื่องดื่ม")

    def test_lookup_no_match_returns_none(self):
        cur = _FakeCursor(
            fetchall=[
                {
                    "keyword": "xyz",
                    "category_id": "p1",
                    "subcategory_id": None,
                    "category_name": "a",
                    "subcategory_name": "",
                }
            ]
        )
        self.assertIsNone(
            conv.lookup_learned(cur, tenant_id="t", workspace_client_id=1, text="กาแฟ 60")
        )

    def test_learn_lowercases_keyword_and_scopes(self):
        cur = _FakeCursor()
        conv.learn(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            keyword="Starbucks",
            category_id="p1",
            subcategory_id="c1",
            category_name="X",
            subcategory_name="Y",
        )
        sql, params = cur.calls[0]
        self.assertIn("ON CONFLICT (tenant_id, workspace_client_id, keyword) DO UPDATE", sql)
        self.assertEqual(params[2], "starbucks")  # 关键词归一小写

    def test_learn_ignores_empty_keyword(self):
        cur = _FakeCursor()
        conv.learn(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            keyword="  ",
            category_id="p1",
            subcategory_id=None,
        )
        self.assertEqual(cur.calls, [])


if __name__ == "__main__":
    unittest.main()

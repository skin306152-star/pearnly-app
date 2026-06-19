# -*- coding: utf-8 -*-
"""线 B 批3 · 多轮澄清会话态 + 可学习词典(doc 10 §4.3/§4.4)。"""

import unittest
from decimal import Decimal
from unittest import mock

from services.expense import conversation as conv
from services.expense.expense_draft import ExpenseDraft


class _LearnStore:
    """模拟 expense_learned 表:learn UPSERT + find_exact 精确查 roundtrip(P2A)。"""

    def __init__(self):
        self.rows = {}
        self._last = None

    def execute(self, sql, params=None):
        if "INSERT INTO expense_learned" in sql:
            _tid, _ws, kw, cid, sid, cn, sn = params
            self.rows[kw] = {
                "category_id": cid,
                "subcategory_id": sid,
                "category_name": cn,
                "subcategory_name": sn,
            }
            self._last = None
        elif "FROM expense_learned" in sql and "keyword = %s" in sql:
            self._last = self.rows.get(params[2])
        else:
            self._last = None

    def fetchone(self):
        return self._last


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


class FindExactTests(unittest.TestCase):
    def test_learn_then_find_exact_roundtrip(self):
        cur = _LearnStore()
        conv.learn(
            cur,
            tenant_id="t1",
            workspace_client_id=7,
            keyword="seller:7-eleven",
            category_id="c1",
            subcategory_id="s1",
            category_name="Food",
            subcategory_name="Drink",
        )
        hit = conv.find_exact(cur, tenant_id="t1", workspace_client_id=7, keyword="seller:7-eleven")
        self.assertEqual((hit["category_id"], hit["subcategory_id"]), ("c1", "s1"))
        self.assertEqual(hit["category_name"], "Food")

    def test_find_exact_miss_returns_none(self):
        cur = _LearnStore()
        self.assertIsNone(
            conv.find_exact(cur, tenant_id="t1", workspace_client_id=7, keyword="tax:999")
        )

    def test_find_exact_empty_key_noop(self):
        cur = _LearnStore()
        self.assertIsNone(conv.find_exact(cur, tenant_id="t1", workspace_client_id=7, keyword="  "))


class LearnCategoryWriteBackTests(unittest.TestCase):
    """用户改分类 → 按 税号 + 规范卖家键写回(P2A · 下次同商户优先沿用)。"""

    TREE = [{"id": "c1", "name": "Food", "children": [{"id": "s1", "name": "Drink"}]}]

    def _capture(self, supplier, cid, sid):
        from services.expense import line_correct_data as lcd

        calls = []
        with (
            mock.patch("services.purchase.categories.get_tree", return_value=self.TREE),
            mock.patch(
                "services.expense.conversation.learn",
                side_effect=lambda cur, **kw: calls.append(kw),
            ),
        ):
            lcd.learn_category(object(), tid="t1", ws=7, supplier=supplier, cid=cid, sid=sid)
        return calls

    def test_writes_tax_and_canonical_seller(self):
        calls = self._capture({"name": "7-ELEVEN สาขา 1", "tax_id": "0107542000011"}, "c1", "s1")
        keys = [c["keyword"] for c in calls]
        self.assertIn("tax:0107542000011", keys)
        self.assertIn("seller:7-eleven", keys)  # 各写法归一同键
        self.assertTrue(all(c["category_id"] == "c1" for c in calls))
        self.assertEqual(calls[0]["category_name"], "Food")  # 名从树解析

    def test_no_category_is_noop(self):
        with mock.patch("services.expense.conversation.learn") as ln:
            from services.expense import line_correct_data as lcd

            lcd.learn_category(object(), tid="t1", ws=7, supplier={"name": "x"}, cid=None, sid=None)
            ln.assert_not_called()


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""用户识别关键词规则(Phase 2)· 增删列 + 归类接线的记忆保护。

护栏点:
  1. add_rule 把小类解析成 (父=category, 自身=subcategory);大类则 category=自身。
  2. 写入 source='user_rule',且纠错自学(correction)不许覆盖 user_rule 行(ON CONFLICT WHERE)。
  3. delete/list 只作用于 source='user_rule',不碰隐式纠错行。
  4. hit_counts 任何异常 → 空 dict(锦上添花不拖垮页面)。
"""

import unittest

import core.db  # noqa: F401  单脚本起头须先 import core.db(dal_reexports 循环·app 运行时无此问题)
from services.expense import conversation, keyword_rules


class FakeCursor:
    def __init__(self):
        self.calls: list = []
        self.resolve_row = None
        self.select_rows: list = []
        self.rowcount = 0
        self.raise_on = None
        self._one = None
        self._all: list = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        s = sql.lower()
        if self.raise_on and self.raise_on in s:
            raise RuntimeError("boom")
        if "from expense_categories" in s:
            self._one = self.resolve_row
        elif "select keyword" in s or "select l.subcategory_id" in s:
            self._all = self.select_rows
        else:
            self._one = None
            self._all = []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all

    def has(self, needle: str) -> bool:
        return any(needle in c[0].lower() for c in self.calls)

    def insert_params(self):
        return next(p for s, p in self.calls if "insert into expense_learned" in s.lower())


class AddRuleTests(unittest.TestCase):
    def test_subcategory_maps_parent_and_self(self):
        cur = FakeCursor()
        cur.resolve_row = {
            "sub_name": "ค่าไฟฟ้า",
            "parent_id": "PARENT",
            "cat_name": "ค่าสาธารณูปโภค",
        }
        res = keyword_rules.add_rule(
            cur, tenant_id="t", workspace_client_id=6, target_id="SUB", keyword="GRAB"
        )
        self.assertEqual(res, {"keyword": "grab", "category_id": "PARENT", "subcategory_id": "SUB"})
        p = cur.insert_params()
        self.assertIn("grab", p)  # 关键词已归一小写
        self.assertIn("PARENT", p)
        self.assertIn("SUB", p)
        self.assertIn("user_rule", p)  # 来源标记

    def test_bigcategory_maps_self_no_sub(self):
        cur = FakeCursor()
        cur.resolve_row = {"sub_name": "ค่าเช่า", "parent_id": None, "cat_name": None}
        res = keyword_rules.add_rule(
            cur, tenant_id="t", workspace_client_id=6, target_id="BIG", keyword="rent"
        )
        self.assertEqual(res["category_id"], "BIG")
        self.assertIsNone(res["subcategory_id"])

    def test_empty_keyword_rejected(self):
        cur = FakeCursor()
        cur.resolve_row = {"sub_name": "x", "parent_id": "P", "cat_name": "c"}
        self.assertIsNone(
            keyword_rules.add_rule(
                cur, tenant_id="t", workspace_client_id=6, target_id="SUB", keyword="   "
            )
        )

    def test_missing_target_rejected(self):
        cur = FakeCursor()
        cur.resolve_row = None  # 科目不存在 / 跨套账
        self.assertIsNone(
            keyword_rules.add_rule(
                cur, tenant_id="t", workspace_client_id=6, target_id="ghost", keyword="grab"
            )
        )
        self.assertFalse(cur.has("insert into expense_learned"))


class ListDeleteTests(unittest.TestCase):
    def test_list_only_user_rule(self):
        cur = FakeCursor()
        cur.select_rows = [{"keyword": "grab", "category_id": "P", "subcategory_id": "S"}]
        out = keyword_rules.list_rules(cur, tenant_id="t", workspace_client_id=6)
        self.assertEqual(out, [{"keyword": "grab", "category_id": "P", "subcategory_id": "S"}])
        self.assertTrue(cur.has("source = 'user_rule'"))

    def test_delete_scoped_to_user_rule(self):
        cur = FakeCursor()
        cur.rowcount = 1
        self.assertTrue(
            keyword_rules.delete_rule(cur, tenant_id="t", workspace_client_id=6, keyword="grab")
        )
        self.assertTrue(cur.has("delete from expense_learned"))
        self.assertTrue(cur.has("source = 'user_rule'"))

    def test_delete_empty_noop(self):
        cur = FakeCursor()
        self.assertFalse(
            keyword_rules.delete_rule(cur, tenant_id="t", workspace_client_id=6, keyword="")
        )
        self.assertEqual(cur.calls, [])


class HitCountsTests(unittest.TestCase):
    def test_parses_rows(self):
        cur = FakeCursor()
        cur.select_rows = [{"sid": "S1", "n": 12}, {"sid": "S2", "n": 3}]
        self.assertEqual(
            keyword_rules.hit_counts(cur, tenant_id="t", workspace_client_id=6),
            {"S1": 12, "S2": 3},
        )

    def test_defensive_on_error(self):
        cur = FakeCursor()
        cur.raise_on = "purchase_lines"
        self.assertEqual(keyword_rules.hit_counts(cur, tenant_id="t", workspace_client_id=6), {})


class LearnSourceGuardTests(unittest.TestCase):
    def test_insert_carries_source_and_guard(self):
        cur = FakeCursor()
        conversation.learn(
            cur,
            tenant_id="t",
            workspace_client_id=6,
            keyword="grab",
            category_id="P",
            subcategory_id="S",
            source="user_rule",
        )
        sql = cur.calls[0][0].lower()
        self.assertIn("source", sql)
        # 纠错不许覆盖 user_rule 行的 ON CONFLICT 守卫
        self.assertIn("expense_learned.source <> 'user_rule'", sql)
        self.assertIn("user_rule", cur.insert_params())


if __name__ == "__main__":
    unittest.main()

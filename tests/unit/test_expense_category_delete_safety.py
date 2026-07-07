# -*- coding: utf-8 -*-
"""费用科目删除安全 + 改名级联(费用数据页两级 CRUD 的下游保护)。

背景:purchase_lines/purchase_docs/expense_learned 的 category 列是裸 id 无外键,delete 又是
硬删,直接删 = 历史单据分类悬空。故:
  1. 被历史/记忆用过 → 转停用(is_active=false·含子类),不真删。
  2. 从未用过 → 才真删。
  3. 用量检查覆盖大类自身 + 其所有子类 id。
  4. 分类改名 → 同步改 GL 科目映射(name-keyed·不改就断推送科目)。
"""

import unittest

import core.db  # noqa: F401  单脚本起头须先 import core.db(dal_reexports 循环·app 运行时无此问题)
from services.erp import mappings_store
from services.purchase import categories


class FakeCursor:
    def __init__(self, *, children=(), usage=0):
        self.children = list(children)
        self.usage = usage
        self.calls: list[tuple] = []
        self._one = None
        self._all: list = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        s = sql.lower()
        if "select id from expense_categories" in s and "parent_id" in s:
            self._all = [{"id": c} for c in self.children]
        elif " as n" in s:
            self._one = {"n": self.usage}
        else:
            self._one = None
            self._all = []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all

    def has(self, needle: str) -> bool:
        return any(needle in sql.lower() for sql, _ in self.calls)

    def usage_ids(self):
        sql, params = next((c for c in self.calls if " as n" in c[0].lower()))
        return params[1]  # 第一个 ANY(%s) = purchase_lines.category_id 的 ids


class DeleteSafetyTests(unittest.TestCase):
    def test_soft_delete_when_used(self):
        cur = FakeCursor(children=["c1", "c2"], usage=3)
        res = categories.delete_category(
            cur, tenant_id="t", workspace_client_id=6, category_id="big"
        )
        self.assertEqual(res, {"disabled": True, "deleted": False})
        self.assertTrue(cur.has("update expense_categories set is_active = false"))
        self.assertFalse(cur.has("delete from expense_categories"))

    def test_hard_delete_when_unused(self):
        cur = FakeCursor(children=[], usage=0)
        res = categories.delete_category(
            cur, tenant_id="t", workspace_client_id=6, category_id="lonely"
        )
        self.assertEqual(res, {"disabled": False, "deleted": True})
        self.assertTrue(cur.has("delete from expense_categories"))
        self.assertFalse(cur.has("is_active = false"))

    def test_usage_check_covers_children(self):
        cur = FakeCursor(children=["c1", "c2"], usage=0)
        categories.delete_category(cur, tenant_id="t", workspace_client_id=6, category_id="big")
        ids = cur.usage_ids()
        self.assertIn("big", ids)
        self.assertIn("c1", ids)
        self.assertIn("c2", ids)


class RenameCascadeTests(unittest.TestCase):
    def test_rename_updates_gl_mapping(self):
        cur = FakeCursor()
        mappings_store.rename_category_mapping(cur, "t", "ค่าเช่า", "ค่าเช่าสำนักงาน")
        self.assertTrue(cur.has("update erp_account_mappings"))

    def test_noop_when_name_unchanged(self):
        cur = FakeCursor()
        mappings_store.rename_category_mapping(cur, "t", "x", "x")
        self.assertEqual(cur.calls, [])

    def test_noop_when_empty(self):
        cur = FakeCursor()
        mappings_store.rename_category_mapping(cur, "t", "", "new")
        self.assertEqual(cur.calls, [])


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""可学习费用分类词典。"""

import unittest
from unittest import mock

from services.expense import category_learning as conv


class _LearnStore:
    """模拟 expense_learned 表:learn UPSERT + find_exact 精确查 roundtrip(P2A)。"""

    def __init__(self):
        self.rows = {}
        self._last = None

    def execute(self, sql, params=None):
        if "INSERT INTO expense_learned" in sql:
            _tid, _ws, kw, cid, sid, cn, sn, _src = params
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


class _Store:
    """expense_learned 全模拟:learn 写 + find_exact 精确查 + lookup_learned 全表 fetchall 三合一。"""

    def __init__(self):
        self.rows = {}
        self._one = None
        self._all = []

    def execute(self, sql, params=None):
        if "INSERT INTO expense_learned" in sql:
            _t, _w, kw, cid, sid, cn, sn, _src = params
            self.rows[kw] = {
                "keyword": kw,
                "category_id": cid,
                "subcategory_id": sid,
                "category_name": cn,
                "subcategory_name": sn,
            }
            self._one, self._all = None, []
        elif "keyword = %s" in sql:
            self._one, self._all = self.rows.get(params[2]), []
        else:
            self._one, self._all = None, list(self.rows.values())

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class LookupForTextTests(unittest.TestCase):
    """文字路学习命中(B-1 修):『以后711都记商品』后『711 水』『711 咖啡』仍命中商品,不被品名规则盖。

    根因回归:子串匹配桥不了 711→7-eleven,必须从文本归一出商户键(merchant)查同一把 seller: 键。
    """

    TREE = [{"id": "c1", "name": "商品", "children": [{"id": "s1", "name": "饮料"}]}]

    def _store_711_goods(self):
        from services.purchase import category_learning

        store = _Store()
        with mock.patch("services.purchase.categories.get_tree", return_value=self.TREE):
            category_learning.learn_category(
                store,
                tenant_id="t",
                workspace_client_id=1,
                supplier={"name": "7-ELEVEN สาขา 1", "tax_id": ""},
                category_id="c1",
                subcategory_id="s1",
            )
        return store

    def test_taught_seller_hits_711_water(self):
        hit = conv.lookup_learned_for_text(
            self._store_711_goods(), tenant_id="t", workspace_client_id=1, text="711 水 40"
        )
        self.assertEqual(hit["category_id"], "c1")  # ★不再水费
        self.assertEqual(hit["category_name"], "商品")
        self.assertEqual(hit["subcategory_name"], "饮料")  # 子科目一并落(显示一致)

    def test_taught_seller_hits_711_coffee(self):
        hit = conv.lookup_learned_for_text(
            self._store_711_goods(), tenant_id="t", workspace_client_id=1, text="711 咖啡 55"
        )
        self.assertEqual(hit["category_name"], "商品")  # 同商户·咖啡也归商品(用户教过赢品名)

    def test_store_key_equals_lookup_key(self):
        from services.expense import merchant

        store = self._store_711_goods()
        self.assertIn("seller:7-eleven", store.rows)  # 存键
        self.assertEqual(merchant.canonical_merchant("711"), "7-eleven")  # 查时归一同键

    def test_unlearned_711_returns_none(self):
        # 没学过 → seller 查不到 → None(由上层 _match_category 走品名:咖啡→餐饮·水→水费,不回归)
        hit = conv.lookup_learned_for_text(
            _Store(), tenant_id="t", workspace_client_id=1, text="711 咖啡 55"
        )
        self.assertIsNone(hit)

    def test_substring_keyword_still_works(self):
        # 品名/卖家裸词子串仍命中(ws 学习路不回归)
        store = _Store()
        conv.learn(
            store,
            tenant_id="t",
            workspace_client_id=1,
            keyword="水",
            category_id="c1",
            subcategory_id="s1",
            category_name="商品",
            subcategory_name="饮料",
        )
        hit = conv.lookup_learned_for_text(
            store, tenant_id="t", workspace_client_id=1, text="abc 水 15"
        )
        self.assertEqual(hit["category_id"], "c1")  # 品名裸词跨卖家命中

    def test_lookup_exception_falls_back_no_crash(self):
        class _Boom(_Store):
            def execute(self, sql, params=None):
                if "keyword = %s" in sql:
                    raise RuntimeError("db down")
                super().execute(sql, params)

        hit = conv.lookup_learned_for_text(
            _Boom(), tenant_id="t", workspace_client_id=1, text="711 水"
        )
        self.assertIsNone(hit)  # 守卫吞掉 → 回落 lookup_learned(空表→None)·不崩


if __name__ == "__main__":
    unittest.main()

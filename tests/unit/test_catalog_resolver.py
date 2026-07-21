# -*- coding: utf-8 -*-
"""catalog_resolver 目录解析守门 · 重点验「跨库存+非库存两目录搜」灭重复。

核心回归:商品在【库存】目录已有、【服务】目录没有时,必须命中复用(并回报 kind=stock),
绝不因为只搜服务目录而漏判成 new → 又建一个非库存重复档(泰方报的 bug)。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.erp.express_push.catalog_resolver import (  # noqa: E402
    build_name_index,
    resolve_customer,
    resolve_product,
    resolve_product_indexed,
)

# 套账既有目录:同一批里既有库存品(kind=stock)也有非库存/服务品(kind=non_stock)。
_CATALOG = [
    {"code": "14-01-05", "name": "น้ำแข็งหลอด", "kind": "stock"},
    {"code": "11-05-03", "name": "งานต่อเติมอาคาร", "kind": "non_stock"},
]


class TestResolveProduct(unittest.TestCase):
    def test_reuse_stock_item_across_catalogs(self):
        # ★商品在库存目录已有 → 复用其码 + 回报 kind=stock(不因只搜服务目录而漏判 new)。
        v = resolve_product("น้ำแข็งหลอด", _CATALOG)
        self.assertEqual(v["status"], "reuse")
        self.assertEqual(v["code"], "14-01-05")
        self.assertEqual(v["kind"], "stock")

    def test_reuse_ignores_thai_tone_and_spacing(self):
        # 骨架归一:声调错位 / 空格差异不影响精确复用。
        v = resolve_product("น้ำแข็ง หลอด", _CATALOG)
        self.assertEqual(v["status"], "reuse")
        self.assertEqual(v["code"], "14-01-05")

    def test_reuse_non_stock_item(self):
        v = resolve_product("งานต่อเติมอาคาร", _CATALOG)
        self.assertEqual(v["status"], "reuse")
        self.assertEqual(v["kind"], "non_stock")

    def test_new_when_absent_from_both(self):
        self.assertEqual(resolve_product("ผลิตภัณฑ์ใหม่ที่ไม่มี", _CATALOG)["status"], "new")

    def test_empty_name_is_new(self):
        self.assertEqual(resolve_product("", _CATALOG)["status"], "new")

    def test_empty_catalog_is_new(self):
        self.assertEqual(resolve_product("anything", [])["status"], "new")

    def test_fuzzy_near_match_asks_human(self):
        cat = [{"code": "P1", "name": "ABCDEFGHIJ", "kind": "non_stock"}]
        v = resolve_product("ABCDEFGHIX", cat)  # 10 中 9 同 → 相似度高但非精确
        self.assertEqual(v["status"], "confirm")
        self.assertEqual(v["guess"], "P1")


class TestResolveCustomer(unittest.TestCase):
    _CUST = [{"code": "C001", "name": "บริษัท เอบีซี จำกัด", "tax_id": "0105546015062"}]

    def test_tax_id_exact_wins_even_if_name_differs(self):
        v = resolve_customer("ชื่อใหม่ไม่เหมือน", "0105546015062", self._CUST)
        self.assertEqual(v["status"], "reuse")
        self.assertEqual(v["code"], "C001")
        self.assertEqual(v["reason"], "tax_exact")

    def test_name_match_when_no_tax_id(self):
        v = resolve_customer("บริษัท เอบีซี จำกัด", "", self._CUST)
        self.assertEqual(v["status"], "reuse")


class TestIndexedResolve(unittest.TestCase):
    def test_indexed_exact_hit_o1(self):
        idx = build_name_index(_CATALOG)
        v = resolve_product_indexed("น้ำแข็งหลอด", idx, _CATALOG)
        self.assertEqual(v["status"], "reuse")
        self.assertEqual(v["code"], "14-01-05")
        self.assertEqual(v["kind"], "stock")

    def test_indexed_miss_falls_to_fuzzy(self):
        cat = [{"code": "P1", "name": "ABCDEFGHIJ", "kind": "non_stock"}]
        idx = build_name_index(cat)
        v = resolve_product_indexed("ABCDEFGHIX", idx, cat)  # 非精确 → 落 resolve_product 模糊
        self.assertEqual(v["status"], "confirm")

    def test_indexed_new_when_absent(self):
        idx = build_name_index(_CATALOG)
        self.assertEqual(resolve_product_indexed("ของใหม่ไม่มี", idx, _CATALOG)["status"], "new")


if __name__ == "__main__":
    unittest.main()

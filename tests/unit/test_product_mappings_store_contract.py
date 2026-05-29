# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/erp/product_mappings_store.py
(2026-05-29 R15 从 erp/mappings_store 抽出产品映射 5 函数 · 纯搬家 0 逻辑改 · facade)

锁定:导出 + facade 三处单一来源 + 无 import-time 循环(校验常量 lazy import)。
行为由 test_erp_mappings_store_{contract,coverage} 经 facade 覆盖。
"""

import unittest

import db
from services.erp import mappings_store as store, product_mappings_store as pm

_PUBLIC = [
    "list_erp_product_mappings",
    "upsert_erp_product_mapping",
    "delete_erp_product_mapping",
    "find_erp_product_mappings_batch",
]
_ALL = _PUBLIC + ["_product_name_norm_for_db"]


class ProductMappingsStoreContractTests(unittest.TestCase):
    def test_exports(self):
        for n in _ALL:
            self.assertTrue(callable(getattr(pm, n, None)), f"missing {n}")

    def test_facade_single_source(self):
        for n in _ALL:
            self.assertIs(getattr(store, n), getattr(pm, n), f"store.{n} 漂移")
        for n in _PUBLIC:
            self.assertIs(getattr(db, n), getattr(pm, n), f"db.{n} 漂移")

    def test_no_import_time_cycle(self):
        # 模块级不得 import mappings_store(校验常量走函数内 lazy import)· 否则 facade 循环
        self.assertIsNone(getattr(pm, "mappings_store", None))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · ERP 映射底座 DAL 抽到 services/erp/mappings_store.py

验证:
1. 15 个对外函数都从 services.erp.mappings_store 抽出且可导入
2. db 命名空间 re-export 同一对象(单一来源 · 防漂移)
3. 校验常量随域搬走(私有不外露)· 商品名归一化 helper 私有保留
"""

import unittest

from core import db
from services.erp import mappings_store as store

_MOVED = [
    "ensure_erp_mapping_tables",
    "list_erp_client_mappings",
    "upsert_erp_client_mapping",
    "delete_erp_client_mapping",
    "list_erp_account_mappings",
    "upsert_erp_account_mapping",
    "delete_erp_account_mapping",
    "list_erp_tax_mappings",
    "upsert_erp_tax_mapping",
    "delete_erp_tax_mapping",
    "list_erp_product_mappings",
    "upsert_erp_product_mapping",
    "delete_erp_product_mapping",
    "find_erp_product_mappings_batch",
    "get_mrerp_mappings_bundle",
]


class ErpMappingsStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"mappings_store 缺函数 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")

    def test_validation_constants_and_norm_helper_live_in_service(self):
        # 校验常量随域搬走 · db 命名空间不再暴露(原本就只 db.py 内部用)
        self.assertIn("mrerp", store.ERP_TYPES_VALID)
        self.assertIn("vat_7", store.PEARNLY_TAX_KINDS_VALID)
        self.assertFalse(hasattr(db, "ERP_TYPES_VALID"))
        # 商品名归一化私有 helper 保留在 service
        self.assertTrue(hasattr(store, "_product_name_norm_for_db"))
        self.assertFalse(hasattr(db, "_product_name_norm_for_db"))


if __name__ == "__main__":
    unittest.main()

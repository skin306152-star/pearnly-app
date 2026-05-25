# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 客户实体/供应商分类/买家映射 DAL 抽到 services/clients/store.py

验证 16 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
客户/分类/映射属 tenant 隔离矩阵 · 抽家后既有 buyer_to_client resolver 测试
(patch db.get_cursor + 调 db.try_resolve_buyer_to_client)仍生效。
"""

import unittest

import db
from services.clients import store

_MOVED = [
    "ensure_clients_table",
    "ensure_supplier_categories_table",
    "get_category_for_seller",
    "ensure_buyer_to_client_table",
    "learn_buyer_to_client",
    "try_resolve_buyer_to_client",
    "update_history_client_id",
    "upsert_supplier_category",
    "list_used_categories",
    "count_supplier_mappings",
    "list_clients",
    "get_client",
    "create_client",
    "update_client",
    "delete_client",
    "assign_invoice_to_client",
]


class ClientsStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"clients.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")


if __name__ == "__main__":
    unittest.main()

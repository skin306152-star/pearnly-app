# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · ERP OAuth token DAL 抽到 services/erp/oauth_store.py

验证:
1. 12 个对外函数都从 services.erp.oauth_store 抽出且可导入
2. db 命名空间 re-export 同一对象(单一来源 · 防漂移)
3. base64 helper 私有保留在 service 模块(_b64_encode/_b64_decode 编解码可逆)
"""

import unittest

import db
from services.erp import oauth_store as store

# 对外(被 erp_xero_routes / app.py 通过 db.xxx 调用)的 12 个函数
_MOVED = [
    "ensure_erp_oauth_tables",
    "set_xero_auto_push",
    "get_xero_auto_push",
    "list_tenants_xero_auto_push_on",
    "save_oauth_state",
    "consume_oauth_state",
    "upsert_oauth_token",
    "get_default_oauth_token",
    "list_oauth_tokens",
    "update_oauth_access_token",
    "delete_oauth_tokens",
    "set_default_oauth_token",
]


class ErpOauthStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"oauth_store 缺函数 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")

    def test_b64_helpers_private_and_reversible(self):
        # base64 编解码 helper 保留在 service · 不对外 re-export(私有 _ 前缀)
        self.assertFalse(hasattr(db, "_b64_encode"))
        self.assertTrue(hasattr(store, "_b64_encode"))
        s = "test-token-สวัสดี-123"
        self.assertEqual(store._b64_decode(store._b64_encode(s)), s)


if __name__ == "__main__":
    unittest.main()

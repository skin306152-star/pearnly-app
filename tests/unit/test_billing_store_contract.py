# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 余额追踪 DAL 抽到 services/billing/store.py

验证 2 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
既有 mock.patch("db.get_latest_balance") 的 recon_handlers/salesvat 测试仍生效。
"""

import unittest

import db
from services.billing import store

_MOVED = [
    "ensure_billing_balance_table",
    "get_latest_balance",
]


class BillingStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"billing.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")


if __name__ == "__main__":
    unittest.main()

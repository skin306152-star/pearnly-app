# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 操作/审计日志 DAL 抽到 services/audit/store.py

验证 3 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
"""

import unittest

import db
from services.audit import store

_MOVED = [
    "insert_operation_log",
    "list_operation_logs",
    "list_operation_logs_paged",
]


class AuditStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"audit.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")


if __name__ == "__main__":
    unittest.main()

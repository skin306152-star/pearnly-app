# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 异常栏 DAL 抽到 services/exceptions/store.py

验证 13 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
异常栏属 tenant 隔离矩阵 · 抽家后既有 tenant 隔离测试(patch db.get_cursor)仍生效。
"""

import unittest

from core import db
from services.exceptions import store

_MOVED = [
    "ensure_exceptions_tables",
    "is_exception_whitelisted",
    "insert_exception",
    "list_exceptions",
    "get_exception",
    "resolve_exception",
    "add_exception_whitelist",
    "list_exception_whitelist",
    "delete_exception_whitelist",
    "delete_pending_exceptions_by_history",
    "count_exceptions_by_status_and_rule",
    "count_whitelist_rules",
    "batch_resolve_exceptions",
]


class ExceptionsStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"exceptions.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · RD 校验日限 DAL 抽到 services/rd/store.py

验证 2 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
"""

import unittest

import db
from services.rd import store

_MOVED = [
    "get_rd_daily_usage",
    "increment_rd_daily_usage",
]


class RdStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"rd.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")


if __name__ == "__main__":
    unittest.main()

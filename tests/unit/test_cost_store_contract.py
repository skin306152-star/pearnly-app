# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 成本追踪 DAL 抽到 services/cost/store.py

验证 6 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
"""

import unittest

from core import db
from services.cost import store

_MOVED = [
    "ensure_ocr_cost_log_table",
    "log_ocr_cost",
    "get_cost_overview",
    "get_cost_by_user",
    "get_cost_daily_trend",
    "get_cost_daily_by_engine",
]


class CostStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"cost.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")


if __name__ == "__main__":
    unittest.main()

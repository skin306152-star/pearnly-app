# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/erp/push_log_queries.py
(2026-05-29 R16 从 erp/push_store 抽出推送日志查询/异常/统计 6 函数 · 纯搬家 0 逻辑改 · facade)

锁定:导出 + facade 三处单一来源(store.X / db.X / 子模块.X 同一对象)+ 无循环。
行为由原 test_push_exceptions_queue 等经 facade 覆盖。
"""

import unittest

import db
from services.erp import push_store as store, push_log_queries as q

_NAMES = [
    "delete_push_logs",
    "list_push_logs",
    "get_push_log_detail",
    "classify_push_exception",
    "list_push_exceptions",
    "get_push_stats_today",
]


class PushLogQueriesContractTests(unittest.TestCase):
    def test_exports(self):
        for n in _NAMES:
            self.assertTrue(callable(getattr(q, n, None)), f"missing {n}")

    def test_facade_single_source(self):
        for n in _NAMES:
            self.assertIs(getattr(store, n), getattr(q, n), f"store.{n} 漂移")
            if hasattr(db, n):
                self.assertIs(getattr(db, n), getattr(q, n), f"db.{n} 漂移")

    def test_no_cycle(self):
        self.assertIsNone(getattr(q, "push_store", None))


if __name__ == "__main__":
    unittest.main()

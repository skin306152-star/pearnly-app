# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/erp/push_log_queries.py
(2026-05-29 R16 从 erp/push_store 抽出推送日志查询/异常/统计 6 函数 · 纯搬家 0 逻辑改 · facade)

锁定:导出 + facade 三处单一来源(store.X / db.X / 子模块.X 同一对象)+ 无循环。
行为由原 test_push_exceptions_queue 等经 facade 覆盖。
"""

import unittest

from core import db
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


class DerivePushAccountsTests(unittest.TestCase):
    """response_body → 列表卡科目摘要(Express 队列响应的 accounts)。"""

    def test_dict_body(self):
        out = q._derive_push_accounts(
            {"accounts": [{"acc": "41-01-00-00", "side": "C", "desc": "x"}]}
        )
        self.assertEqual(out, [{"acc": "41-01-00-00", "side": "C", "desc": "x"}])

    def test_json_string_body(self):
        import json

        out = q._derive_push_accounts(json.dumps({"accounts": [{"acc": "21-02-01-00"}]}))
        self.assertEqual(out, [{"acc": "21-02-01-00", "side": "", "desc": ""}])

    def test_none_when_absent_or_bad(self):
        self.assertIsNone(q._derive_push_accounts({"queued": True}))
        self.assertIsNone(q._derive_push_accounts(None))
        self.assertIsNone(q._derive_push_accounts("not json"))
        self.assertIsNone(q._derive_push_accounts({"accounts": [{"side": "C"}]}))  # 无 acc 码


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/exceptions/exceptions_schema.py + exceptions_whitelist.py
(2026-05-29 R13 从 exceptions/store 抽出 schema DDL + 白名单 DAL · 纯搬家 0 逻辑改 · facade)

锁定:导出 + facade 三处单一来源(store.X / db.X / 子模块.X 同一对象)+ 子模块无循环。
行为由原 test_exceptions_store_contract 经 facade 透明覆盖。
"""

import unittest

from core import db
from services.exceptions import store, exceptions_schema as sch, exceptions_whitelist as wl

_WL = [
    "is_exception_whitelisted",
    "add_exception_whitelist",
    "list_exception_whitelist",
    "delete_exception_whitelist",
    "count_whitelist_rules",
]


class ExceptionsWhitelistContractTests(unittest.TestCase):
    def test_exports(self):
        self.assertTrue(callable(getattr(sch, "ensure_exceptions_tables", None)))
        for n in _WL:
            self.assertTrue(callable(getattr(wl, n, None)), f"missing {n}")

    def test_facade_single_source(self):
        self.assertIs(store.ensure_exceptions_tables, sch.ensure_exceptions_tables)
        self.assertIs(db.ensure_exceptions_tables, sch.ensure_exceptions_tables)
        for n in _WL:
            self.assertIs(getattr(store, n), getattr(wl, n), f"store.{n} 漂移")
            self.assertIs(getattr(db, n), getattr(wl, n), f"db.{n} 漂移")

    def test_no_cycle(self):
        self.assertIsNone(getattr(wl, "store", None))
        self.assertIsNone(getattr(sch, "store", None))


if __name__ == "__main__":
    unittest.main()

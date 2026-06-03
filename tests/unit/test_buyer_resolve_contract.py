# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/clients/buyer_resolve.py
(2026-05-29 R12 从 clients/store 抽出买家→客户学习与解析 6 函数 · 纯搬家 0 逻辑改 · facade)

锁定:
  1. buyer_resolve 导出 6 函数 · 不 import clients/store(实现下沉 · 无循环)。
  2. **facade 单一来源**:clients/store.X / buyer_resolve.X 同一对象(store 顶部 re-import)·
     public 5 个 db.X 也同一对象(私有 _buyer_candidates_conflict 不进 db re-export)。
  (行为由 test_resolve_or_create_buyer_client + test_clients_store_contract + test_misc_clients_coverage 经 facade 覆盖)
"""

import unittest

from core import db
from services.clients import store, buyer_resolve as br

_PUBLIC = [
    "ensure_buyer_to_client_table",
    "learn_buyer_to_client",
    "try_resolve_buyer_to_client",
    "resolve_or_create_buyer_client",
    "update_history_client_id",
]
_ALL = _PUBLIC + ["_buyer_candidates_conflict"]


class BuyerResolveContractTests(unittest.TestCase):
    def test_exports(self):
        for n in _ALL:
            self.assertTrue(callable(getattr(br, n, None)), f"missing {n}")

    def test_facade_store_single_source(self):
        for n in _ALL:
            self.assertIs(getattr(store, n), getattr(br, n), f"store.{n} 漂移")

    def test_db_reexports_public(self):
        for n in _PUBLIC:
            self.assertIs(getattr(db, n), getattr(br, n), f"db.{n} 漂移")

    def test_no_cycle(self):
        self.assertIsNone(getattr(br, "store", None))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/workspace/seller_routing.py
(2026-05-29 R14 从 workspace/store 抽出卖方分拣路由 6 函数 · 纯搬家 0 逻辑改 · facade)

锁定:导出 + facade 三处单一来源(store.X / db.X public / 子模块.X 同一对象)+ 无循环。
行为由 test_seller_workspace_routing + test_workspace_store_contract 经 facade 覆盖。
"""

import unittest

from core import db
from services.workspace import store, seller_routing as sr

_PUBLIC = [
    "ensure_seller_route_table",
    "learn_seller_workspace_route",
    "match_workspace_for_seller",
    "update_history_workspace_client_id",
]
_ALL = _PUBLIC + ["_norm_tax", "_match_seller_route_id"]


class SellerRoutingContractTests(unittest.TestCase):
    def test_exports(self):
        for n in _ALL:
            self.assertTrue(callable(getattr(sr, n, None)), f"missing {n}")

    def test_facade_single_source(self):
        for n in _ALL:
            self.assertIs(getattr(store, n), getattr(sr, n), f"store.{n} 漂移")
        for n in _PUBLIC:
            self.assertIs(getattr(db, n), getattr(sr, n), f"db.{n} 漂移")

    def test_no_cycle(self):
        self.assertIsNone(getattr(sr, "store", None))


if __name__ == "__main__":
    unittest.main()

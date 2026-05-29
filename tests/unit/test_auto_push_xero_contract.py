# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/erp/auto_push_xero.py
(2026-05-29 R19 从 erp/auto_push 抽出 Xero 后台自动推路径 · 纯搬家 0 逻辑改 · facade)

锁定:① Xero 自动推函数在 auto_push_xero 且是 coroutine ② auto_push 经 facade re-export 同一对象
(契约 auto_push._auto_push_xero_for_history 不破)③ _trigger_auto_push_all 能解析到它 ④ 无循环依赖。
行为细节由原 auto_push 集成路径覆盖。
"""

import inspect
import unittest

from services.erp import auto_push, auto_push_xero


class AutoPushXeroContractTests(unittest.TestCase):
    def test_xero_fn_lives_in_leaf_and_is_coroutine(self):
        self.assertTrue(inspect.iscoroutinefunction(auto_push_xero._auto_push_xero_for_history))

    def test_facade_single_source(self):
        # auto_push.X 与 auto_push_xero.X 同一对象(re-export · 无 shim 复制)
        self.assertIs(
            auto_push._auto_push_xero_for_history,
            auto_push_xero._auto_push_xero_for_history,
        )

    def test_trigger_resolves_xero(self):
        # _trigger_auto_push_all 留在 auto_push · 运行时经模块全局解析到 re-export 的 Xero 函数
        self.assertIn("_auto_push_xero_for_history", auto_push._trigger_auto_push_all.__globals__)

    def test_leaf_reuses_top_level_db(self):
        import db

        self.assertIs(auto_push_xero.db, db)

    def test_no_cycle(self):
        self.assertIsNone(getattr(auto_push_xero, "auto_push", None))


if __name__ == "__main__":
    unittest.main()

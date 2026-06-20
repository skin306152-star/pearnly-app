# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/erp/auto_push.py
(2026-05-29 从 app.py L1745-2251 抽出 ERP 自动推送编排族 · 纯搬家 0 逻辑改)

锁定:
  1. 模块导出 5 个函数 · loop/编排是 coroutine。
  2. app.py(ocr_recognize / _handle_line_image_ocr 触发)用的 3 个入口与本模块同一对象
     (单一来源 · 无 shim · 铁律#27.4)。
  3. 模块复用顶层 erp_push + db(单一来源 · 防自己再 import 一份 push 适配)。
  4. 行为细节(分组/兜底/dedup/重试/per-invoice 隔离)由 test_auto_push_smart_routing 守。
"""

import inspect
import unittest

from services.erp import auto_push


class AutoPushModuleContractTests(unittest.TestCase):
    def test_exports_five_functions(self):
        for name in (
            "_auto_push_history",
            "_erp_seller_routing_enabled",
            "_persist_push_outcome",
            "_auto_push_batch_for_endpoint",
            "_auto_push_smart_routed",
        ):
            self.assertTrue(callable(getattr(auto_push, name, None)), f"missing: {name}")

    def test_orchestrators_are_coroutines(self):
        self.assertTrue(inspect.iscoroutinefunction(auto_push._auto_push_history))
        self.assertTrue(inspect.iscoroutinefunction(auto_push._auto_push_smart_routed))
        self.assertTrue(inspect.iscoroutinefunction(auto_push._auto_push_batch_for_endpoint))

    def test_app_single_source_three_entrypoints(self):
        import app

        self.assertIs(app._auto_push_history, auto_push._auto_push_history)
        self.assertIs(app._auto_push_smart_routed, auto_push._auto_push_smart_routed)
        self.assertIs(app._erp_seller_routing_enabled, auto_push._erp_seller_routing_enabled)

    def test_module_reuses_top_level_erp_push_and_db(self):
        from core import db
        from services.erp import erp_push

        self.assertIs(auto_push.erp_push, erp_push)
        self.assertIs(auto_push.db, db)

    def test_seller_routing_flag_default_off(self):
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ERP_SELLER_ROUTING", None)
            os.environ.pop("ERP_SELLER_ROUTING_USERS", None)
            self.assertFalse(auto_push._erp_seller_routing_enabled())


if __name__ == "__main__":
    unittest.main()

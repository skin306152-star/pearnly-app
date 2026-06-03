# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/background_loops.py
(2026-05-29 从 app.py L614-801 抽出 · 纯搬家 0 逻辑改)

锁定:
  1. 模块导出 4 个函数 · 两条 loop 是 async coroutine 函数(create_task 要 awaitable)。
  2. app.py lifespan 用的 erp_retry_loop / email_ingest_loop 与本模块同一对象
     (单一来源 · 防 app.py 再拷一份)。
  3. 模块复用顶层 erp_push(单一来源 · 防自己 import 第二份 push 适配)。
  4. db 走运行时 import(模块级 `import db`)· 保 tenant 隔离 monkeypatch 生效。
"""

import asyncio
import inspect
import unittest

from services import background_loops as bl


class BackgroundLoopsContractTests(unittest.TestCase):
    def test_exports_four_callables(self):
        for name in (
            "erp_retry_loop",
            "run_erp_retry_tick",
            "email_ingest_loop",
            "run_email_ingest_tick",
        ):
            self.assertTrue(callable(getattr(bl, name, None)), f"missing/uncallable: {name}")

    def test_loops_are_coroutine_functions(self):
        # create_task 需要 coroutine · 防误改成普通 def
        self.assertTrue(inspect.iscoroutinefunction(bl.erp_retry_loop))
        self.assertTrue(inspect.iscoroutinefunction(bl.email_ingest_loop))
        self.assertTrue(inspect.iscoroutinefunction(bl.run_erp_retry_tick))
        self.assertTrue(inspect.iscoroutinefunction(bl.run_email_ingest_tick))

    def test_startup_uses_single_source_loops(self):
        # REFACTOR-WA-B1 R5:lifespan(起这两条 loop)已抽到 services/startup.py
        from services import startup

        self.assertIs(startup.erp_retry_loop, bl.erp_retry_loop)
        self.assertIs(startup.email_ingest_loop, bl.email_ingest_loop)

    def test_module_reuses_top_level_erp_push_and_db(self):
        from core import db
        from services.erp import erp_push

        self.assertIs(bl.erp_push, erp_push)
        self.assertIs(bl.db, db)

    def test_erp_retry_tick_swallows_db_errors(self):
        """run_erp_retry_tick 外层 try 吞异常(loop 不能因单 tick 炸而死)·
        db.list_logs_due_for_retry 抛错时 tick 不向上 raise。"""
        orig = bl.db.list_logs_due_for_retry

        def _boom(*a, **k):
            raise RuntimeError("boom")

        bl.db.list_logs_due_for_retry = _boom
        try:
            asyncio.run(bl.run_erp_retry_tick())  # 不应 raise
        finally:
            bl.db.list_logs_due_for_retry = orig


if __name__ == "__main__":
    unittest.main()

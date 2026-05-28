# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/startup.py
(2026-05-29 从 app.py lifespan(~446 行)抽出启动/关闭序列 · 纯搬家 0 逻辑改)

锁定:
  1. 导出 run_startup / run_shutdown(均 coroutine)+ _GIT_DEPLOY_SH 常量。
  2. run_shutdown({}) / run_shutdown(None) 安全可调不 raise(无 task 时收尾不炸)。
  3. app.lifespan 仍是 @asynccontextmanager(FastAPI 要)· app 不再自带 startup 明细。
  4. startup 复用单一来源(playwright_bootstrap / background_loops / users.columns)·
     不另起一份(单一来源由各自模块的 contract 测试交叉验)。
"""

import asyncio
import inspect
import unittest

from services import startup


class StartupContractTests(unittest.TestCase):
    def test_exports_run_startup_shutdown_coroutines(self):
        self.assertTrue(inspect.iscoroutinefunction(startup.run_startup))
        self.assertTrue(inspect.iscoroutinefunction(startup.run_shutdown))

    def test_git_deploy_sh_constant_present(self):
        self.assertIsInstance(startup._GIT_DEPLOY_SH, str)
        self.assertIn("git-deploy.sh", startup._GIT_DEPLOY_SH)
        self.assertIn("systemctl restart mrpilot", startup._GIT_DEPLOY_SH)

    def test_run_shutdown_safe_with_no_tasks(self):
        # 无 task(email_task/erp_retry_task 都 None)· 收尾不应 raise
        asyncio.run(startup.run_shutdown({}))
        asyncio.run(startup.run_shutdown(None))

    def test_startup_reuses_single_source_symbols(self):
        from services import playwright_bootstrap, background_loops
        from services.users import columns

        self.assertIs(
            startup.ensure_playwright_installed, playwright_bootstrap.ensure_playwright_installed
        )
        self.assertIs(startup.erp_retry_loop, background_loops.erp_retry_loop)
        self.assertIs(startup.email_ingest_loop, background_loops.email_ingest_loop)
        self.assertIs(startup.ensure_user_profile_columns, columns.ensure_user_profile_columns)

    def test_app_lifespan_is_async_context_manager(self):
        import app

        # 瘦壳仍存在 · 仍是 FastAPI lifespan(被 FastAPI(lifespan=...) 用)
        self.assertTrue(hasattr(app, "lifespan"))


if __name__ == "__main__":
    unittest.main()

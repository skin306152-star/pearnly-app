# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/playwright_bootstrap.py
(2026-05-29 从 app.py L162-480 抽出 · 纯搬家 0 逻辑改)

锁定:
  1. 模块导出 3 个公开函数(probe_chromium_launch / ensure_playwright_installed /
     read_playwright_status)· 防搬迁改名漏导出。
  2. read_playwright_status() 无副作用安全可调:状态文件缺失时返 dict ·
     含 playwright_installed / chromium_installed 等契约 key(给 /api/version 暴露)。
  3. app.py lifespan 调的 ensure_playwright_installed 与本模块是同一对象
     (单一来源 · 防 app.py 再拷一份漂移)。
  4. admin_diagnostics_routes 用的 read_playwright_status 与本模块同一对象
     (/api/admin/diagnostics/runtime 走单一来源)。
"""

import unittest

from services import playwright_bootstrap as pb


class PlaywrightBootstrapContractTests(unittest.TestCase):
    def test_module_exports_three_public_funcs(self):
        for name in (
            "probe_chromium_launch",
            "ensure_playwright_installed",
            "read_playwright_status",
        ):
            self.assertTrue(callable(getattr(pb, name, None)), f"missing/uncallable: {name}")

    def test_read_status_returns_contract_dict_when_file_missing(self):
        """状态快照文件不存在时也安全返 dict · 含必备 key · 不 raise"""
        out = pb.read_playwright_status()
        self.assertIsInstance(out, dict)
        for key in (
            "playwright_installed",
            "chromium_installed",
            "chromium_can_launch",
            "playwright_version",
            "deploy_log_tail",
            "sentinels",
        ):
            self.assertIn(key, out)
        # 缺失/读不到时这两个必须是布尔(bool(...) 包裹)
        self.assertIsInstance(out["playwright_installed"], bool)
        self.assertIsInstance(out["chromium_installed"], bool)

    def test_startup_uses_single_source_ensure(self):
        # REFACTOR-WA-B1 R5:lifespan 启动序列已抽到 services/startup.py · 它是消费方
        from services import startup

        self.assertIs(startup.ensure_playwright_installed, pb.ensure_playwright_installed)

    def test_admin_diagnostics_uses_single_source_read_status(self):
        from routes import admin_diagnostics_routes as adr

        self.assertIs(adr.read_playwright_status, pb.read_playwright_status)


if __name__ == "__main__":
    unittest.main()

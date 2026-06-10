# -*- coding: utf-8 -*-
"""设置页模块管理路由守门测试(POS 项目 · C3 · 批2:require_perm 统一执行点)。

锁定:4 条路由契约 · app.py include · POS 信封 + settings.modules.manage 带码守门
(收银员/低权限成员不可调模块管理)。"""

import inspect
import unittest

import routes.pos_modules_routes as mod
from routes.pos_modules_routes import router

EXPECTED = {
    ("GET", "/api/pos/admin/modules"),
    ("PUT", "/api/pos/admin/modules"),
    ("GET", "/api/pos/admin/onboarding-state"),
    ("GET", "/api/pos/admin/business-presets"),
}


class PosModulesRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths)

    def test_all_handlers_perm_gated(self):
        for fn in (
            mod.api_get_modules,
            mod.api_set_module,
            mod.api_onboarding_state,
            mod.api_business_presets,
        ):
            self.assertIn(
                'require_perm_pos_tid(request, "settings.modules.manage")',
                inspect.getsource(fn),
                fn.__name__,
            )

    def test_uses_envelope(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "PosError"))


if __name__ == "__main__":
    unittest.main()

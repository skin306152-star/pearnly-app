# -*- coding: utf-8 -*-
"""模块视图 + onboarding 路由守门测试(平台业态套餐 · 按域名分功能收口)。

锁定:
  1. router 只注册 GET /api/me/modules + PUT /api/me/onboarding —— 逐模块 toggle 路由
     已下架(客户侧模块自选与「域名分功能」冲突 · Zihao 2026-07-12 拍板),不许回潮
  2. app.py include_router 真挂上,且 toggle 路径不复活
  3. onboarding 走 settings.modules.manage 权限码 · 读用 require_tenant
  4. onboarding 锁死 firm-only:非 firm 业态源码级拒绝(防老前端/脚本改回旧业态标签)
"""

import inspect
import unittest

from routes import modules_routes
from routes.modules_routes import router

EXPECTED = {
    ("GET", "/api/me/modules"),
    ("PUT", "/api/me/onboarding"),
}


class ModulesRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_modules_router_and_toggle_stays_dead(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/me/modules", paths)
        self.assertIn("/api/me/onboarding", paths)
        # 防回潮:设置页逐模块开关路由已删,任何路由文件都不许再挂这个路径
        self.assertNotIn("/api/me/modules/{module_key}", paths)

    def test_write_endpoint_requires_modules_manage_perm(self):
        # onboarding 须走 settings.modules.manage(owner/admin · 挡会计/录入/收银员)
        src = inspect.getsource(modules_routes.api_onboarding)
        self.assertIn('require_perm_pos_tid(request, "settings.modules.manage")', src)
        # 读接口用 require_tenant(任意已登录主体)
        self.assertIn("require_tenant", inspect.getsource(modules_routes.api_get_modules))

    def test_onboarding_locked_to_firm(self):
        # 业态自选已下架:非 firm 一律 platform.business_type_locked(唯一合法调用 =
        # 新注册向导静默套 firm)。pos_only 等只走运营侧直调 presets.apply_preset。
        src = inspect.getsource(modules_routes.api_onboarding)
        self.assertIn('!= "firm"', src)
        self.assertIn("platform.business_type_locked", src)

    def test_toggle_endpoint_removed_from_module(self):
        # 函数本体也不许残留(路由级防回潮之外的源码级双保险)
        self.assertFalse(hasattr(modules_routes, "api_toggle_module"))
        self.assertFalse(hasattr(modules_routes, "ModuleToggleRequest"))

    def test_modules_view_exposes_needs_onboarding(self):
        # 视图须含 needs_onboarding(前端首进自动起引导向导的判据 · 向导静默套 firm)
        src = inspect.getsource(modules_routes._modules_view)
        self.assertIn("needs_onboarding", src)


if __name__ == "__main__":
    unittest.main()

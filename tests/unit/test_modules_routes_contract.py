# -*- coding: utf-8 -*-
"""模块开关 + 业态 onboarding 路由守门测试(POS PO-A1 / 平台业态套餐)。

锁定:
  1. router 注册 GET /api/me/modules + PUT /api/me/onboarding + PUT /api/me/modules/{key} 契约
  2. app.py include_router 真挂上
  3. 写接口(onboarding/toggle)用 require_account_owner(owner 专属)· 读用 require_tenant
"""

import inspect
import unittest

from routes import modules_routes
from routes.modules_routes import router

EXPECTED = {
    ("GET", "/api/me/modules"),
    ("PUT", "/api/me/onboarding"),
    ("PUT", "/api/me/modules/{module_key}"),
}


class ModulesRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_modules_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/me/modules", paths)
        self.assertIn("/api/me/onboarding", paths)
        self.assertIn("/api/me/modules/{module_key}", paths)

    def test_write_endpoints_require_account_owner(self):
        # 写接口源码须调 require_account_owner(比 require_owner 更严 · 挡受邀成员)
        for fn in (modules_routes.api_onboarding, modules_routes.api_toggle_module):
            src = inspect.getsource(fn)
            self.assertIn("require_account_owner", src)
        # 读接口用 require_tenant(任意已登录主体)
        self.assertIn("require_tenant", inspect.getsource(modules_routes.api_get_modules))

    def test_modules_view_exposes_needs_onboarding(self):
        # 视图须含 needs_onboarding(前端首进自动弹业态选择的判据)
        src = inspect.getsource(modules_routes._modules_view)
        self.assertIn("needs_onboarding", src)


if __name__ == "__main__":
    unittest.main()

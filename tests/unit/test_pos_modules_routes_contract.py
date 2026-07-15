# -*- coding: utf-8 -*-
"""设置页模块管理路由守门测试(POS 项目 · C3 · Phase3:自助模块管理封死)。

锁定:
  1. 4 条路由壳仍在(保路由注册,不动 app include)· app.py 真挂上
  2. 自助模块管理封死(各是各的:功能跟入口走)—— PUT 逐模块 toggle 影子活体 +
     GET 读侧 + business-presets 孤悬端点(均零前端消费者)一律 403 pos.forbidden,
     不再走 settings.modules.manage 自助流(照 test_modules_routes_contract 锁
     /api/me/modules/{key} 已删的封死范式)
  3. onboarding-state(开通向导唯一合法读)仍带 settings.modules.manage 码守门"""

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

# 已封死(403)的自助模块管理端点句柄
SEALED = (mod.api_get_modules, mod.api_set_module, mod.api_business_presets)


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

    def test_self_service_module_admin_sealed_403(self):
        # 三端点封死:抛 pos.forbidden 403,且不再自助走 settings.modules.manage
        for fn in SEALED:
            src = inspect.getsource(fn)
            self.assertIn('raise PosError("pos.forbidden", 403)', src, fn.__name__)
            self.assertNotIn("settings.modules.manage", src, fn.__name__)

    def test_toggle_store_write_gone(self):
        # 自助写库路径彻底移除:不再 import modules_store、不再开写事务游标
        text = inspect.getsource(mod)
        self.assertNotIn("modules_store", text)
        self.assertNotIn("commit=True", text)

    def test_onboarding_state_still_perm_gated(self):
        # 开通向导唯一合法读接口仍带码守门(未被误封)
        self.assertIn(
            'require_perm_pos_tid(request, "settings.modules.manage")',
            inspect.getsource(mod.api_onboarding_state),
        )

    def test_uses_envelope(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "PosError"))


if __name__ == "__main__":
    unittest.main()

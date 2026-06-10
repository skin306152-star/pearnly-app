# -*- coding: utf-8 -*-
"""餐厅 POS 路由守门测试(餐厅 POS · PO-R · 批2:管理端走 require_perm 统一执行点)。

锁定:前台 14 + 管理 8 路由 path+method 契约 · app.py include · POS 信封 + 模块守门 +
前台收银员 token(pos_auth)/ 管理 pos.admin.manage 带码守门。"""

import inspect
import unittest

import routes.pos_restaurant_admin_routes as admin_mod
import routes.pos_restaurant_routes as front_mod
from routes.pos_restaurant_admin_routes import router as admin_router
from routes.pos_restaurant_routes import router as front_router

FRONT_EXPECTED = {
    ("GET", "/api/pos/restaurant/tables"),
    ("POST", "/api/pos/restaurant/tables/{table_id}/open"),
    ("GET", "/api/pos/restaurant/sessions/{session_id}"),
    ("POST", "/api/pos/restaurant/sessions/{session_id}/lines"),
    ("PATCH", "/api/pos/restaurant/sessions/{session_id}/lines/{line_id}"),
    ("DELETE", "/api/pos/restaurant/sessions/{session_id}/lines/{line_id}"),
    ("POST", "/api/pos/restaurant/sessions/{session_id}/send-kitchen"),
    ("POST", "/api/pos/restaurant/sessions/{session_id}/cancel"),
    ("POST", "/api/pos/restaurant/sessions/{session_id}/request-bill"),
    ("GET", "/api/pos/restaurant/sessions/{session_id}/bill"),
    ("POST", "/api/pos/restaurant/sessions/{session_id}/checkout"),
    ("GET", "/api/pos/restaurant/kitchen"),
    ("POST", "/api/pos/restaurant/kot/{kot_id}/status"),
    ("POST", "/api/pos/restaurant/kot/items/{line_id}/status"),
}

ADMIN_EXPECTED = {
    ("GET", "/api/pos/admin/restaurant/areas"),
    ("POST", "/api/pos/admin/restaurant/areas"),
    ("PATCH", "/api/pos/admin/restaurant/areas/{area_id}"),
    ("DELETE", "/api/pos/admin/restaurant/areas/{area_id}"),
    ("GET", "/api/pos/admin/restaurant/tables"),
    ("POST", "/api/pos/admin/restaurant/tables"),
    ("PATCH", "/api/pos/admin/restaurant/tables/{table_id}"),
    ("DELETE", "/api/pos/admin/restaurant/tables/{table_id}"),
}


def _routes(router) -> set:
    got = set()
    for r in router.routes:
        for m in getattr(r, "methods", set()) or set():
            if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                got.add((m, r.path))
    return got


class RestaurantRoutesContractTests(unittest.TestCase):
    def test_front_router_routes(self):
        self.assertEqual(_routes(front_router), FRONT_EXPECTED)

    def test_admin_router_routes(self):
        self.assertEqual(_routes(admin_router), ADMIN_EXPECTED)

    def test_app_includes_both(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in FRONT_EXPECTED | ADMIN_EXPECTED:
            self.assertIn(p, paths, f"restaurant route missing from app: {p}")

    def test_uses_pos_envelope_and_gate(self):
        for mod in (front_mod, admin_mod):
            self.assertTrue(hasattr(mod, "ok"))
            self.assertTrue(hasattr(mod, "assert_module_enabled"))
            self.assertTrue(hasattr(mod, "PosError"))
            self.assertTrue(hasattr(mod, "require_workspace"))
        # 前台 = 收银员 token(pos_auth);管理 = 权限码统一执行点(收银员 403)
        self.assertTrue(hasattr(front_mod, "pos_auth"))
        self.assertIn(
            'require_perm_pos(request, "pos.admin.manage")',
            inspect.getsource(admin_mod._owner_ctx),
        )


if __name__ == "__main__":
    unittest.main()

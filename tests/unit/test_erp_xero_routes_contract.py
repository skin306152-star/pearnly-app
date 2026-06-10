# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · ERP 连接器聚合 + Xero 8 路由从 app.py 抽到 erp_xero_routes.py。

锁定(防搬迁回归 + 权限批2):
  1. router 注册的 8 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 权限批2:4 处 owner 守门换统一执行点 require_perm(request, "settings.org.edit")·
     复用 services/authz/deps 同一份对象 · 旧门 _require_owner_or_super 不许复活
  4. _tid / get_current_user_from_request 单一来源(防鉴权失踪)
  5. _ensure_fresh_xero_token 单一来源在 erp_xero_routes · app.py 自动推送复用的是同一个对象
"""

import inspect
import unittest

from routes import erp_xero_routes
from core import route_helpers
from routes.erp_xero_routes import router


class ErpXeroRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/erp/connectors/status"),
            ("GET", "/api/erp/xero/auth/start"),
            ("GET", "/api/erp/xero/auth/callback"),
            ("GET", "/api/erp/xero/status"),
            ("POST", "/api/erp/xero/auto-push"),
            ("POST", "/api/erp/xero/select_org"),
            ("POST", "/api/erp/xero/disconnect"),
            ("POST", "/api/erp/xero/push/{history_id}"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_erp_xero_router(self):
        """防 include_router 漏挂 · app 必须能路由到连接器/Xero"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/erp/connectors/status", paths)
        self.assertIn("/api/erp/xero/auth/callback", paths)
        self.assertIn("/api/erp/xero/push/{history_id}", paths)

    def test_owner_guard_uses_require_perm_settings_org_edit(self):
        """权限批2:4 处 owner 守门(auth/start·auto-push·select_org·disconnect)换统一执行点 ·
        require_perm 复用 services/authz/deps 同一份对象 · 码钉 settings.org.edit ·
        旧门 _require_owner_or_super 不许在本模块复活"""
        from services.authz import deps

        self.assertIs(erp_xero_routes.require_perm, deps.require_perm)
        self.assertFalse(hasattr(erp_xero_routes, "_require_owner_or_super"))
        src = inspect.getsource(erp_xero_routes)
        self.assertEqual(
            src.count('require_perm(request, "settings.org.edit")'),
            4,
            "owner 守门 require_perm(settings.org.edit) 接线数应为 4",
        )

    def test_tid_and_auth_single_source(self):
        """_tid / get_current_user_from_request 单一来源(防鉴权失踪)"""
        from core import auth

        self.assertIs(erp_xero_routes._tid, route_helpers._tid)
        self.assertIs(
            erp_xero_routes.get_current_user_from_request,
            auth.get_current_user_from_request,
        )

    def test_ensure_fresh_token_single_source(self):
        """_ensure_fresh_xero_token 单一来源 = erp_xero_routes · ERP 自动推送编排
        (services/erp/auto_push.py · REFACTOR-WA-B1 抽出)在函数内 lazy import 复用本模块同一对象,
        不在模块级另起一份(否则这里会抓到重复定义)。"""
        from services.erp import auto_push

        self.assertTrue(callable(erp_xero_routes._ensure_fresh_xero_token))
        self.assertFalse(
            hasattr(auto_push, "_ensure_fresh_xero_token"),
            "auto_push 不应在模块级重定义 _ensure_fresh_xero_token · 应 lazy import erp_xero_routes 同一对象",
        )


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""B4 + P3 守门:workspace_routes 路由契约。

锁定:
  1. /api/workspace/* 路由按预期 path+method 注册(GET/POST/PUT-endpoint +
     P3 新增 PATCH 编辑 / DELETE 软删归档);
  2. router 已挂到 app(include_router);
  3. DELETE 仅限单账套主体软删归档 · 不得新增批量/破坏性删除路由。
"""

import unittest

from routes.workspace_routes import router as workspace_router


def _route_set(router):
    out = set()
    for r in router.routes:
        methods = getattr(r, "methods", set()) or set()
        for m in methods:
            if m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                out.add((m, r.path))
    return out


class WorkspaceRouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        rs = _route_set(workspace_router)
        self.assertIn(("GET", "/api/workspace/clients"), rs)
        self.assertIn(("POST", "/api/workspace/clients"), rs)
        self.assertIn(("PUT", "/api/workspace/clients/{workspace_client_id}/endpoint"), rs)
        # P3(2026-05-27 · Zihao 拍板)· 账套主体管理页:补编辑 + 归档(软删)路由
        self.assertIn(("PATCH", "/api/workspace/clients/{workspace_client_id}"), rs)
        self.assertIn(("DELETE", "/api/workspace/clients/{workspace_client_id}"), rs)

    def test_delete_is_soft_archive_only(self):
        # P3:DELETE 仅允许出现在单个账套主体的归档路由上(软删 is_active=False)·
        # 不得出现批量/破坏性删除路由(发票归属链、seller 路由记忆都靠软删保全)。
        rs = _route_set(workspace_router)
        delete_paths = {p for (m, p) in rs if m == "DELETE"}
        self.assertEqual(
            delete_paths,
            {"/api/workspace/clients/{workspace_client_id}"},
            "DELETE 仅限单账套主体归档(软删)· 不得新增其它破坏性删除路由",
        )


class WorkspaceRouterMountedTests(unittest.TestCase):
    def test_mounted_in_app(self):
        # 轻量:确认 app 能 import 且包含 workspace 路由(不启动服务)
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workspace/clients", paths)


if __name__ == "__main__":
    unittest.main()

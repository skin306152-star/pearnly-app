# -*- coding: utf-8 -*-
"""B4 守门:workspace_routes 路由契约(非破坏版)。

锁定:
  1. 3 个 /api/workspace/* 路由按预期 path+method 注册;
  2. router 已挂到 app(include_router);
  3. 不碰任何上传/推送/对账主路径(本测试只断言新增路由存在 · 不改旧行为)。
"""

import unittest

from workspace_routes import router as workspace_router


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

    def test_no_unexpected_destructive_routes(self):
        # 非破坏版:不应有 DELETE/批量等破坏性路由
        rs = _route_set(workspace_router)
        self.assertFalse(
            any(m == "DELETE" for (m, _p) in rs),
            "B4 非破坏版不应含 DELETE 路由",
        )


class WorkspaceRouterMountedTests(unittest.TestCase):
    def test_mounted_in_app(self):
        # 轻量:确认 app 能 import 且包含 workspace 路由(不启动服务)
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workspace/clients", paths)


if __name__ == "__main__":
    unittest.main()

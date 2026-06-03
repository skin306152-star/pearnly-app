# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 泰国 RD 税务 4 路由从 app.py 抽到 rd_routes.py。

锁定(防搬迁回归):
  1. router 注册的 4 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. _check_rd_access 复用 route_helpers._plan_permissions(单一来源)·
     扁平化下永远放行(can_verify_tax=True · rd_daily_limit=None)
  4. RdQueryRequest 字段契约(branch 默认 0)
"""

import unittest

from core import route_helpers
from routes.rd_routes import RdQueryRequest, _check_rd_access, router


class RdRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m == "POST":
                    got.add((m, r.path))
        expected = {
            ("POST", "/api/rd/verify"),
            ("POST", "/api/rd/lookup"),
            ("POST", "/api/v1/rd/verify"),
            ("POST", "/api/v1/rd/lookup"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_rd_router(self):
        """防 include_router 漏挂 · app 必须能路由到 rd"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/rd/verify", paths)
        self.assertIn("/api/v1/rd/lookup", paths)

    def test_check_rd_access_uses_plan_permissions(self):
        """_check_rd_access 依赖 route_helpers._plan_permissions · 扁平化下放行"""
        self.assertIs(
            _check_rd_access.__globals__["_plan_permissions"], route_helpers._plan_permissions
        )
        # 扁平化:can_verify_tax=True 且 rd_daily_limit=None → 无日限直接 return(不抛)
        self.assertIsNone(_check_rd_access({"id": "u1", "plan": "free"}))

    def test_rd_query_request_fields(self):
        """RdQueryRequest 字段契约 · branch 默认 0"""
        m = RdQueryRequest(tax_id="0105556000000")
        self.assertEqual(m.branch, 0)
        self.assertEqual(set(RdQueryRequest.model_fields.keys()), {"tax_id", "branch"})


if __name__ == "__main__":
    unittest.main()

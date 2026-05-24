# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 员工管理路由从 app.py 抽到 team_routes.py。

锁定(防搬迁回归):
  1. team_router 注册的 7 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. admin 410 tombstone(/api/admin/employees/{id}/active)仍由 app.py 提供(未误删)
  4. EmployeeToggleRequest 从 team_routes import 回去给 admin stub 用(单一来源 · 防再各自拷贝漂移)
"""

import unittest

from team_routes import EmployeeToggleRequest, router


class TeamRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/team/employees"),
            ("GET", "/api/team/employees/{employee_id}/assignments"),
            ("POST", "/api/team/employees/{employee_id}/assignments"),
            ("POST", "/api/team/employees"),
            ("POST", "/api/team/employees/{employee_id}/reset-password"),
            ("DELETE", "/api/team/employees/{employee_id}"),
            ("PATCH", "/api/team/employees/{employee_id}/active"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_team_router(self):
        """防 include_router 漏挂 · app 必须能路由到 team"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/team/employees", paths)
        self.assertIn("/api/team/employees/{employee_id}/reset-password", paths)

    def test_admin_employee_stub_stays_in_app(self):
        """admin 410 tombstone 属 admin 组 · 仍由 app.py 提供(未误删)"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/employees/{employee_id}/active", paths)

    def test_employee_toggle_request_single_source(self):
        """app.py 的 admin stub 用的 EmployeeToggleRequest 必须是 team_routes 那个对象
        (单一来源 · 防接力 agent 又在 app.py 各自拷一份漂移)"""
        import app

        self.assertIs(app.EmployeeToggleRequest, EmployeeToggleRequest)
        self.assertEqual(EmployeeToggleRequest.model_fields.keys(), {"is_active"})


if __name__ == "__main__":
    unittest.main()

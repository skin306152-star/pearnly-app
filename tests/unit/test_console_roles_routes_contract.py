# -*- coding: utf-8 -*-
"""console_roles_routes 契约守门(G3):路径/方法齐全 + 写口挂正确权限码 + role.* 落审计。

不起服务,只查 router 路由表与 handler 源码(同 test_team_store_contract 套路)。
"""

import inspect
import unittest

import routes.console_roles_routes as mod
from routes.console_roles_routes import router


def _routes():
    out = {}
    for r in router.routes:
        for m in r.methods:
            if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                out[(m, r.path)] = r.endpoint
    return out


class RouteShapeTests(unittest.TestCase):
    def setUp(self):
        self.routes = _routes()

    def test_all_five_endpoints_registered(self):
        for key in (
            ("GET", "/api/team/roles/custom"),
            ("POST", "/api/team/roles"),
            ("PATCH", "/api/team/roles/{role_id}"),
            ("DELETE", "/api/team/roles/{role_id}"),
            ("PUT", "/api/team/members/{uid}/role-assign"),
        ):
            self.assertIn(key, self.routes, f"缺路由 {key}")

    def test_does_not_collide_with_system_roles_get(self):
        # 系统角色 GET /api/team/roles 归 console_team_routes,本文件不得重定义
        self.assertNotIn(("GET", "/api/team/roles"), self.routes)


class PermissionGateTests(unittest.TestCase):
    def test_writes_require_edit_role_perm(self):
        for fn in (
            mod.create_custom_role,
            mod.update_custom_role,
            mod.delete_custom_role,
            mod.assign_role,
        ):
            src = inspect.getsource(fn)
            self.assertIn('require_perm(request, "team.member.edit_role")', src, fn.__name__)

    def test_list_requires_view_perm(self):
        self.assertIn(
            'require_perm(request, "team.member.view")',
            inspect.getsource(mod.list_custom_roles),
        )


class AuditTrailTests(unittest.TestCase):
    def test_create_update_delete_assign_logged(self):
        expect = {
            mod.create_custom_role: "role.create",
            mod.update_custom_role: "role.update",
            mod.delete_custom_role: "role.delete",
            mod.assign_role: "role.change",
        }
        for fn, action in expect.items():
            src = inspect.getsource(fn)
            self.assertIn("_log_op(", src, fn.__name__)
            self.assertIn(f'"{action}"', src, fn.__name__)


if __name__ == "__main__":
    unittest.main()

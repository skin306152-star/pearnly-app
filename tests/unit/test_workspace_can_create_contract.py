# -*- coding: utf-8 -*-
"""N1 P0-1(客户没有出生地)守门:GET /api/workspace/clients/can-create 是「+新建客户」
按钮的显隐探针——state honesty(没权限不给一个点了才 403 的假门)。锁定:①端点注册且
先于 /{workspace_client_id} 之前(否则 "can-create" 被当 int 路径解析炸 422)②权限
真实来源于 actor_has_perm(settings.workspace.manage),不是前端自己猜角色。
"""

from __future__ import annotations

import unittest
from unittest import mock

from routes import workspace_routes as wr
from routes.workspace_routes import router as workspace_router

_USER = {"id": "u1", "tenant_id": "t-1", "role": "member", "is_super_admin": False}


def _route_order(router, path_suffix: str) -> int:
    for i, r in enumerate(router.routes):
        if getattr(r, "path", "").endswith(path_suffix):
            return i
    raise AssertionError(f"route not found: {path_suffix}")


class RouteContractTests(unittest.TestCase):
    def test_can_create_registered(self):
        paths = {getattr(r, "path", None) for r in workspace_router.routes}
        self.assertIn("/api/workspace/clients/can-create", paths)

    def test_can_create_registered_before_int_id_route(self):
        # FastAPI 按注册顺序匹配路径——can-create 必须排在 {workspace_client_id} 之前,
        # 否则 "can-create" 会被当整数路径参数解析,422 而不是命中这个端点。
        idx_can_create = _route_order(workspace_router, "/api/workspace/clients/can-create")
        idx_by_id = _route_order(workspace_router, "/api/workspace/clients/{workspace_client_id}")
        self.assertLess(idx_can_create, idx_by_id)

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workspace/clients/can-create", paths)


class CanCreateBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def test_allowed_true_when_actor_has_perm(self):
        with (
            mock.patch.object(wr, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(wr, "actor_has_perm", return_value=True) as perm_mock,
        ):
            out = await wr.can_create_workspace_client(mock.Mock())
        self.assertEqual(out, {"allowed": True})
        # 判据必须是 settings.workspace.manage(owner/admin 专属码),不是别的码。
        perm_mock.assert_called_once()
        self.assertEqual(perm_mock.call_args.args[-1], "settings.workspace.manage")

    async def test_allowed_false_when_actor_lacks_perm(self):
        with (
            mock.patch.object(wr, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(wr, "actor_has_perm", return_value=False),
        ):
            out = await wr.can_create_workspace_client(mock.Mock())
        self.assertEqual(out, {"allowed": False})


if __name__ == "__main__":
    unittest.main()

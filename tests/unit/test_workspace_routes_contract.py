# -*- coding: utf-8 -*-
"""B4 + P3 守门:workspace_routes 路由契约。

锁定:
  1. /api/workspace/* 路由按预期 path+method 注册(GET/POST/PUT-endpoint +
     P3 新增 PATCH 编辑 / DELETE 软删归档);
  2. router 已挂到 app(include_router);
  3. DELETE 仅限单账套主体软删归档 · 不得新增批量/破坏性删除路由。
"""

import unittest
from unittest import mock

from fastapi import HTTPException

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
        # 用户引导闭环(2026-06-11)· 公司资料页读单个 + 建企业主体税号带出
        self.assertIn(("GET", "/api/workspace/clients/{workspace_client_id}"), rs)
        self.assertIn(("GET", "/api/workspace/tax-lookup"), rs)

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


class TaxLookupBehaviorTests(unittest.IsolatedAsyncioTestCase):
    """税号带出:复用 RD lookup_vat · 命中加 vat_registered=true · 未命中诚实降级。"""

    async def test_hit_returns_clean_normalized_shape(self):
        from routes import workspace_routes as wr

        with (
            mock.patch.object(wr, "require_perm", return_value={"id": "u1"}),
            mock.patch(
                "services.rd.rd_api.lookup_vat",
                return_value={
                    "ok": True,
                    "data": {
                        "tax_id": "0105551234567",
                        "name": "ACME CO LTD",
                        "address": "123 Bangkok",
                        "branch_label": "สำนักงานใหญ่",
                        "raw_fields": {"BranchName": "ACME", "HouseNumber": "123"},
                    },
                    "cached": False,
                },
            ),
        ):
            out = await wr.workspace_tax_lookup("0105551234567", mock.Mock(), branch=0)
        self.assertTrue(out["ok"])
        # 归一字段直接可用(绿卡渲染)
        self.assertEqual(out["data"]["name"], "ACME CO LTD")
        self.assertEqual(out["data"]["address"], "123 Bangkok")
        self.assertEqual(out["data"]["branch_label"], "สำนักงานใหญ่")
        self.assertTrue(out["data"]["vat_registered"])
        # 不透传 raw_fields 17 字段噪音
        self.assertNotIn("raw_fields", out["data"])

    async def test_miss_returns_ok_false(self):
        from routes import workspace_routes as wr

        with (
            mock.patch.object(wr, "require_perm", return_value={"id": "u1"}),
            mock.patch(
                "services.rd.rd_api.lookup_vat", return_value={"ok": False, "error": "not_found"}
            ),
        ):
            out = await wr.workspace_tax_lookup("123", mock.Mock(), branch=0)
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "not_found")


class GetSingleScopeTests(unittest.IsolatedAsyncioTestCase):
    """公司资料页读单个:被分派成员越权 → fail-closed 404(不泄漏存在性)。"""

    async def test_assigned_member_out_of_scope_404(self):
        from routes import workspace_routes as wr

        authz = mock.Mock(scope_mode="assigned")
        authz.allows_workspace.return_value = False
        with (
            mock.patch.object(
                wr,
                "get_current_user_from_request",
                return_value={"id": "u1", "is_super_admin": False},
            ),
            mock.patch.object(wr, "get_authz", return_value=authz),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.get_workspace_client_detail(123, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()

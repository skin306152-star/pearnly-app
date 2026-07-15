# -*- coding: utf-8 -*-
"""
守门测试 · Earn 后台充值审核(credits 模式 · billing_routes)路由契约。

背景:2026-05-22 CLEANUP-PLAN-01/02 删了老 /api/admin/payments/* 审核路由 + 前端渲染,
计划迁到 /api/admin/credits/topup/*,但管理端 UI 一直没重建 → Earn 后台『看不到充值审核』。
2026-05-24 重建前端(static/admin · /admin/topup 页)接这 3 个端点。

这里把这 3 个后端端点 + 前端会调的路径锁成契约 · 防再次被清理悄悄删掉(money 路径 · 删了直接收不到钱)。
"""

import unittest


class AdminTopupRouteContractTests(unittest.TestCase):
    def test_billing_router_has_admin_topup_routes(self):
        from routes import billing_routes as br

        got = {
            (m, r.path)
            for r in br.router.routes
            for m in (getattr(r, "methods", set()) or set())
            if m in ("GET", "POST")
        }
        for needed in {
            ("GET", "/api/admin/credits/topup/requests"),
            ("POST", "/api/admin/credits/topup/approve/{request_id}"),
            ("POST", "/api/admin/credits/topup/reject/{request_id}"),
            ("GET", "/api/admin/credits/topup/slip/{request_id}"),  # ENC-b · slip 鉴权取件
        }:
            self.assertIn(needed, got, f"缺失充值审核路由 {needed} · Earn 后台会再次看不到充值审核")

    def test_app_includes_admin_topup_routes(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/credits/topup/requests", paths)
        self.assertIn("/api/admin/credits/topup/approve/{request_id}", paths)
        self.assertIn("/api/admin/credits/topup/reject/{request_id}", paths)
        self.assertIn("/api/admin/credits/topup/slip/{request_id}", paths)


if __name__ == "__main__":
    unittest.main()

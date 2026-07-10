# -*- coding: utf-8 -*-
"""admin_pos_entitlement_routes 契约(PS-3)。

锁定:6 路由 path+method 契约;app include_router 挂上;全路由复用 route_helpers._require_super_admin
单一来源;非超管一律 403(开通/吊销/转移/发放/重置密码是钱+授权+凭据敏感动作,守门丢不得)。"""

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_pos_entitlement_routes
from routes.admin_pos_entitlement_routes import router


class RoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(
            got,
            {
                ("GET", "/api/admin/pos-entitlement"),
                ("POST", "/api/admin/pos-entitlement/grant"),
                ("POST", "/api/admin/pos-entitlement/provision"),
                ("POST", "/api/admin/pos-entitlement/reset-password"),
                ("POST", "/api/admin/pos-entitlement/revoke"),
                ("POST", "/api/admin/pos-entitlement/transfer"),
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/pos-entitlement", paths)
        self.assertIn("/api/admin/pos-entitlement/grant", paths)

    def test_super_admin_guard_single_source(self):
        self.assertIs(
            admin_pos_entitlement_routes._require_super_admin,
            route_helpers._require_super_admin,
        )


class GuardEnforcedTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def _as_non_super(self):
        return mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"is_super_admin": False},
        )

    def test_get_status_non_super_403(self):
        with self._as_non_super():
            r = self.client.get("/api/admin/pos-entitlement?q=x")
        self.assertEqual(r.status_code, 403)

    def test_grant_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/pos-entitlement/grant", json={"tenant_id": "t1"})
        self.assertEqual(r.status_code, 403)

    def test_revoke_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/pos-entitlement/revoke", json={"tenant_id": "t1"})
        self.assertEqual(r.status_code, 403)

    def test_transfer_non_super_403(self):
        with self._as_non_super():
            r = self.client.post(
                "/api/admin/pos-entitlement/transfer",
                json={"from_tenant_id": "a", "to_tenant_id": "b"},
            )
        self.assertEqual(r.status_code, 403)

    def test_provision_non_super_403(self):
        with self._as_non_super():
            r = self.client.post(
                "/api/admin/pos-entitlement/provision",
                json={"email": "shop@example.com"},
            )
        self.assertEqual(r.status_code, 403)

    def test_reset_password_non_super_403(self):
        with self._as_non_super():
            r = self.client.post(
                "/api/admin/pos-entitlement/reset-password",
                json={"email": "shop@example.com"},
            )
        self.assertEqual(r.status_code, 403)


if __name__ == "__main__":
    unittest.main()

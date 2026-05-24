# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 公共 helper 从 app.py 抽到 route_helpers.py。

锁定(防搬迁回归 + 防重复拷贝复活):
  1. 5 个 helper + _WEAK_PASSWORDS 都能从 route_helpers import(防丢)
  2. app.py / billing_routes / admin_diagnostics 用的是 route_helpers 同一份对象
     (防有人再在各文件里复制一份 · 漂移)
  3. _check_password_strength 4 个拒绝分支 + 通过分支(行为契约不变)
  4. _get_client_ip XFF 取第一个 / 回退 client.host / 无 client 返 None
  5. _require_super_admin 非超管 403 · 超管放行(鉴权契约不变)
"""

import unittest
from unittest import mock

from fastapi import HTTPException

import route_helpers


class RouteHelpersImportContractTests(unittest.TestCase):
    def test_all_helpers_importable(self):
        for name in (
            "_require_super_admin",
            "_require_owner_or_super",
            "_log_op",
            "_get_client_ip",
            "_check_password_strength",
            "_WEAK_PASSWORDS",
        ):
            self.assertTrue(hasattr(route_helpers, name), f"route_helpers 缺 {name}")

    def test_single_source_of_truth(self):
        """app.py 与已抽出的 routes 必须复用 route_helpers 同一份对象 · 不许各自拷贝"""
        import admin_diagnostics_routes
        import app
        import billing_routes
        import team_routes

        self.assertIs(app._require_super_admin, route_helpers._require_super_admin)
        self.assertIs(app._require_owner_or_super, route_helpers._require_owner_or_super)
        self.assertIs(app._log_op, route_helpers._log_op)
        self.assertIs(billing_routes._require_super_admin, route_helpers._require_super_admin)
        self.assertIs(
            admin_diagnostics_routes._require_super_admin,
            route_helpers._require_super_admin,
        )
        # REFACTOR-B1(2026-05-25):team_add_employee 随 7 路由从 app.py 搬到 team_routes ·
        # _check_password_strength 的消费者随之转移 · 单一来源断言跟到 team_routes。
        self.assertIs(team_routes._require_owner_or_super, route_helpers._require_owner_or_super)
        self.assertIs(team_routes._log_op, route_helpers._log_op)
        self.assertIs(team_routes._check_password_strength, route_helpers._check_password_strength)


class PasswordStrengthContractTests(unittest.TestCase):
    def test_too_short(self):
        self.assertEqual(route_helpers._check_password_strength("ab1"), "pwd.too_short")
        self.assertEqual(route_helpers._check_password_strength(""), "pwd.too_short")

    def test_common_weak(self):
        self.assertEqual(
            route_helpers._check_password_strength("password123"), "pwd.too_weak_common"
        )

    def test_all_digits(self):
        self.assertEqual(
            route_helpers._check_password_strength("248613579"), "pwd.too_weak_numeric"
        )

    def test_letters_only(self):
        self.assertEqual(route_helpers._check_password_strength("abcdefgh"), "pwd.too_weak")

    def test_strong_passes(self):
        self.assertIsNone(route_helpers._check_password_strength("Zihao2026x"))


class _FakeClient:
    def __init__(self, host):
        self.host = host


class _FakeRequest:
    def __init__(self, headers=None, client_host=None):
        self.headers = headers or {}
        self.client = _FakeClient(client_host) if client_host else None


class ClientIpContractTests(unittest.TestCase):
    def test_xff_first_ip(self):
        req = _FakeRequest(headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})
        self.assertEqual(route_helpers._get_client_ip(req), "1.2.3.4")

    def test_fallback_client_host(self):
        req = _FakeRequest(client_host="9.9.9.9")
        self.assertEqual(route_helpers._get_client_ip(req), "9.9.9.9")

    def test_no_client_returns_none(self):
        req = _FakeRequest()
        self.assertIsNone(route_helpers._get_client_ip(req))


class RequireSuperAdminContractTests(unittest.TestCase):
    def test_non_super_403(self):
        with mock.patch.object(
            route_helpers, "get_current_user_from_request", return_value={"is_super_admin": False}
        ):
            with self.assertRaises(HTTPException) as ctx:
                route_helpers._require_super_admin(_FakeRequest())
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertEqual(ctx.exception.detail, "admin.not_super_admin")

    def test_super_passes(self):
        user = {"is_super_admin": True, "id": "u1"}
        with mock.patch.object(route_helpers, "get_current_user_from_request", return_value=user):
            self.assertIs(route_helpers._require_super_admin(_FakeRequest()), user)


if __name__ == "__main__":
    unittest.main()

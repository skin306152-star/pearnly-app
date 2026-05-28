#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_auth_integration.py · REFACTOR-WC-D2

域:auth(登录 / 当前用户 / 改密)· 高敏 · spec 01/13 兜底
本文件:2 个集成测试 · env-gated
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import (  # noqa: E402
    assert_json_response,
    get_test_client,
    login_for_token,
    require_db,
    require_test_user,
)


class AuthLoginAndMeIntegrationTest(unittest.TestCase):
    """POST /api/auth/login → GET /api/me · 端到端拿 token + 查身份"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.creds = creds
        self.client = get_test_client()

    def test_login_returns_token_and_me_returns_user(self) -> None:
        token = login_for_token(
            self.client, self.creds["PEARNLY_E2E_USER"], self.creds["PEARNLY_E2E_PASS"]
        )
        self.assertTrue(token)
        # 真去查 /api/me 用 token
        resp = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        data = assert_json_response(self, resp)
        # 必须有用户标识(契约 · 铁律 #15)
        self.assertTrue(
            "username" in data or "user" in data or "email" in data or "id" in data,
            msg=f"/api/me 没返用户标识字段 · body={data}",
        )


class AuthLoginInvalidPasswordRejectedIntegrationTest(unittest.TestCase):
    """POST /api/auth/login 错密码 · 必须 401 不是 500(防爆栈泄露)"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.user = creds["PEARNLY_E2E_USER"]
        self.client = get_test_client()

    def test_wrong_password_returns_401_not_500(self) -> None:
        resp = self.client.post(
            "/api/auth/login",
            json={"username": self.user, "password": "definitely-wrong-password-xyz-123"},
        )
        # 验证类失败应是 4xx 不是 5xx
        self.assertEqual(
            resp.status_code,
            401,
            msg=f"错密码应 401 · 实际 {resp.status_code} body={resp.text[:200]}",
        )
        # 错误消息不应泄露内部细节(防爆栈)
        body = resp.text.lower()
        self.assertNotIn("traceback", body, msg="错密码响应里有 traceback · 泄露内部!")
        self.assertNotIn("psycopg2", body, msg="错密码响应里有 psycopg2 · 泄露 DB!")


if __name__ == "__main__":
    unittest.main(verbosity=2)

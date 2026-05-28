#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_signup_integration.py · REFACTOR-WC-D3

域:注册(signup)· 高敏 · PLG 反薅闸前置契约(铁律 #4 · spec 02 兜底)
本文件:4 个集成测试 · env-gated

只验「输入校验 4xx 契约」· 全部在 DB 写入前就失败:
  - 不创建任何账号(校验未过 · 走不到 INSERT)
  - 不发任何邮件(校验未过 · 走不到 send)
  - 不碰真付费用户余额
锁定的契约:signup 必须挡住 ① 非法邮箱 ② 弱密码 ③ 缺邮箱验证码(反薅核心)
—— 若将来重构 auth_signup.py 打破任一条,薅羊毛闸就会被悄悄拆掉,本测试拦住。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import (  # noqa: E402
    assert_json_response,
    get_test_client,
    require_db,
)


class SignupValidationContractIntegrationTest(unittest.TestCase):
    """POST /api/auth/signup 输入校验契约 · 反薅闸前置 · 纯 4xx · 不建账号不发邮件"""

    def setUp(self) -> None:
        require_db()
        self.client = get_test_client()

    def _post_signup(self, payload: dict):  # type: ignore[no-untyped-def]
        """POST /api/auth/signup · 若 signup 全局禁用(503)则 skip。"""
        resp = self.client.post("/api/auth/signup", json=payload)
        if resp.status_code == 503:
            self.skipTest("signup 全局禁用(503)· 跳过校验契约测试")
        return resp

    def test_invalid_email_rejected_400(self) -> None:
        """非法邮箱(无 @)· 必须 400 email_invalid · 不是 500"""
        resp = self._post_signup(
            {"email": "notanemail", "password": "validpass123", "verification_code": "1234"}
        )
        data = assert_json_response(self, resp, expect_status=400)
        self.assertEqual(
            data.get("detail"),
            "email_invalid",
            msg=f"非法邮箱应返 email_invalid · 实际 {data}",
        )

    def test_short_password_rejected_400(self) -> None:
        """密码 < 6 位 · 必须 400 password_too_short(校验早于建账号)"""
        resp = self._post_signup(
            {"email": "someone@gmail.com", "password": "123", "verification_code": "1234"}
        )
        data = assert_json_response(self, resp, expect_status=400)
        self.assertEqual(
            data.get("detail"),
            "password_too_short",
            msg=f"弱密码应返 password_too_short · 实际 {data}",
        )

    def test_missing_verification_code_rejected_400(self) -> None:
        """合法邮箱 + 合法密码但缺邮箱验证码 · 必须卡在 verification_code_required(反薅核心)"""
        email = f"signup-contract-{uuid4().hex[:12]}@gmail.com"
        resp = self._post_signup({"email": email, "password": "validpass123"})
        data = assert_json_response(self, resp, expect_status=400)
        self.assertEqual(
            data.get("detail"),
            "verification_code_required",
            msg=f"缺验证码应返 verification_code_required(防绕过邮箱验证薅号)· 实际 {data}",
        )

    def test_validation_error_no_internal_leak(self) -> None:
        """校验失败响应不得泄露 traceback / DB 驱动名(防爆栈泄露 · 同 auth 契约)"""
        resp = self._post_signup(
            {"email": "notanemail", "password": "x", "verification_code": "1234"}
        )
        body = resp.text.lower()
        self.assertNotIn("traceback", body, msg="signup 校验响应里有 traceback · 泄露内部!")
        self.assertNotIn("psycopg2", body, msg="signup 校验响应里有 psycopg2 · 泄露 DB!")


if __name__ == "__main__":
    unittest.main(verbosity=2)

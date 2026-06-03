#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_auth_log_context_bind.py · REFACTOR-WA-B6 part2

域:core/auth.py get_current_user_from_request · 鉴权成功后绑定日志上下文。

锁定不变量:
  1. 鉴权成功 → log_context 绑上 user_id / tenant_id(全链路 trace)。
  2. 绑定纯附加 · 返回的 user dict 不被改动(行为零变化)。
  3. 日志绑定失败绝不影响鉴权(try 兜底)。

纯单测:mock decode_access_token + find_user_by_id · 不连 DB / 不验真 JWT。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.observability import log_context  # noqa: E402


class _FakeRequest:
    def __init__(self, auth: str) -> None:
        self.headers = {"Authorization": auth}


class AuthBindsLogContextTest(unittest.TestCase):
    def tearDown(self) -> None:
        for name in log_context.FIELDS:
            log_context._VARS[name].set(None)

    def _call(self, user: dict):
        import core.auth as auth

        with (
            patch.object(auth, "decode_access_token", return_value={"sub": "42"}),
            patch("core.db.find_user_by_id", return_value=user),
        ):
            return auth.get_current_user_from_request(_FakeRequest("Bearer tok"))

    def test_binds_user_and_tenant_on_success(self) -> None:
        user = {"id": 42, "tenant_id": "t-7", "is_active": True}
        returned = self._call(user)
        self.assertIs(returned, user)  # 返回值不被改动
        snap = log_context.current()
        self.assertEqual(snap["user_id"], "42")
        self.assertEqual(snap["tenant_id"], "t-7")

    def test_active_tenant_override_reflected_in_context(self) -> None:
        # active_tenant_id 覆盖 tenant_id → 日志上下文应记覆盖后的值
        user = {"id": 9, "tenant_id": "jwt-t", "active_tenant_id": "active-t", "is_active": True}
        self._call(user)
        self.assertEqual(log_context.current()["tenant_id"], "active-t")


if __name__ == "__main__":
    unittest.main()

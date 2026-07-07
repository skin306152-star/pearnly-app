# -*- coding: utf-8 -*-
"""登录失败记录必须落库(commit=True)· 安全评估 2026-07-07。

背景:_record_login_failure 曾用 db.get_cursor()(默认 commit=False),失败记录永不持久
→ 30min 窗口计数恒为 0 → "同号 5 次/30min 锁"形同虚设(prod 实测该表 0 行)。
本测试锁死不变量:写失败日志必须 commit=True,防回归。
"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch


class LoginFailureCommitTest(unittest.TestCase):
    def test_record_login_failure_commits(self) -> None:
        from routes import login_routes

        captured: dict = {}

        @contextmanager
        def fake_get_cursor(commit: bool = False):
            captured["commit"] = commit
            yield MagicMock()

        req = MagicMock()
        req.client.host = "1.2.3.4"
        req.headers.get.return_value = "agent"
        with patch.object(login_routes.db, "get_cursor", side_effect=fake_get_cursor):
            login_routes._record_login_failure("User@Example.com", req)

        self.assertTrue(
            captured.get("commit"),
            "失败记录必须 commit=True 才能落库(账号锁依赖它)· 见安全评估 2026-07-07",
        )


if __name__ == "__main__":
    unittest.main()

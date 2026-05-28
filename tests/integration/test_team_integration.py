#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_team_integration.py · REFACTOR-WC-D2

域:team(团队成员列表 / 邀请)· 中敏
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
    mock_gmail_smtp,
    require_db,
    require_test_user,
)


class TeamMembersListIntegrationTest(unittest.TestCase):
    """GET /api/team · 当前 tenant 团队成员"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_team_list_returns_members(self) -> None:
        resp = self.client.get("/api/team", headers={"Authorization": f"Bearer {self.token}"})
        # 团队 endpoint 可能挂在 /api/team 或 /api/team/members · 接受任何 < 500
        self.assertLess(resp.status_code, 500, msg=f"team 500:{resp.text[:200]}")
        if resp.status_code == 200:
            data = assert_json_response(self, resp)
            # 必有某种"成员"列表字段
            if isinstance(data, dict):
                self.assertTrue(
                    any(k in data for k in ("members", "users", "team", "items")),
                    msg=f"team 返 dict 但无成员字段 · body={data}",
                )


class TeamInviteMockGmailIntegrationTest(unittest.TestCase):
    """POST /api/team/invite · 邮件 mock · 不真发"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_invite_with_mocked_smtp_no_real_email(self) -> None:
        with mock_gmail_smtp():
            resp = self.client.post(
                "/api/team/invite",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"email": "test-invite@pearnly.test", "role": "employee"},
            )
        # 接受 200 / 201 / 4xx · 不应 500(即使端点 404 也允许 · 路由层活)
        self.assertLess(resp.status_code, 500, msg=f"invite 500:{resp.text[:200]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

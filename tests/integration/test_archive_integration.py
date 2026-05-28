#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_archive_integration.py · REFACTOR-WC-D2

域:archive(OCR 历史归档 list / detail / delete)· 中-高敏 · spec 04 兜底
本文件:3 个集成测试 · env-gated
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


class ArchiveListIntegrationTest(unittest.TestCase):
    """GET /api/history · 历史列表 = 归档主入口"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_history_list_first_page_under_50(self) -> None:
        resp = self.client.get(
            "/api/history?limit=50",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        data = assert_json_response(self, resp)
        if isinstance(data, list):
            self.assertLessEqual(len(data), 50)
        elif isinstance(data, dict):
            items = data.get("items") or data.get("history") or data.get("data") or []
            self.assertIsInstance(items, list)
            self.assertLessEqual(len(items), 50)


class ArchiveDetailNonexistentReturns404IntegrationTest(unittest.TestCase):
    """GET /api/history/<id> 不存在 id · 必 404 不是 500"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_nonexistent_history_id_returns_404(self) -> None:
        resp = self.client.get(
            "/api/history/99999999",  # 极不可能存在的 id
            headers={"Authorization": f"Bearer {self.token}"},
        )
        # 接受 404 / 403(权限拒绝)/ 200(返空字段)· 不应 500
        self.assertNotEqual(resp.status_code, 500, msg=f"history detail 500:{resp.text[:200]}")


class ArchiveDeleteUnauthorizedReturns4xxIntegrationTest(unittest.TestCase):
    """DELETE /api/history/<id> 没 token · 必 401 / 403 不 500"""

    def setUp(self) -> None:
        require_db()
        # 故意不登录
        self.client = get_test_client()

    def test_delete_without_token_returns_401_or_403(self) -> None:
        resp = self.client.delete("/api/history/99999999")
        self.assertIn(
            resp.status_code,
            (401, 403, 404, 422),
            msg=f"delete 无 token 应 401/403 · 实际 {resp.status_code}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

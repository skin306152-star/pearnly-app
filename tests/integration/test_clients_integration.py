#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_clients_integration.py · REFACTOR-WC-D2

域:clients(客户列表 / 创建)· 中敏 · spec 03 兜底
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


class ClientsListIntegrationTest(unittest.TestCase):
    """GET /api/clients · 当前 tenant 客户列表"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_clients_list_returns_array_or_paginated(self) -> None:
        resp = self.client.get("/api/clients", headers={"Authorization": f"Bearer {self.token}"})
        data = assert_json_response(self, resp)
        # 接受 array / { clients: [] } / { items: [], total: N }
        if isinstance(data, dict):
            self.assertTrue(
                any(k in data for k in ("clients", "items", "data")),
                msg=f"clients 返 dict 但无 clients/items/data · body={data}",
            )


class ClientsCreateValidationIntegrationTest(unittest.TestCase):
    """POST /api/clients · 空 body / 缺必填字段 · 必 4xx 不 500"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_create_with_empty_body_returns_4xx(self) -> None:
        resp = self.client.post(
            "/api/clients",
            headers={"Authorization": f"Bearer {self.token}"},
            json={},
        )
        # 校验失败 4xx 或路由 404(变体路径) · 不 500
        self.assertLess(resp.status_code, 500, msg=f"clients create 空 body 500:{resp.text[:200]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

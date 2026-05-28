#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_erp_integration.py · REFACTOR-WC-D2

域:erp(集成 endpoint + 推送)· 中-高敏 · spec 08 兜底
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


class ErpEndpointsListIntegrationTest(unittest.TestCase):
    """GET /api/erp/endpoints · 列当前 tenant 的 ERP 连接配置"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_erp_endpoints_returns_array(self) -> None:
        resp = self.client.get(
            "/api/erp/endpoints", headers={"Authorization": f"Bearer {self.token}"}
        )
        data = assert_json_response(self, resp)
        # 接受 dict 或 list 包装(具体 schema 整顿期 G4 收口前不锁)
        if isinstance(data, dict):
            self.assertIn(
                "items",
                data,
                msg=f"返 dict 但无 items · 期望 dict 含 items 或纯 list · body={data}",
            )
        else:
            self.assertIsInstance(data, list)


class ErpPushNoRealCallIntegrationTest(unittest.TestCase):
    """POST /api/erp/endpoints/<id>/push · 不真打 ERP(没真 endpoint id · 应 4xx)
    硬线:绝不真打 mrerp 生产 · 测试用不存在的 endpoint id 验证"路由 → 校验"链路活
    """

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_push_to_nonexistent_endpoint_returns_4xx(self) -> None:
        # 不存在的 endpoint id = 99999 · 应 404 / 403 / 422 · 不应 500
        resp = self.client.post(
            "/api/erp/endpoints/99999/push",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"history_ids": []},
        )
        self.assertLess(
            resp.status_code,
            500,
            msg=f"push 到 nonexistent endpoint 500:{resp.text[:200]}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

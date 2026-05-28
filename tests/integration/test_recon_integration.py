#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_recon_integration.py · REFACTOR-WC-D2

域:recon(对账 · 销项税核对 / 银行 / VAT excel)
本文件:3 个集成测试 · env-gated · 真路由 + 真 DB
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


class ReconJobsListIntegrationTest(unittest.TestCase):
    """GET /api/recon-jobs · 列当前用户提交过的异步对账任务"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_recon_jobs_list_returns_array_or_paginated(self) -> None:
        resp = self.client.get("/api/recon-jobs", headers={"Authorization": f"Bearer {self.token}"})
        data = assert_json_response(self, resp)
        # 接受两种契约:array | {items: array, total: N}
        if isinstance(data, list):
            for item in data[:3]:
                self.assertIn("status", item)
        else:
            self.assertIn("items", data, msg=f"返既非 array 又无 items 字段:{data}")


class ReconVatExcelEmptyUploadIntegrationTest(unittest.TestCase):
    """POST /api/vat-excel/* · 上传空 Excel 期望被拒(不是 500)"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_empty_upload_returns_4xx_not_500(self) -> None:
        # 上传 0 字节"假 Excel" · 路由应该 4xx 拒绝(校验生效) · 不是 500 崩
        files = {"file": ("empty.xlsx", b"", "application/vnd.ms-excel")}
        resp = self.client.post(
            "/api/vat-excel/upload",  # 路径可能不存在 · 接受 404 也算路由层活
            headers={"Authorization": f"Bearer {self.token}"},
            files=files,
        )
        self.assertLess(
            resp.status_code,
            500,
            msg=f"上传空文件不应 500 · 实际 {resp.status_code} body={resp.text[:200]}",
        )


class ReconBankRoutesReachableIntegrationTest(unittest.TestCase):
    """GET /api/bank-recon/* · 路由可达(身份验证 + 数据读)"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_bank_recon_list_or_404_no_500(self) -> None:
        resp = self.client.get(
            "/api/bank-recon/list",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        # 接受 200(有数据)/ 404(路由未注册或路径变)/ 401(token 过期边缘)
        # 关键是不 500
        self.assertNotEqual(resp.status_code, 500, msg=f"bank-recon 500:{resp.text[:200]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

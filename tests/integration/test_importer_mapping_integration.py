#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_importer_mapping_integration.py · REFACTOR-WC-D3

域:通用导入器模板学习层(ADR-006 · S4 · /api/recon/import/*)· 中敏 · 收入对账上游
本文件:4 个集成测试 · env-gated · 此前 0 集成覆盖

只验「鉴权闸 + 列映射校验契约」· 全部在 template_store 写库前就失败:
  - POST /api/recon/import/save-mapping  未登录 → 401(发合法 body 绕过 Pydantic · 撞 handler 鉴权)
  - GET  /api/recon/import/mappings      未登录 → 401
  - POST save-mapping 已登录但坏 document_type → 422(必须 statement / gl)
  - POST save-mapping 已登录但映射缺『date』列 → 422(对账下游强依赖日期列)
锁定的契约:模板学习必须先卡登录、再卡 document_type 白名单 + date 列 ——
重构 services/importer 若放松这些前置校验,坏映射会污染 tenant 模板库,本测试拦住。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import (  # noqa: E402
    auth_header,
    get_test_client,
    login_for_token,
    require_db,
    require_test_user,
)

# 合法 Pydantic body(必填 document_type / template_signature / mapping 齐全)·
# 用于"未登录"测试:body 合法 → 过 Pydantic → 进 handler → 撞 401(而非 422)。
_VALID_BODY = {
    "document_type": "statement",
    "template_signature": "sig-contract-test",
    "mapping": {"date": 0},
}


class ImporterMappingAuthGateIntegrationTest(unittest.TestCase):
    """鉴权闸契约 · 未登录就能验(不需要真账号)"""

    def setUp(self) -> None:
        require_db()
        self.client = get_test_client()

    def test_save_mapping_unauthenticated_401(self) -> None:
        """未登录 POST save-mapping(body 合法)· 必须 401 · 不是 422/500"""
        resp = self.client.post("/api/recon/import/save-mapping", json=_VALID_BODY)
        self.assertEqual(
            resp.status_code,
            401,
            msg=f"未登录 save-mapping 应 401 · 实际 {resp.status_code} body={resp.text[:200]}",
        )

    def test_list_mappings_unauthenticated_401(self) -> None:
        """未登录 GET mappings · 必须 401"""
        resp = self.client.get("/api/recon/import/mappings")
        self.assertEqual(
            resp.status_code,
            401,
            msg=f"未登录 mappings 应 401 · 实际 {resp.status_code} body={resp.text[:200]}",
        )


class ImporterMappingValidationIntegrationTest(unittest.TestCase):
    """已登录列映射校验契约 · 坏映射在写库前 422"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_bad_document_type_rejected_422(self) -> None:
        """document_type 不在 (statement, gl) · 必须 422(早于写库)"""
        body = dict(_VALID_BODY, document_type="bogus_type")
        resp = self.client.post(
            "/api/recon/import/save-mapping", json=body, headers=auth_header(self.token)
        )
        self.assertEqual(
            resp.status_code,
            422,
            msg=f"坏 document_type 应 422 · 实际 {resp.status_code} body={resp.text[:200]}",
        )

    def test_mapping_without_date_column_rejected_422(self) -> None:
        """列映射缺『date』· 必须 422(对账下游强依赖日期列 · 早于写库)"""
        body = dict(_VALID_BODY, mapping={"amount": 1})
        resp = self.client.post(
            "/api/recon/import/save-mapping", json=body, headers=auth_header(self.token)
        )
        self.assertEqual(
            resp.status_code,
            422,
            msg=f"缺 date 列映射应 422 · 实际 {resp.status_code} body={resp.text[:200]}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

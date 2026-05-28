#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_bank_recon_integration.py · REFACTOR-WC-D3

域:收入对账(银行对账单上传 / 会话)· 核心路径 · spec 07 兜底
本文件:3 个集成测试 · env-gated

只验「上传前置校验 + 会话查询契约」· 用极小/坏文件 → 在解析(pdfplumber/Gemini)之前
就被 400 挡掉 · 不触发 OCR(不烧 Gemini · 不写库):
  - POST /api/bank-recon/upload  坏格式(.txt)→ 400 bank_recon.unsupported_format
  - POST /api/bank-recon/upload  空/过小文件(.pdf <50B)→ 400 bank_recon.empty_file
  - GET  /api/bank-recon/sessions/{bogus}  已登录 → 404 bank_recon.session_not_found
锁定的契约:对账上传必须先卡"扩展名白名单 + 非空" —— 重构 bank_recon_routes
若把这两道前置校验挪到解析之后,坏/空文件会直接进 OCR 管道烧钱,本测试拦住。
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import (  # noqa: E402
    auth_header,
    get_test_client,
    login_for_token,
    require_db,
    require_test_user,
)


class BankReconUploadValidationIntegrationTest(unittest.TestCase):
    """上传前置校验契约 · 坏/空文件在解析前被 400 挡掉(不进 OCR)"""

    def setUp(self) -> None:
        require_db()
        self.client = get_test_client()

    def test_unsupported_format_rejected_400(self) -> None:
        """非白名单扩展名(.txt)· 必须 400 unsupported_format(早于 file.read / 解析)"""
        resp = self.client.post(
            "/api/bank-recon/upload",
            files={"file": ("bad.txt", io.BytesIO(b"not a statement"), "text/plain")},
        )
        self.assertEqual(
            resp.status_code,
            400,
            msg=f"坏格式应 400 · 实际 {resp.status_code} body={resp.text[:200]}",
        )
        self.assertIn(
            "unsupported_format",
            resp.text,
            msg=f"坏格式应返 bank_recon.unsupported_format · body={resp.text[:200]}",
        )

    def test_empty_file_rejected_400(self) -> None:
        """白名单扩展名但内容过小(<50B)· 必须 400 empty_file(早于解析 · 不烧 Gemini)"""
        resp = self.client.post(
            "/api/bank-recon/upload",
            files={"file": ("tiny.pdf", io.BytesIO(b"x"), "application/pdf")},
        )
        self.assertEqual(
            resp.status_code,
            400,
            msg=f"空/过小文件应 400 · 实际 {resp.status_code} body={resp.text[:200]}",
        )
        self.assertIn(
            "empty_file",
            resp.text,
            msg=f"过小文件应返 bank_recon.empty_file · body={resp.text[:200]}",
        )


class BankReconSessionLookupIntegrationTest(unittest.TestCase):
    """会话查询契约 · 不存在的 session 必须 404(不是 500)"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_unknown_session_returns_404(self) -> None:
        """查不存在的 session_id · 必须 404 session_not_found · 不爆栈"""
        bogus = f"nonexistent-{uuid4().hex}"
        resp = self.client.get(
            f"/api/bank-recon/sessions/{bogus}",
            headers=auth_header(self.token),
        )
        self.assertEqual(
            resp.status_code,
            404,
            msg=f"未知 session 应 404 · 实际 {resp.status_code} body={resp.text[:200]}",
        )
        self.assertNotIn("traceback", resp.text.lower(), msg="404 响应里有 traceback · 泄露内部!")


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_ocr_recognize_contract_integration.py · REFACTOR-WC-D3

域:OCR 识别热路径输入守门(POST /api/ocr/recognize)· 高敏热路径 · spec 16 兜底
本文件:2 个集成测试 · env-gated

只验「Gemini/扣费之前的输入守门契约」· 不真识别(不烧 Gemini · 不扣 credits):
  - POST /api/ocr/recognize  缺 file 字段 → 422(FastAPI 级 File(...) 必填 · 无需登录)
  - POST /api/ocr/recognize  已登录但坏格式(.txt)→ 400 ocr.unsupported_format
锁定的契约:OCR 热路径必须在 file.read / OCR pipeline / 扣费之前就把坏格式 400 挡掉 ——
窗口 A 正在拆 app.py 的 recognize 路由,本测试是"重构别让坏/非法输入溜进计费 OCR 管道"的安全网。
"""

from __future__ import annotations

import io
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


class OcrRecognizeRequiredFileIntegrationTest(unittest.TestCase):
    """缺 file 字段契约 · FastAPI 级校验(无需登录)"""

    def setUp(self) -> None:
        require_db()
        self.client = get_test_client()

    def test_missing_file_returns_422(self) -> None:
        """不带 file 字段 POST · FastAPI File(...) 必填 → 422(早于 handler)"""
        resp = self.client.post("/api/ocr/recognize")
        self.assertEqual(
            resp.status_code,
            422,
            msg=f"缺 file 应 422 · 实际 {resp.status_code} body={resp.text[:200]}",
        )


class OcrRecognizeFormatGuardIntegrationTest(unittest.TestCase):
    """已登录格式守门契约 · 坏格式在 OCR/扣费前 400"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_unsupported_format_rejected_400(self) -> None:
        """坏扩展名(.txt)· 必须 400 ocr.unsupported_format(早于 file.read/Gemini/扣费)"""
        resp = self.client.post(
            "/api/ocr/recognize",
            headers=auth_header(self.token),
            files={"file": ("malware.txt", io.BytesIO(b"not an invoice"), "text/plain")},
        )
        self.assertEqual(
            resp.status_code,
            400,
            msg=f"坏格式应 400 · 实际 {resp.status_code} body={resp.text[:200]}",
        )
        self.assertIn(
            "unsupported_format",
            resp.text,
            msg=f"坏格式应返 ocr.unsupported_format · body={resp.text[:200]}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

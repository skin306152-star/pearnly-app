#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_vat_excel_integration.py · REFACTOR-WC-D3

域:销项税核对(VAT Excel 公式对账)· 核心路径 · spec 06 兜底
本文件:3 个集成测试 · env-gated

只验「访问闸 + 上传校验契约」· 不传真发票/报告 → 不触发并行 OCR(不烧 Gemini):
  - GET  /api/vat_excel/check  匿名 → 401 auth.missing_token(不泄栈)
  - POST /api/vat_excel/build  未登录 → 401(auth 先于一切)
  - POST /api/vat_excel/build  已登录但空上传 → 400(必须 1 发票 + 1 报告)
锁定的契约:对账入口必须先卡登录、再卡"至少一发票一报告" —— 重构 vat_excel_routes
若调换/丢失这两道前置校验,空请求会直接进 OCR 管道烧钱,本测试拦住。
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


class VatExcelAccessGateIntegrationTest(unittest.TestCase):
    """访问闸契约 · 无需登录就能验(匿名 + 未授权路径)"""

    def setUp(self) -> None:
        require_db()
        self.client = get_test_client()

    def test_check_anonymous_returns_401(self) -> None:
        """GET /check 匿名 · 401 auth.missing_token(不是 500 · 不泄栈)

        原断言是「优雅 200 + allowed:False」,对着的是 routes/vat_excel_routes.py:77-78
        那两行 `if not user: return {allowed: False}`。但 get_current_user_from_request
        (core/auth.py:268)无 token 时是 raise 401,从不返 None —— 那两行是死代码,
        这条契约产品从来没提供过,而全仓也没有任何前端在匿名探测 /check。
        改成锁真正成立的那条:匿名到不了这个口,且错误体不泄内部细节。
        """
        resp = self.client.get("/api/vat_excel/check")
        self.assertEqual(
            resp.status_code,
            401,
            msg=f"匿名 /check 应 401 · 实际 {resp.status_code} body={resp.text[:200]}",
        )
        body = resp.text.lower()
        self.assertNotIn("traceback", body, msg="匿名响应里有 traceback · 泄露内部!")

    def test_build_unauthenticated_returns_401(self) -> None:
        """POST /build 未登录 · 必须 401(auth 早于文件处理 · 防匿名烧 OCR)"""
        resp = self.client.post("/api/vat_excel/build", data={"lang": "th"})
        # auth 校验在 handler 第一行 · 未登录直接 401 · 不进文件/OCR
        self.assertEqual(
            resp.status_code,
            401,
            msg=f"未登录 build 应 401 · 实际 {resp.status_code} body={resp.text[:200]}",
        )
        body = resp.text.lower()
        self.assertNotIn("traceback", body, msg="未登录响应里有 traceback · 泄露内部!")


class VatExcelBuildValidationIntegrationTest(unittest.TestCase):
    """已登录上传校验契约 · 空上传必须 400(不进 OCR)"""

    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )

    def test_empty_upload_rejected_400(self) -> None:
        """已登录但 0 发票 0 报告 · 必须 400 · 不触发并行 OCR(不烧 Gemini)"""
        resp = self.client.post(
            "/api/vat_excel/build",
            data={"lang": "th"},
            headers=auth_header(self.token),
        )
        # 必须 4xx(空上传)· 不是 200(假装成功)· 不是 5xx(爆栈)
        self.assertEqual(
            resp.status_code,
            400,
            msg=f"空上传应 400(至少 1 发票 + 1 报告)· 实际 {resp.status_code} body={resp.text[:200]}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_version_endpoint_contract.py · REFACTOR-WC

域:/api/version 部署金丝雀契约
本文件:1 个集成测试 · 只需 app import(不需 DB · 不需登录 · 不烧外部服务)

为啥要这个测试:
  /api/version 是**每次部署后的验证金丝雀**(`curl https://pearnly.com/api/version`
  看 version 翻新 = 部署成功 · 见 CLAUDE.md 部署铁律)。它若被结构性重构搬丢字段 /
  改坏返回,整条"部署是否生效"的验证链就瞎了。

  本测试锁定契约:GET /api/version → 200,且含 version(str)+ ts(部署时间戳)。
  更新通知横幅 version-banner 已下线,接口不再返回 release_notes。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import get_test_client  # noqa: E402


class VersionEndpointContractIntegrationTest(unittest.TestCase):
    """部署金丝雀契约守门。"""

    def setUp(self) -> None:
        self.client = get_test_client()

    def test_version_returns_deploy_fields(self) -> None:
        resp = self.client.get("/api/version")
        self.assertEqual(
            resp.status_code,
            200,
            msg=f"/api/version 应 200(部署金丝雀)· 实际 {resp.status_code} body={resp.text[:200]}",
        )
        data = resp.json()

        # 部署验证字段 · version(str)标识版本 · ts(部署时间戳)翻新判部署生效
        for field in ("version", "ts"):
            self.assertIn(
                field,
                data,
                msg=f"/api/version 必须含 {field}(部署验证依赖)· keys={sorted(data.keys())}",
            )
        self.assertNotIn(
            "release_notes",
            data,
            msg="version-banner 已下线 · /api/version 不应再返回 release_notes",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

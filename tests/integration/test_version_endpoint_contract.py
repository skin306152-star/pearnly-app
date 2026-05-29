#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_version_endpoint_contract.py · REFACTOR-WC

域:/api/version 部署金丝雀 + release_notes 4 语完整性契约
本文件:1 个集成测试 · 只需 app import(不需 DB · 不需登录 · 不烧外部服务)

为啥要这个测试:
  /api/version 是**每次部署后的验证金丝雀**(`curl https://pearnly.com/api/version`
  看 cache_bust 翻新 = 部署成功 · 见 CLAUDE.md 部署铁律)。它若被结构性重构
  搬丢字段 / 改坏返回,整条"部署是否生效"的验证链就瞎了。同时铁律 #6 要求
  release_notes 必须 4 语齐全(zh/th/en/ja · 缺一不部署)。

  本测试锁定两条契约:
    1. GET /api/version → 200,且含 version + cache_bust(部署验证字段)
    2. release_notes 是 dict 且 zh/th/en/ja 4 语 key 齐全(铁律 #6)
  任一被搬坏 → 本测试红。

设计:
  - 只查返回名册 · 不查 release_notes 文案内容(那随每次部署变 · 测内容会脆)。
  - 无需 DB / 凭据 / 外部服务 · app import 失败则 SkipTest(沿用 _helpers 范式)。
  - 0 业务代码改动(铁律 #17/#21/#23/#27 · 窗口 C 硬约束)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import get_test_client  # noqa: E402

REQUIRED_LANGS = {"zh", "th", "en", "ja"}


class VersionEndpointContractIntegrationTest(unittest.TestCase):
    """部署金丝雀 + release_notes 4 语契约守门。"""

    def setUp(self) -> None:
        self.client = get_test_client()

    def test_version_returns_deploy_fields_and_4lang_release_notes(self) -> None:
        resp = self.client.get("/api/version")
        self.assertEqual(
            resp.status_code,
            200,
            msg=f"/api/version 应 200(部署金丝雀)· 实际 {resp.status_code} body={resp.text[:200]}",
        )
        data = resp.json()

        # 1. 部署验证字段 · curl 看 cache_bust 翻新判断部署生效
        for field in ("version", "cache_bust"):
            self.assertIn(
                field,
                data,
                msg=f"/api/version 必须含 {field}(部署验证依赖)· keys={sorted(data.keys())}",
            )

        # 2. release_notes 4 语完整(铁律 #6 · 缺一不部署)
        release_notes = data.get("release_notes")
        self.assertIsInstance(
            release_notes,
            dict,
            msg=f"release_notes 应是 4 语 dict · 实际 {type(release_notes).__name__}",
        )
        missing = REQUIRED_LANGS - set(release_notes.keys())
        self.assertEqual(
            missing,
            set(),
            msg=f"release_notes 缺语言(铁律 #6 4 语必齐)· 缺 {missing} · 现有 {sorted(release_notes.keys())}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

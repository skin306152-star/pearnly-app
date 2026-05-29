#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_health_endpoint_contract.py · REFACTOR-WC

域:/api/health 健康检查端点契约
本文件:1 个集成测试 · 只需 app import(不需 DB · 不需登录 · 不烧外部服务)

为啥要这个测试:
  /api/health 是运维 / 负载均衡 / 监控探活用的健康检查端点(免鉴权 · 返 200)。
  它若被结构性重构搬丢 / 改成需要鉴权 / 返回结构变坏,探活链路就会误判服务挂掉。
  本测试锁定:GET /api/health 免鉴权 → 200,且含 status + engines + version。

  注:这是对"现状 /api/health"的契约守门;主计划 B4 的 /ready(DB/Gemini/SMTP/LINE
  各 check + 任一挂返非 200)尚未落地(/api/ready 当前 404),待 B4 实现后另补。

设计:
  - 字段(status / engines / version)均 2026-05-29 对真实 /api/health 返回逐项校验通过
    (KEYS=engines,status,version · status:str='ok' · engines:dict · version:str · 非手写猜测)。
  - 断言 status='ok' + engines 是 dict(子系统探测表)· 不深挖 engines 内具体取值
    (随运行时探测变 · 测取值会脆)。
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


class HealthEndpointContractIntegrationTest(unittest.TestCase):
    """健康检查端点契约守门 · 免鉴权 200 + 字段在。"""

    def setUp(self) -> None:
        self.client = get_test_client()

    def test_health_is_public_200_with_fields(self) -> None:
        # 免鉴权(不带 Authorization)· 探活必须直接 200
        resp = self.client.get("/api/health")
        self.assertEqual(
            resp.status_code,
            200,
            msg=f"/api/health 免鉴权应 200(探活)· 实际 {resp.status_code} body={resp.text[:200]}",
        )
        data = resp.json()
        for field in ("status", "engines", "version"):
            self.assertIn(
                field,
                data,
                msg=f"/api/health 必须含 {field}(探活字段)· keys={sorted(data.keys())}",
            )
        self.assertEqual(
            data.get("status"),
            "ok",
            msg=f"/api/health status 应为 'ok' · 实际 {data.get('status')!r}",
        )
        self.assertIsInstance(
            data.get("engines"),
            dict,
            msg=f"/api/health engines 应是子系统探测 dict · 实际 {type(data.get('engines')).__name__}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

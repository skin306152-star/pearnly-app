#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_ready_endpoint_contract.py · REFACTOR-WA-B4

域:/api/ready 真探活端点契约(补审计漏洞 #3 · 铁律 #23.7)

为啥要这个测试:
  /api/ready 区别于 /api/health(永远 ok)· 是真探活:DB 真跑 SELECT 1 +
  Gemini/SMTP/LINE 配置探针 · 任一挂 → 503。它若被结构性重构搬丢 / 改成
  永远 200,探活语义就退化成"等于没有"(就是 B4 要根治的硬伤)。

本测试锁定(免鉴权):
  - /api/ready 存在(非 404 · 区别于 B4 前的 stub 状态)。
  - 返 200 或 503(两者都是有效探活响应 · 不强求 CI 有真 DB/凭据)。
  - body 含 "ready"(bool) + "checks"(dict · 含 db/gemini/smtp/line 4 探针)。
  - 探针挂时端点必须能真返 503(不是 500 崩 · 也不是假 200)。

设计:
  - 无需 DB / 凭据 · app import 失败则 SkipTest(沿用 _helpers 范式)。
  - CI 无 DATABASE_URL → probe_db 失败 → 端点应 503 · 仍属"合约通过"。
  - 0 业务逻辑改动外的断言;不深挖具体探针取值(随环境变 · 测取值会脆)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import get_test_client  # noqa: E402


class ReadyEndpointContractIntegrationTest(unittest.TestCase):
    """/api/ready 探活契约守门 · 免鉴权 · 200/503 · 含 ready + checks。"""

    def setUp(self) -> None:
        self.client = get_test_client()

    def test_ready_exists_and_returns_probe_shape(self) -> None:
        resp = self.client.get("/api/ready")
        # 关键:不能是 404(B4 前是 404)· 也不能是 500(探针崩 = 退化)
        self.assertIn(
            resp.status_code,
            (200, 503),
            msg=f"/api/ready 应返 200(全就绪)或 503(任一挂)· 实际 {resp.status_code} "
            f"body={resp.text[:300]}",
        )
        data = resp.json()
        self.assertIn(
            "ready", data, msg=f"/api/ready 必须含 ready 布尔 · keys={sorted(data.keys())}"
        )
        self.assertIsInstance(data.get("ready"), bool, msg="ready 应是 bool")
        self.assertIn(
            "checks", data, msg=f"/api/ready 必须含 checks dict · keys={sorted(data.keys())}"
        )
        self.assertIsInstance(data.get("checks"), dict, msg="checks 应是 dict")
        for probe in ("db", "gemini", "smtp", "line"):
            self.assertIn(
                probe,
                data["checks"],
                msg=f"/api/ready checks 必须含 {probe} 探针 · 实际 {sorted(data['checks'].keys())}",
            )

    def test_ready_status_matches_checks(self) -> None:
        # 一致性:ready=True iff 所有探针 ok=True(铁律 #23.7「任一挂返非 200」)
        resp = self.client.get("/api/ready")
        data = resp.json()
        all_ok = all(c.get("ok") for c in data["checks"].values())
        self.assertEqual(
            data["ready"],
            all_ok,
            msg=f"ready({data['ready']}) 应等于 所有探针 ok({all_ok})· checks={data['checks']}",
        )
        # 503 ⇔ not ready
        if not data["ready"]:
            self.assertEqual(resp.status_code, 503, msg="not ready 必须 503")
        else:
            self.assertEqual(resp.status_code, 200, msg="ready 必须 200")


if __name__ == "__main__":
    unittest.main(verbosity=2)

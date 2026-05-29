#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_core_routes_presence.py · REFACTOR-WC-D3

域:核心路径"路由存在性"安全网 · 跨 7 条核心业务路径
本文件:1 个集成测试 · 只需 app import(不需 DB · 不需登录 · 不烧外部服务)

为啥要这个测试:
  窗口 A 正在拆 app.py(10k→<500)· 把 @app 路由逐个搬到独立 *_routes.py +
  app.include_router()。这种结构性搬迁最大的隐患 = "搬漏一条用户可见路由"——
  路由没注册进 app,前端调用 404,而其它测试(契约/鉴权闸)都按"路由存在"
  为前提,挡不住"整条路由消失"。

  本测试断言 7 条核心业务路径的关键 endpoint **仍然注册在 app.routes 里**。
  任一被静默搬丢 → 本测试红 → 重构 PR 被拦。这是"结构性重构别让用户可见
  路由凭空消失"的兜底,对应主计划硬门槛 #5(每条核心路径至少一个测试)。

设计:
  - 不查行为 · 只查"路由名册"(app.routes 的 path 集合)· 故无需 DB / 凭据。
  - app import 失败(缺依赖等)= SkipTest(沿用 _helpers 范式 · 不让 CI 假红)。
  - 断言的 18 个 path 均为 2026-05-29 从真实 app.app.routes 逐条 in 校验
    (非手写猜测 · 已剔除 /api/ocr/history-quota、/api/bank-recon/list 等
    实际不存在的旧文档式路径)· 全是结构性重构必须保持的稳定契约。
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

# 7 条核心业务路径 → 必须保持注册的用户可见 endpoint
# (路径字符串 2026-05-29 逐条 `in app.app.routes` 校验通过)
CORE_ROUTES = {
    "登录/auth": [
        "/api/auth/login",
        "/api/me",
    ],
    "注册/signup": [
        "/api/auth/signup",
    ],
    "上传识别/ocr": [
        "/api/ocr/recognize",
        "/api/ocr/quota",
        "/api/history",
    ],
    "销项税/vat": [
        "/api/vat_excel/check",
        "/api/vat_excel/build",
    ],
    "收入对账/recon": [
        "/api/bank-recon/upload",
        "/api/bank-recon/sessions",
        "/api/bank-recon/stats",
        "/api/recon/import/mappings",
        "/api/recon/import/save-mapping",
    ],
    "ERP推送/erp": [
        "/api/erp/endpoints",
    ],
    "充值/billing": [
        "/api/billing/status",
        "/api/billing/topup-request",
    ],
    "客户团队/clients-team": [
        "/api/clients",
        "/api/team/employees",
    ],
}


class CoreRoutesPresenceIntegrationTest(unittest.TestCase):
    """核心路径路由名册守门 · 防 app.py 拆分时静默丢用户可见路由。"""

    def setUp(self) -> None:
        # get_test_client 内部 import app · 失败则 SkipTest(无需 DB)
        self.client = get_test_client()
        import app  # noqa: WPS433 · 已由 get_test_client 验证可 import

        self.registered = {getattr(r, "path", "") for r in app.app.routes}

    def test_all_core_routes_still_registered(self) -> None:
        missing = []
        for path_group, paths in CORE_ROUTES.items():
            for path in paths:
                if path not in self.registered:
                    missing.append(f"{path_group} :: {path}")
        self.assertEqual(
            missing,
            [],
            msg=(
                "核心路径路由被搬丢(app.py 拆分回归)· 缺失:\n  "
                + "\n  ".join(missing)
                + "\n这些 endpoint 必须保持注册在 app.routes · 重构别让用户可见路由凭空消失。"
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

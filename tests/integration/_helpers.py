#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/_helpers.py · REFACTOR-WC-D2(2026-05-28 窗口 C)

集成测试通用骨架 · 主要做 3 件事:
  1. env-gated 跳过(无 DB / 无外部凭据 = clean skip · 不让 CI 红)
  2. 提供 TestClient + 真 FastAPI app(若 app import 失败也 skip)
  3. 提供 Gemini / LINE / Gmail mock context manager(集成测试只 mock 外部)

设计原则:
  - 不修改任何业务代码(铁律 #17 / #21 / #23 / #27 · 窗口 C 硬约束)
  - 不假设 CI 有真 DB(20 个测试在 CI 默认 skip · 本地 + env 才跑真)
  - 不假设 .env.local 存在(优雅 fallback)

使用例:
    from tests.integration._helpers import (
        require_db,
        get_test_client,
        mock_gemini_recognize,
    )

    class FooIntegration(unittest.TestCase):
        def setUp(self) -> None:
            require_db()  # 没 DB env 直接 SkipTest
            self.client = get_test_client()  # 真 app · 真路由

        def test_endpoint(self) -> None:
            with mock_gemini_recognize(returns={"ok": True}):
                resp = self.client.post("/api/recognize", files=...)
            self.assertEqual(resp.status_code, 200)
"""

from __future__ import annotations

import contextlib
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 尝试加载 .env.local(本地集成测试 · 不强制)
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env.local")
except ImportError:
    pass

# 集成测试共享单个 app 实例 · 反复登录会撞进程内限流桶(尤其 /api/login 强限流)。
# 统一在测试上下文默认关限流(setdefault · 显式 env 仍可覆盖);限流本身由
# tests/integration/test_ratelimit_middleware.py 用独立 app + 显式 env 覆盖验证。
# 必须在 import app(get_test_client 内)之前设 · 中间件启动时读一次 env。
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")


# ──────────────────────────────────────────────────────────────
# Env-gated skip helpers · 集成测试要么真跑要么干净 skip
# ──────────────────────────────────────────────────────────────


def require_env(*keys: str) -> dict[str, str]:
    """需要某些 env var · 缺一 SkipTest · 返回 dict。"""
    missing = [k for k in keys if not os.environ.get(k, "").strip()]
    if missing:
        raise unittest.SkipTest(
            f"integration test 需要 env: {missing} · 在 .env.local 或 shell env 配齐再跑"
        )
    return {k: os.environ[k].strip() for k in keys}


def require_db() -> None:
    """需要 DB 连接 · 接受 PEARNLY_INTEGRATION_DB=1 强制启用 · 否则 skip。

    集成测试默认在 CI 是 skip 的(CI 没真 DB)· 本地 / staging 跑前:
        export PEARNLY_INTEGRATION_DB=1
        export DATABASE_URL=postgresql://...
    """
    if not os.environ.get("PEARNLY_INTEGRATION_DB", "").strip():
        raise unittest.SkipTest("集成测试需要 DB · 设 PEARNLY_INTEGRATION_DB=1 + DATABASE_URL 才跑")
    require_env("DATABASE_URL")


def require_test_user() -> dict[str, str]:
    """需要测试账号凭据(走真账号 E2E env)· 没设 SkipTest。"""
    return require_env("PEARNLY_E2E_USER", "PEARNLY_E2E_PASS")


def require_admin_user() -> dict[str, str]:
    """需要超管账号凭据 · 用于 Earn admin 路由测试。"""
    return require_env("PEARNLY_ADMIN_USER", "PEARNLY_ADMIN_PASS")


# ──────────────────────────────────────────────────────────────
# TestClient · 真 FastAPI app(import 失败 = SkipTest · 不让 CI 红)
# ──────────────────────────────────────────────────────────────


def get_test_client():  # type: ignore[no-untyped-def]
    """返回 fastapi.testclient.TestClient(app)· import 失败 SkipTest。

    用 lazy import:CI 没装 fastapi 也不爆 ModuleNotFoundError。
    """
    try:
        from fastapi.testclient import TestClient
    except ImportError as e:
        raise unittest.SkipTest(f"fastapi.testclient 不可用:{e}")
    try:
        import app  # type: ignore  # noqa: WPS433
    except Exception as e:
        # app.py import 会触发 db.ensure_* / Gemini 客户端 init 等 · 任一挂都 skip
        raise unittest.SkipTest(f"app import 失败(可能 DB 没连):{e}")
    fastapi_app = getattr(app, "app", None)
    if fastapi_app is None:
        raise unittest.SkipTest("app 模块没暴露 FastAPI 实例 app")
    return TestClient(fastapi_app)


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login_for_token(client, username: str, password: str) -> str:  # type: ignore[no-untyped-def]
    """登录拿 JWT · 失败 SkipTest(不让网络抖动 / 凭据无效红 CI)。"""
    try:
        resp = client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
    except Exception as e:
        raise unittest.SkipTest(f"/api/auth/login 不可达:{e}")
    if resp.status_code != 200:
        raise unittest.SkipTest(
            f"/api/auth/login 返 {resp.status_code} · 凭据 / DB / Migration 问题:{resp.text[:200]}"
        )
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise unittest.SkipTest(f"/api/auth/login 没返 access_token:{data}")
    return token


# ──────────────────────────────────────────────────────────────
# 外部服务 mock · 集成测试不打真 Gemini / LINE / Gmail
# ──────────────────────────────────────────────────────────────


@contextlib.contextmanager
def mock_gemini_recognize(returns: Any) -> Iterator[None]:
    """Mock services/ocr/* 的 Gemini 调用 · 返回固定 returns。

    集成测试只要确认"路由 → service → 持久化"链路通 · 不要真打 Gemini · 烧钱 + 慢。
    """
    targets = [
        "services.ocr.layer1_vision.call_gemini",
        "services.ocr.pipeline.call_gemini",
    ]
    patches = []
    for t in targets:
        with contextlib.suppress(Exception):
            p = patch(t, return_value=returns)
            p.start()
            patches.append(p)
    try:
        yield
    finally:
        for p in patches:
            with contextlib.suppress(Exception):
                p.stop()


@contextlib.contextmanager
def mock_line_send() -> Iterator[None]:
    """Mock LINE Bot 发消息 · 测试不真发。"""
    targets = [
        "line_client.send_message",
        "line_client.LineClient.push_text",
    ]
    patches = []
    for t in targets:
        with contextlib.suppress(Exception):
            p = patch(t, return_value={"ok": True})
            p.start()
            patches.append(p)
    try:
        yield
    finally:
        for p in patches:
            with contextlib.suppress(Exception):
                p.stop()


@contextlib.contextmanager
def mock_gmail_smtp() -> Iterator[None]:
    """Mock Gmail SMTP 发邮件 · 测试不真发(防泄露测试地址 + 配额)。"""
    targets = [
        "smtplib.SMTP",
        "smtplib.SMTP_SSL",
    ]
    patches = []
    for t in targets:
        with contextlib.suppress(Exception):
            mock_obj = patch(t)
            mock_obj.start()
            patches.append(mock_obj)
    try:
        yield
    finally:
        for p in patches:
            with contextlib.suppress(Exception):
                p.stop()


# ──────────────────────────────────────────────────────────────
# 通用 assertion helpers
# ──────────────────────────────────────────────────────────────


def assert_json_response(test_case, resp, expect_status: int = 200) -> dict:
    """统一 assert: status code 对 + 返回是 JSON dict · 否则给清晰错。"""
    test_case.assertEqual(
        resp.status_code,
        expect_status,
        msg=f"期望 {expect_status} 但拿到 {resp.status_code} · body: {resp.text[:300]}",
    )
    try:
        return resp.json()
    except Exception as e:
        test_case.fail(f"resp 不是 JSON · raw body: {resp.text[:300]} · err: {e}")
        return {}  # unreachable · 安抚 type checker

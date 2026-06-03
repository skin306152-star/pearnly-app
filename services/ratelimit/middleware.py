# -*- coding: utf-8 -*-
"""services/ratelimit/middleware.py · REFACTOR-WA-B5 · 全局限流中间件(纯 ASGI)。

设计原则(保守 · 不误伤付费用户):
  - 默认每来源 RATE_LIMIT_PER_MIN=600 次/分钟(≈10 req/s · 正常浏览/批量 OCR 不触顶 ·
    只拦疯狂刷的脚本)· 全部走 env 可调 · 设 0 关闭限流。
  - 来源 key:已登录(带 Authorization)按 token 指纹分桶 · 否则按客户端 IP。
    (不解 JWT · token 指纹即可区分会话 · 与 auth 解耦)
  - 豁免:健康检查 / webhook / 版本 / 静态资源 —— 这些要么是基建探活,要么是部署回调,
    限流它们只会帮倒忙。
  - fail-open:限流器自身抛异常 → 放行(限流是附加防护 · 绝不能因它把站点锁死)。
  - 超限返 429 + Retry-After + 稳定错误码 JSON(error=too_many_requests)。
"""

from __future__ import annotations

import json
import os

from starlette.types import ASGIApp, Receive, Scope, Send

# 前缀豁免:基建 / 部署回调 / 版本探测 / 静态资源
_EXEMPT_PREFIXES = (
    "/api/health",
    "/api/ready",
    "/api/v1/health",
    "/api/version",
    "/internal/deploy",
    "/static",
    "/assets",
)


def _enabled() -> bool:
    return (os.environ.get("RATE_LIMIT_ENABLED") or "true").strip().lower() != "false"


def _limit_per_min() -> int:
    try:
        return int(os.environ.get("RATE_LIMIT_PER_MIN", "600"))
    except ValueError:
        return 600


def _client_ip(scope: Scope) -> str:
    headers = dict(scope.get("headers") or [])
    xff = headers.get(b"x-forwarded-for", b"").decode("latin-1").strip()
    if xff:
        return xff.split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


def _subject_key(scope: Scope) -> str:
    headers = dict(scope.get("headers") or [])
    auth = headers.get(b"authorization", b"").decode("latin-1").strip()
    if auth:
        # token 指纹分桶 · 不验签不解码 · 仅用于区分会话来源
        return "tok:" + str(hash(auth) & 0xFFFFFFFF)
    return "ip:" + _client_ip(scope)


def _is_exempt(path: str) -> bool:
    return any(path.startswith(p) for p in _EXEMPT_PREFIXES)


async def _reject(send: Send, retry_after: int) -> None:
    body = json.dumps({"error": "too_many_requests", "detail": "rate_limited"}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"application/json"),
                (b"retry-after", str(retry_after).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        # 进程内单例 limiter · 延迟 import 避免循环
        from services.ratelimit.limiter import FixedWindowLimiter

        self.limiter = FixedWindowLimiter()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not _enabled():
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if _is_exempt(path):
            await self.app(scope, receive, send)
            return

        try:
            allowed, retry_after = self.limiter.check(
                _subject_key(scope), _limit_per_min(), window=60
            )
        except Exception:  # fail-open:限流器挂了绝不锁站
            allowed, retry_after = True, 0

        if not allowed:
            await _reject(send, retry_after)
            return

        await self.app(scope, receive, send)

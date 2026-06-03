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

# 前缀豁免默认值:基建 / 部署回调 / 版本探测 / 静态资源 · 可经 RATE_LIMIT_EXEMPT_PREFIXES 覆盖
_DEFAULT_EXEMPT_PREFIXES = (
    "/api/health",
    "/api/ready",
    "/api/v1/health",
    "/api/version",
    "/internal/deploy",
    "/static",
    "/assets",
)


def _subject_key(headers: dict, scope: Scope) -> str:
    """限流分桶 key:已登录按 token 指纹 · 否则按客户端 IP(headers 已物化 · 不重复解析)。"""
    auth = headers.get(b"authorization", b"").decode("latin-1").strip()
    if auth:
        # token 指纹分桶 · 不验签不解码 · 仅用于区分会话来源
        return "tok:" + str(hash(auth) & 0xFFFFFFFF)
    xff = headers.get(b"x-forwarded-for", b"").decode("latin-1").strip()
    if xff:
        return "ip:" + xff.split(",")[0].strip()
    client = scope.get("client")
    return "ip:" + (client[0] if client else "unknown")


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
        # 配置在启动读一次(env 改动随重启生效)· 避免每请求 os.environ 查询+解析
        self.enabled = (os.environ.get("RATE_LIMIT_ENABLED") or "true").strip().lower() != "false"
        try:
            self.limit = int(os.environ.get("RATE_LIMIT_PER_MIN", "600"))
        except ValueError:
            self.limit = 600
        override = (os.environ.get("RATE_LIMIT_EXEMPT_PREFIXES") or "").strip()
        self.exempt = (
            tuple(p.strip() for p in override.split(",") if p.strip()) or _DEFAULT_EXEMPT_PREFIXES
        )
        # 进程内单例 limiter · 延迟 import 避免循环
        from services.ratelimit.limiter import FixedWindowLimiter

        self.limiter = FixedWindowLimiter()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        # str.startswith 接受前缀元组 · 一次判断所有豁免前缀
        if scope.get("path", "").startswith(self.exempt):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])  # 物化一次 · 供分桶 key 复用
        try:
            allowed, retry_after = self.limiter.check(
                _subject_key(headers, scope), self.limit, window=60
            )
        except Exception:  # fail-open:限流器挂了绝不锁站
            allowed, retry_after = True, 0

        if not allowed:
            await _reject(send, retry_after)
            return

        await self.app(scope, receive, send)

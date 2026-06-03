# -*- coding: utf-8 -*-
"""services/observability/request_context.py · REFACTOR-WA-B6 · 请求上下文中间件。

纯 ASGI 中间件(非 BaseHTTPMiddleware):BaseHTTPMiddleware 在独立 task 跑下游,
contextvar 不保证传播到路由 handler;纯 ASGI 与 handler 同 task · request_id 全程可见。

每个 HTTP 请求:
  - 入站带 X-Request-ID 则沿用(利于反代/客户端跨服务串联)· 否则生成 uuid4
  - 绑进 log_context · 本请求所有日志自动带 request_id
  - 响应头回写 X-Request-ID · 用户报障可据此定位
user_id / tenant_id 由鉴权层后续绑定(中间件阶段尚不知身份)。
"""

from __future__ import annotations

import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from services.observability import log_context

_HEADER = b"x-request-id"


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        incoming = headers.get(_HEADER, b"").decode("latin-1").strip()
        request_id = incoming or uuid.uuid4().hex
        tokens = log_context.bind(request_id=request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append((_HEADER, request_id.encode("latin-1")))
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            log_context.reset(tokens)

# -*- coding: utf-8 -*-
"""Small, non-breaking security header middleware."""

from __future__ import annotations

import os

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# CSP 默认策略(安全评估 2026-07-07 L2)· 域名取自前端实际加载来源 · 经 env 覆盖收紧。
# 首发以 report-only 挂载:只上报违规、不拦截,确认真实页面零误伤后再转强制(CSP_REPORT_ONLY=false)。
_DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob: https://api.qrserver.com https://*.line-scdn.net "
    "https://*.googleusercontent.com https://storage.googleapis.com https://www.mrerp4sme.com; "
    "connect-src 'self' https://api.line.me https://access.line.me; "
    "frame-src 'self' https://liff.line.me https://access.line.me; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        # 空串可关闭 CSP;默认 report-only(先观察不拦截,防把页面打崩)
        self.csp = os.environ.get("CONTENT_SECURITY_POLICY", _DEFAULT_CSP).strip()
        self.csp_report_only = (
            os.environ.get("CSP_REPORT_ONLY") or "true"
        ).strip().lower() != "false"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.setdefault(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains; preload",
                )
                headers.setdefault(
                    "Permissions-Policy",
                    "camera=(self), microphone=(), geolocation=(), payment=(), usb=(), serial=()",
                )
                if self.csp:
                    name = (
                        "Content-Security-Policy-Report-Only"
                        if self.csp_report_only
                        else "Content-Security-Policy"
                    )
                    headers.setdefault(name, self.csp)
            await send(message)

        await self.app(scope, receive, send_with_headers)

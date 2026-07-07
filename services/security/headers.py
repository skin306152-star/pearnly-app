# -*- coding: utf-8 -*-
"""Small, non-breaking security header middleware."""

from __future__ import annotations

import os

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# CSP(安全评估 2026-07-07 L2)· 分两档下发:
#  ① 强制档 _ENFORCE_CSP:只含真浏览器登录+面板复验过零误伤的指令(script/object/base)。
#     script-src 白名单取自前端全量扫描 + prod 真机 CSP 违规抓取(仅 CF beacon 需加白)。
#     它挡住"从外域注入脚本 / <object> 插件 / <base> 注入"这些真 XSS 载体;点击劫持已由
#     X-Frame-Options: DENY 覆盖。img-src/connect-src/frame/form 涉收据图、OAuth 表单跳转、
#     LIFF 等合成浏览难穷尽的路径,先不强制免误伤。
#  ② 观察档 _REPORT_CSP:完整策略以 report-only 下发,持续观察真实流量违规,零误伤确认后再升格强制。
_ENFORCE_CSP = (
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
    "https://cdnjs.cloudflare.com https://static.cloudflareinsights.com; "
    "object-src 'none'; base-uri 'self'"
)
_REPORT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com "
    "https://static.cloudflareinsights.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob: https://api.qrserver.com https://*.line-scdn.net "
    "https://*.googleusercontent.com https://storage.googleapis.com https://www.mrerp4sme.com; "
    "connect-src 'self' https://api.line.me https://access.line.me https://static.cloudflareinsights.com; "
    "frame-src 'self' https://liff.line.me https://access.line.me; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        # 两档独立、均可 env 覆盖/空串关闭。强制档下发 Content-Security-Policy,
        # 观察档下发 Content-Security-Policy-Report-Only(见常量注释)。
        self.csp_enforce = os.environ.get("CSP_ENFORCE", _ENFORCE_CSP).strip()
        self.csp_report = os.environ.get("CONTENT_SECURITY_POLICY", _REPORT_CSP).strip()

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
                if self.csp_enforce:
                    headers.setdefault("Content-Security-Policy", self.csp_enforce)
                if self.csp_report:
                    headers.setdefault("Content-Security-Policy-Report-Only", self.csp_report)
            await send(message)

        await self.app(scope, receive, send_with_headers)

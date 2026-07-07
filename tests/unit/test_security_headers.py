# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.security.headers import SecurityHeadersMiddleware


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    app.add_middleware(SecurityHeadersMiddleware)
    return TestClient(app)


class SecurityHeadersMiddlewareTests(unittest.TestCase):
    def test_adds_non_breaking_baseline_headers(self):
        resp = _client().get("/ping")

        self.assertEqual(resp.headers["x-content-type-options"], "nosniff")
        self.assertEqual(resp.headers["x-frame-options"], "DENY")
        self.assertEqual(resp.headers["referrer-policy"], "strict-origin-when-cross-origin")
        self.assertIn("max-age=31536000", resp.headers["strict-transport-security"])
        self.assertIn("geolocation=()", resp.headers["permissions-policy"])

    def test_csp_emits_both_enforce_and_report(self):
        # 强制档 + 观察档同时下发:强制档 = 已复验子集,观察档 = 完整策略
        resp = _client().get("/ping")
        enforce = resp.headers["content-security-policy"]
        report = resp.headers["content-security-policy-report-only"]
        self.assertIn("script-src 'self'", enforce)
        self.assertIn("object-src 'none'", enforce)
        self.assertIn("default-src 'self'", report)  # 完整策略才有 default-src

    def test_enforce_omits_unverified_directives(self):
        # 不变量:强制档只含真机复验过的指令,决不含 img/connect/frame/form(防误伤)
        enforce = _client().get("/ping").headers["content-security-policy"]
        for unverified in ("img-src", "connect-src", "frame-ancestors", "form-action"):
            self.assertNotIn(unverified, enforce)

    def test_cloudflareinsights_whitelisted(self):
        # 回归守门:CF 边缘注入的 beacon 必须在两档白名单内(prod 真机抓到过该违规)
        resp = _client().get("/ping")
        self.assertIn("static.cloudflareinsights.com", resp.headers["content-security-policy"])
        self.assertIn(
            "static.cloudflareinsights.com",
            resp.headers["content-security-policy-report-only"],
        )

    def test_both_csp_disabled_when_env_empty(self):
        with patch.dict(os.environ, {"CSP_ENFORCE": "", "CONTENT_SECURITY_POLICY": ""}):
            resp = _client().get("/ping")
        self.assertNotIn("content-security-policy", resp.headers)
        self.assertNotIn("content-security-policy-report-only", resp.headers)


if __name__ == "__main__":
    unittest.main()

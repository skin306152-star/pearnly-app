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

    def test_csp_defaults_to_report_only(self):
        # 首发 report-only:上报违规不拦截 · 强制头不应出现
        resp = _client().get("/ping")
        self.assertIn("content-security-policy-report-only", resp.headers)
        self.assertIn("default-src 'self'", resp.headers["content-security-policy-report-only"])
        self.assertNotIn("content-security-policy", resp.headers)

    def test_csp_enforcing_when_env_false(self):
        with patch.dict(os.environ, {"CSP_REPORT_ONLY": "false"}):
            resp = _client().get("/ping")
        self.assertIn("content-security-policy", resp.headers)
        self.assertNotIn("content-security-policy-report-only", resp.headers)

    def test_csp_disabled_when_empty(self):
        with patch.dict(os.environ, {"CONTENT_SECURITY_POLICY": ""}):
            resp = _client().get("/ping")
        self.assertNotIn("content-security-policy", resp.headers)
        self.assertNotIn("content-security-policy-report-only", resp.headers)


if __name__ == "__main__":
    unittest.main()

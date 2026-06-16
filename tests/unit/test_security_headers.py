# -*- coding: utf-8 -*-
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.security.headers import SecurityHeadersMiddleware


class SecurityHeadersMiddlewareTests(unittest.TestCase):
    def test_adds_non_breaking_baseline_headers(self):
        app = FastAPI()

        @app.get("/ping")
        def ping():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        resp = TestClient(app).get("/ping")

        self.assertEqual(resp.headers["x-content-type-options"], "nosniff")
        self.assertEqual(resp.headers["x-frame-options"], "DENY")
        self.assertEqual(resp.headers["referrer-policy"], "strict-origin-when-cross-origin")
        self.assertIn("max-age=31536000", resp.headers["strict-transport-security"])
        self.assertIn("geolocation=()", resp.headers["permissions-policy"])


if __name__ == "__main__":
    unittest.main()

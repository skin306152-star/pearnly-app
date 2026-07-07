# -*- coding: utf-8 -*-
"""CSP 违规上报端点:两种上报形状都解析落日志,垃圾/超大 body 不炸恒 204(安全评估 2026-07-07)。"""

from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.security_routes import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class CspReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = _client()

    def test_report_uri_shape_logged(self) -> None:
        payload = {
            "csp-report": {
                "violated-directive": "script-src",
                "blocked-uri": "https://evil.example/x.js",
                "document-uri": "https://pearnly.com/",
            }
        }
        with self.assertLogs("mr-pilot", level="WARNING") as cm:
            resp = self.client.post("/api/csp-report", json=payload)
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(any("evil.example" in m for m in cm.output))

    def test_report_to_shape_logged(self) -> None:
        payload = [
            {"body": {"effectiveDirective": "img-src", "blockedURL": "https://x.test/a.png"}}
        ]
        with self.assertLogs("mr-pilot", level="WARNING") as cm:
            resp = self.client.post("/api/csp-report", json=payload)
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(any("img-src" in m for m in cm.output))

    def test_garbage_body_is_204(self) -> None:
        self.assertEqual(self.client.post("/api/csp-report", content=b"not json").status_code, 204)

    def test_oversized_body_dropped(self) -> None:
        big = b'{"csp-report":{"blocked-uri":"' + b"a" * (20 * 1024) + b'"}}'
        self.assertEqual(self.client.post("/api/csp-report", content=big).status_code, 204)


if __name__ == "__main__":
    unittest.main()

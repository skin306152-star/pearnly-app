#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_erp_test_connection_route_dispatch.py

v118.34.1 (Zihao 2026-05-19 拍板) · Regression guard for the
`/api/erp/test-connection` route's mrerp dispatch.

Why this test exists:
    The original C-1 wiring shipped a `push_mrerp` stub in the
    ADAPTER_REGISTRY (erp_push.py:207) whose only job was to refuse
    push calls with the message
        "mrerp push is not wired into push_to_endpoint yet"
    The legacy `/api/erp/test-connection` route went
        adapter str → ADAPTER_REGISTRY[adapter] → push_mrerp(...)
    which surfaced that refusal as a fake "connection failed" — so the
    wizard's Step-2 test button always failed before even attempting
    the real MR.ERP login.

What this test pins down:
    1. The stub still exists (we didn't accidentally turn it into a real
       push without realising the test-connection route would silently
       gain push behaviour — an even worse outcome).
    2. test_endpoint_connection("mrerp", ...) WOULD return the stub
       message if anyone hooked it back up to the route. This proves
       the hazard is realizable, so the fix must avoid that path.
    3. The route must NOT delegate the mrerp branch through
       test_endpoint_connection / push_mrerp; it MUST call
       test_mrerp_endpoint(cfg) directly.

If this test ever regresses, somebody re-introduced the stub-as-
test-connection bug — yank their commit.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import erp_push as _erp   # noqa: E402


class StubContractTests(unittest.TestCase):
    """Pin down that the stub still exists and would still bite if used."""

    def test_push_mrerp_is_still_a_refusal_stub(self):
        """If someone implements push_mrerp for real but doesn't also
        re-check the test-connection routing, the wizard would silently
        start pushing test invoices when the user clicks the test button.
        Catch that change here so the reviewer is forced to rethink."""
        success, http_status, body = _erp.push_mrerp({}, {"test": True})
        self.assertFalse(success, "push_mrerp suddenly returns success — re-audit test-connection routing")
        self.assertEqual(http_status, 0)
        self.assertIn("not wired", body.lower())

    def test_adapter_registry_mrerp_points_at_stub(self):
        self.assertIs(_erp.ADAPTER_REGISTRY.get("mrerp"), _erp.push_mrerp)

    def test_test_endpoint_connection_would_surface_stub_for_mrerp(self):
        """This is the bug shape we ship to prevent: if the route ever
        routes mrerp through test_endpoint_connection, the user sees
        the stub message instead of a real login attempt."""
        result = _erp.test_endpoint_connection("mrerp", {
            "system_url": "https://example.invalid",
            "username_enc": "u", "password_enc": "p",
        })
        self.assertFalse(result["success"])
        # The exact phrase the user reported in the F12 Response trace.
        self.assertIn("not wired into push_to_endpoint",
                      (result.get("response_body") or "")
                      + " "
                      + (result.get("error_msg") or ""))


class TestMrerpEndpointDoesNotUseStubTests(unittest.TestCase):
    """test_mrerp_endpoint must own the mrerp test-connection path
    and never delegate to the stub."""

    def test_empty_config_short_circuits_with_friendly_error(self):
        result = _erp.test_mrerp_endpoint({})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "ERR_NO_CREDS")
        self.assertIsInstance(result.get("error_friendly"), dict)
        # Most damning regression: the stub message must not appear.
        raw = (result.get("raw_error") or "").lower()
        self.assertNotIn("not wired", raw)
        self.assertNotIn("push_to_endpoint", raw)

    def test_response_shape_is_rich_not_legacy(self):
        """test_mrerp_endpoint returns {ok, companies, error_friendly,
        ...} — the wizard JS depends on this. If anyone replaces it with
        a legacy {success, response_body, ...} shape, the UI silently
        renders blank error bars."""
        result = _erp.test_mrerp_endpoint({})
        for key in ("ok", "elapsed_ms", "companies", "error_code",
                    "error_friendly", "raw_error"):
            self.assertIn(key, result,
                          f"missing rich-shape key {key!r}; result={result!r}")


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed in this env — route-level dispatch test is "
    "covered server-side; the contract tests above still run.",
)
class RouteDispatchTests(unittest.TestCase):
    """Route-handler test using FastAPI TestClient. Patches auth + the
    two erp helpers so we can assert the dispatch decision directly."""

    @classmethod
    def setUpClass(cls):
        # Importing app boots the whole FastAPI stack; do it once for
        # the suite.
        import os
        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app   # noqa: F401
        cls.app_module = app

    def _make_client(self):
        from fastapi.testclient import TestClient
        return TestClient(self.app_module.app)

    def test_route_calls_test_mrerp_endpoint_not_legacy_for_mrerp(self):
        """The actual bug: mrerp adapter must NOT route through
        test_endpoint_connection (which falls into push_mrerp stub)."""
        app = self.app_module
        mrerp_mock = MagicMock(return_value={
            "ok": True, "elapsed_ms": 100, "companies": [],
            "error_code": None, "error_friendly": None, "raw_error": None,
        })
        legacy_mock = MagicMock(return_value={
            "success": False, "http_status": 0, "response_body": "stub",
            "error_msg": "stub", "elapsed_ms": 0,
        })

        with patch.object(app, "get_current_user_from_request",
                          return_value={"id": "u-test", "plan": "pro"}), \
             patch.object(app, "_check_push_access", return_value=None), \
             patch.object(app._erp, "test_mrerp_endpoint", mrerp_mock), \
             patch.object(app._erp, "test_endpoint_connection", legacy_mock):
            with self._make_client() as client:
                r = client.post("/api/erp/test-connection", json={
                    "adapter": "mrerp",
                    "config": {
                        "system_url": "https://x.invalid",
                        "username_enc": "u", "password_enc": "p",
                    },
                })

        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"), f"route swallowed success flag: {body!r}")
        mrerp_mock.assert_called_once()
        legacy_mock.assert_not_called()

    def test_route_still_uses_legacy_for_webhook(self):
        """The fix must not break other adapters — webhook (and any
        non-mrerp adapter in the registry) should still go through
        test_endpoint_connection."""
        app = self.app_module
        mrerp_mock = MagicMock()
        legacy_mock = MagicMock(return_value={
            "success": True, "http_status": 200, "response_body": "ok",
            "error_msg": None, "elapsed_ms": 5,
        })

        with patch.object(app, "get_current_user_from_request",
                          return_value={"id": "u-test", "plan": "pro"}), \
             patch.object(app, "_check_push_access", return_value=None), \
             patch.object(app._erp, "test_mrerp_endpoint", mrerp_mock), \
             patch.object(app._erp, "test_endpoint_connection", legacy_mock):
            with self._make_client() as client:
                r = client.post("/api/erp/test-connection", json={
                    "adapter": "webhook",
                    "config": {"url": "https://example.invalid/hook"},
                })

        self.assertEqual(r.status_code, 200, r.text)
        legacy_mock.assert_called_once()
        mrerp_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)

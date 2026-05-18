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


class HardeningContractTests(unittest.TestCase):
    """v118.34.2 contract: test_mrerp_endpoint must NEVER raise, must
    accept both {username, password} plaintext and {username_enc,
    password_enc} ciphertext, and must surface a friendly error even
    when its imports fail."""

    def test_never_raises_on_garbage_input(self):
        """Hammer it with malformed input — None, weird types, mixed
        shapes — and verify it always returns a dict, never throws."""
        cases = [
            None,
            {},
            {"username": "u"},   # missing password
            {"password": "p"},   # missing username
            {"username": "", "password": ""},  # both empty strings
            {"username": "u", "password": "p", "system_url": ""},  # empty url
            {"username_enc": "garbage", "password_enc": "more-garbage"},
            {"username_enc": "gAAAAA-but-truncated"},  # looks-fernet-but-broken
        ]
        for cfg in cases:
            try:
                result = _erp.test_mrerp_endpoint(cfg)
            except Exception as e:
                self.fail(
                    f"test_mrerp_endpoint raised {type(e).__name__} on "
                    f"input {cfg!r}: {e!s}"
                )
            self.assertIsInstance(result, dict, f"non-dict for {cfg!r}")
            self.assertIn("ok", result)
            self.assertFalse(
                result["ok"],
                f"unexpected ok=True for malformed input {cfg!r}",
            )
            # Friendly error is always populated when ok=False.
            self.assertIsInstance(
                result.get("error_friendly"), dict,
                f"missing error_friendly for {cfg!r}: {result!r}",
            )

    def test_accepts_plaintext_credentials_shape(self):
        """Wizard sends {username, password} (plain). Backend must not
        complain about missing _enc fields — it should attempt
        construction and fail downstream (auth/network), not ERR_NO_CREDS."""
        result = _erp.test_mrerp_endpoint({
            "system_url": "https://invalid.example.org",
            "username": "user-xyz",
            "password": "pass-xyz",
            "comidyear": "6", "seldb": "1",
        })
        self.assertFalse(result["ok"])
        # Either we got past creds and hit a network/auth/playwright
        # error, OR Playwright is missing on this host. Both are fine —
        # the important thing is we DIDN'T report ERR_NO_CREDS for a
        # request that supplied creds in the plaintext shape.
        self.assertNotEqual(
            result["error_code"], "ERR_NO_CREDS",
            f"plaintext shape rejected as missing creds: {result!r}",
        )

    def test_garbage_in_plaintext_field_routes_through_to_login(self):
        """Garbage value typed into 'username' is NOT a decrypt issue;
        it should reach the login attempt (and fail there)."""
        result = _erp.test_mrerp_endpoint({
            "system_url": "https://invalid.example.org",
            "username": "definitely-not-a-real-account",
            "password": "x",
        })
        self.assertFalse(result["ok"])
        # Not a decrypt issue because we sent plain.
        self.assertNotEqual(result["error_code"], "ERR_CRED_DECRYPT")

    def test_import_failure_returns_friendly_not_500(self):
        """If the heavy MR.ERP/Playwright import fails (simulated by
        patching the lazy import inside the function), we MUST surface
        an ERR_PLAYWRIGHT_MISSING / ERR_UNEXPECTED with a friendly
        catalogue — NOT raise (which becomes a 500 to the UI)."""
        import builtins
        real_import = builtins.__import__

        def boom(name, *a, **kw):
            if "mrerp_adapter" in name:
                raise ImportError("No module named 'playwright.sync_api'")
            return real_import(name, *a, **kw)

        with patch.object(builtins, "__import__", side_effect=boom):
            result = _erp.test_mrerp_endpoint({
                "username": "u", "password": "p",
            })
        self.assertIsInstance(result, dict)
        self.assertFalse(result["ok"])
        self.assertIn(result["error_code"],
                      ("ERR_PLAYWRIGHT_MISSING", "ERR_UNEXPECTED"))
        self.assertIsInstance(result["error_friendly"], dict)
        # Friendly text must mention playwright OR mention server error.
        any_lang_text = " ".join(result["error_friendly"].values()).lower()
        self.assertTrue(
            "playwright" in any_lang_text or "server" in any_lang_text
            or "服务器" in any_lang_text or "伺服器" in any_lang_text,
            f"friendly message uninformative: {result['error_friendly']!r}",
        )


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

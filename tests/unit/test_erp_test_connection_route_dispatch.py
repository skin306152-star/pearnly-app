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

    def test_test_connection_route_calls_mrerp_adapter_not_push_stub(self):
        """v118.34.4 (Zihao 2026-05-19 拍板) · The named guard the user
        explicitly demanded. Source of truth for the contract:

            "test-connection 路由 mrerp 分支改成直接 instantiate
             MRERPAdapter + 调 login + select_company · 不要走
             push_to_endpoint stub"

        We verify this by calling _erp.test_mrerp_endpoint (the function
        the routes — both /api/erp/test-connection and
        /api/erp/endpoints/:id/test-connection — delegate to for mrerp)
        with empty config. The result MUST be the rich `test_mrerp_endpoint`
        shape ({ok, companies, error_friendly, ...}), NOT the
        push_mrerp stub shape ({success, response_body, error_msg}).

        Critically, the raw_error/response_body MUST NOT carry the
        stub's "not wired into push_to_endpoint yet" phrase — that's
        the smoking-gun string that surfaced in the user's F12 trace.

        If this test ever fails, either:
          (a) someone rewired the route through ADAPTER_REGISTRY again
              (the original C-1 trap), OR
          (b) someone changed test_mrerp_endpoint's response shape and
              broke the wizard's UI contract.
        Either way: revert their commit, do not patch around it.
        """
        result = _erp.test_mrerp_endpoint({})
        # ── Shape: rich, not stub ──
        for required_key in ("ok", "companies", "error_code",
                             "error_friendly", "raw_error", "elapsed_ms"):
            self.assertIn(required_key, result,
                          f"rich shape missing {required_key!r}; "
                          f"someone may have routed mrerp through "
                          f"push_to_endpoint again: {result!r}")
        # The stub-shape keys must NOT leak through.
        for stub_key in ("response_body", "http_status"):
            self.assertNotIn(stub_key, result,
                             f"stub-shape key {stub_key!r} leaked into "
                             f"test_mrerp_endpoint result; mrerp branch "
                             f"is delegating through push_mrerp again: "
                             f"{result!r}")
        # The smoking-gun substring from the user's F12 trace.
        joined = " ".join([
            str(result.get("raw_error") or ""),
            str(result.get("error_code") or ""),
            " ".join((result.get("error_friendly") or {}).values()),
        ]).lower()
        self.assertNotIn("not wired into push_to_endpoint", joined,
                         f"stub message leaked into mrerp test-connection: "
                         f"{result!r}")
        # And empty-config short-circuit returns ERR_NO_CREDS, not
        # ERR_PUSH_NOT_WIRED — proves we went through test_mrerp_endpoint
        # not push_mrerp.
        self.assertEqual(result.get("error_code"), "ERR_NO_CREDS")

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


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None
    and __import__("importlib").util.find_spec("httpx") is not None,
    "needs fastapi + httpx; the async route test is covered server-side.",
)
class AsyncLoopOffloadTests(unittest.IsolatedAsyncioTestCase):
    """v118.34.10 (Zihao 2026-05-19 拍板) · The named guard the user
    explicitly demanded after seeing the
        'Playwright Sync API inside the asyncio loop'
    error from a real production click.

    Source contract:
        > test_test_connection_route_in_async_context_does_not_block
        > 在真 async 环境里调一次 · 确保不出 sync/async 冲突

    The flaw the user caught: my existing unit tests run inside
    pytest/unittest sync land, so they never exercised the route's
    async-handler-to-sync-Playwright path. The bug only shows up when
    the route's `await` chain reaches the Playwright sync_api with a
    running asyncio loop in scope. Playwright explicitly detects
    asyncio.get_running_loop() and refuses to start.

    These tests plant a "tripwire" sync helper that does the same
    detection. If the route calls the helper without offloading
    (i.e. uses `_erp.test_mrerp_endpoint(cfg)` directly), the helper
    runs inside the event loop, the tripwire fires, the test fails
    with a clear message. If the route uses
    `await asyncio.to_thread(_erp.test_mrerp_endpoint, cfg)`, the
    helper runs in a worker thread (no loop), tripwire passes.

    Covers ALL the production async routes that touch MRERPAdapter:
      • /api/erp/test-connection
      • /api/erp/endpoints/:id/test-connection
      • /api/erp/endpoints/:id/customers
      • /api/erp/endpoints/:id/products
      • /api/erp/push
    """

    @classmethod
    def setUpClass(cls):
        import os
        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app   # noqa
        cls.app_module = app

    @staticmethod
    def _tripwire_sync_helper(*args, **kwargs):
        """Pretends to be a sync helper. Records whether it was called
        from within an asyncio loop (BAD) or from a worker thread (GOOD).

        Returns the rich-shape success dict so the route's downstream
        code is happy — we don't want to mask the bug behind a different
        failure mode."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # We're inside an event loop — route did NOT offload.
            # Raise the exact Playwright error text so the failure
            # mode matches what the user saw on production.
            raise RuntimeError(
                "It looks like you are using Playwright Sync API "
                "inside the asyncio loop. Please use the Async API "
                "instead. (tripwire from "
                "AsyncLoopOffloadTests · loop=" + repr(loop) + ")"
            )
        except RuntimeError as e:
            if "Sync API inside" in str(e):
                raise
            # No running loop — we're in a thread. Good.
        return {
            "ok": True, "elapsed_ms": 12, "companies": [],
            "error_code": None, "error_friendly": None, "raw_error": None,
            "customers": [], "products": [],
            "success": True, "http_status": 200, "response_body": "ok",
            "error_msg": None, "request_body": None, "adapter": "mrerp",
        }

    async def _make_async_client(self):
        import httpx
        try:
            from httpx import ASGITransport
            transport = ASGITransport(app=self.app_module.app)
            return httpx.AsyncClient(transport=transport, base_url="http://test")
        except ImportError:
            # Older httpx without explicit ASGITransport
            return httpx.AsyncClient(app=self.app_module.app, base_url="http://test")

    async def test_test_connection_route_in_async_context_does_not_block(self):
        """The named test from the user's spec. Hits the legacy
        /api/erp/test-connection route with adapter=mrerp from a real
        async client and asserts the route offloads to a thread."""
        app = self.app_module
        with patch.object(app, "get_current_user_from_request",
                          return_value={"id": "u", "plan": "pro"}), \
             patch.object(app, "_check_push_access", return_value=None), \
             patch.object(app._erp, "test_mrerp_endpoint",
                          side_effect=self._tripwire_sync_helper):
            client = await self._make_async_client()
            async with client:
                r = await client.post("/api/erp/test-connection", json={
                    "adapter": "mrerp",
                    "config": {"username": "u", "password": "p"},
                })
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(
            body.get("ok"),
            f"route response not ok (tripwire likely fired): {body!r}",
        )

    async def test_per_endpoint_test_connection_route_offloads(self):
        """Same tripwire on the per-endpoint variant."""
        app = self.app_module
        fake_ep = {
            "id": "ep-1", "adapter": "mrerp", "config": {"username": "u"},
            "enabled": True,
        }
        with patch.object(app, "get_current_user_from_request",
                          return_value={"id": "u", "plan": "pro"}), \
             patch.object(app, "_check_push_access", return_value=None), \
             patch.object(app.db, "get_erp_endpoint", return_value=fake_ep), \
             patch.object(app._erp, "test_mrerp_endpoint",
                          side_effect=self._tripwire_sync_helper):
            client = await self._make_async_client()
            async with client:
                r = await client.post(
                    "/api/erp/endpoints/ep-1/test-connection?refresh=1",
                )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(
            body.get("ok"),
            f"per-endpoint route tripwire fired: {body!r}",
        )

    async def test_customers_route_offloads(self):
        app = self.app_module
        fake_ep = {"id": "ep-1", "adapter": "mrerp", "config": {}, "enabled": True}
        with patch.object(app, "get_current_user_from_request",
                          return_value={"id": "u", "plan": "pro"}), \
             patch.object(app, "_check_push_access", return_value=None), \
             patch.object(app.db, "get_erp_endpoint", return_value=fake_ep), \
             patch.object(app._erp, "list_mrerp_customers",
                          side_effect=self._tripwire_sync_helper):
            client = await self._make_async_client()
            async with client:
                r = await client.get(
                    "/api/erp/endpoints/ep-1/customers?refresh=1",
                )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        # Tripwire dict carries ok=True. If route bypassed to_thread,
        # the route would have hit RuntimeError and returned an
        # error_code in the friendly catch block.
        self.assertTrue(
            body.get("ok"),
            f"customers route tripwire fired: {body!r}",
        )

    async def test_products_route_offloads(self):
        app = self.app_module
        fake_ep = {"id": "ep-1", "adapter": "mrerp", "config": {}, "enabled": True}
        with patch.object(app, "get_current_user_from_request",
                          return_value={"id": "u", "plan": "pro"}), \
             patch.object(app, "_check_push_access", return_value=None), \
             patch.object(app.db, "get_erp_endpoint", return_value=fake_ep), \
             patch.object(app._erp, "list_mrerp_products",
                          side_effect=self._tripwire_sync_helper):
            client = await self._make_async_client()
            async with client:
                r = await client.get(
                    "/api/erp/endpoints/ep-1/products?refresh=1",
                )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(
            body.get("ok"),
            f"products route tripwire fired: {body!r}",
        )

    async def test_push_route_offloads(self):
        """`push_to_endpoint` MUST also be offloaded because once the
        mrerp branch lights up it will drive MRERPAdapter the same way."""
        app = self.app_module
        fake_ep = {"id": "ep-1", "adapter": "webhook",
                   "config": {"url": "http://example/"}, "enabled": True}
        fake_history = {
            "id": "h-1", "invoice_no": "INV-1",
            "seller_name": "S", "total_amount": "100",
        }
        with patch.object(app, "get_current_user_from_request",
                          return_value={"id": "u", "plan": "pro"}), \
             patch.object(app, "_check_push_access", return_value=None), \
             patch.object(app.db, "get_ocr_history_detail", return_value=fake_history), \
             patch.object(app.db, "get_erp_endpoint", return_value=fake_ep), \
             patch.object(app.db, "insert_push_log", return_value="log-1"), \
             patch.object(app.db, "update_endpoint_stats", return_value=None), \
             patch.object(app.db, "update_history_push_status", return_value=None), \
             patch.object(app._erp, "push_to_endpoint",
                          side_effect=self._tripwire_sync_helper):
            client = await self._make_async_client()
            async with client:
                r = await client.post("/api/erp/push", json={
                    "history_id": "h-1", "endpoint_id": "ep-1",
                })
        # Route returns ok status; key thing is the route DIDN'T hit
        # the tripwire (which would've raised RuntimeError).
        self.assertIn(r.status_code, (200, 500), r.text)
        if r.status_code == 500:
            # Inspect what raised; tripwire-fired indicates the bug.
            self.assertNotIn("Playwright Sync API", r.text,
                             f"push route did NOT offload: {r.text}")


@unittest.skipUnless(
    __import__("importlib").util.find_spec("playwright") is not None,
    "playwright not installed in this env — chromium launch test only "
    "runs where the package is present (skipped in clean dev boxes).",
)
class ChromiumActualLaunchTests(unittest.TestCase):
    """v118.34.11 (Zihao 2026-05-19 拍板) · The named guard test the
    user explicitly demanded after the TargetClosedError:

        > test_chromium_can_actually_launch_in_production_env
        > mock 不行 · 真起一个 browser 才算过

    Forces a REAL chromium launch with the same server-side flags
    production uses (--no-sandbox / --disable-dev-shm-usage / --disable-gpu).
    If chromium can't actually launch in this environment, this test
    fails with the exact same error text the wizard would surface to
    the user. No mocks.

    Why this matters: previously we shipped v118.34.9 with
    `playwright_installed: true` and `chromium_installed: true` BOTH
    showing green via /api/version, but production click still
    crashed because system libs (libnss3, libgbm1, libcups2, ...)
    weren't installed. The binary was on disk, the binary was just
    unable to RUN. A boolean "is the file there" check is the
    wrong assertion — the right one is "does it boot?".

    Auto-skips when playwright pip package isn't installed. On
    server-side / CI where playwright IS installed, this test must
    pass; failure means the chromium environment is broken and
    deploys should be paused until install-deps lands.
    """

    def test_chromium_can_actually_launch_in_production_env(self):
        """Real launch, real version probe, real close. The test from
        the user's spec, verbatim."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            self.skipTest(f"playwright import failed in this env: {e}")

        pw = None
        browser = None
        try:
            pw = sync_playwright().start()
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            # Browser.version is a property in playwright-python sync
            # API, not a method.
            version = browser.version
            # Sanity check the version string looks plausible.
            self.assertRegex(
                version, r"^\d+\.",
                f"chromium reported odd version string: {version!r}",
            )
            # Open + close a page to exercise the full surface, not
            # just the launch.
            ctx = browser.new_context()
            page = ctx.new_page()
            page.goto("about:blank")
            ctx.close()
        except Exception as e:
            # Bubble up the EXACT chromium error so the failure message
            # tells operators what to install.
            self.fail(
                f"chromium failed to launch in this environment: "
                f"{type(e).__name__}: {e}\n"
                f"Hint: most commonly missing system libs. Try:\n"
                f"    python -m playwright install-deps chromium\n"
                f"On the prod box, the v118.34.11 deploy.sh handles "
                f"this automatically; this test failing means the deploy "
                f"step also failed."
            )
        finally:
            try:
                if browser is not None:
                    browser.close()
            except Exception:
                pass
            try:
                if pw is not None:
                    pw.stop()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main(verbosity=2)

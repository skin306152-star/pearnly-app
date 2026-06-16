# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch

from starlette.requests import Request

from routes import google_oauth_routes as gor


def _request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/integrations/google/connect",
            "query_string": b"",
            "headers": [(b"authorization", b"Bearer LOGIN")],
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


class _CursorCtx:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


class GoogleConnectLaunchTicketTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_returns_one_time_url_without_login_token(self):
        saved = {}

        def save_state(_cur, **kw):
            saved.update(kw)

        with (
            patch.object(gor, "auth_member", return_value=({"id": "u1"}, "tenant-1")),
            patch.object(gor.google_oauth, "is_configured", return_value=True),
            patch.object(gor.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(gor, "resolve_ws", return_value=42),
            patch.object(gor.google_store, "save_state", side_effect=save_state),
            patch.object(gor.secrets, "token_urlsafe", return_value="LAUNCH"),
        ):
            body = await gor.api_connect_start(_request(), workspace_client_id=42)

        self.assertTrue(body["ok"])
        self.assertEqual(body["data"]["url"], "/api/integrations/google/connect?launch=LAUNCH")
        self.assertNotIn("Bearer", body["data"]["url"])
        self.assertNotIn("LOGIN", body["data"]["url"])
        self.assertEqual(saved["state"], "launch:LAUNCH")
        self.assertEqual(saved["tenant_id"], "tenant-1")
        self.assertEqual(saved["workspace_client_id"], 42)
        self.assertEqual(saved["user_id"], "u1")

    async def test_connect_consumes_launch_and_sets_no_referrer_headers(self):
        consumed = {}
        saved = {}

        def consume_state(_cur, **kw):
            consumed.update(kw)
            return {"tenant_id": "tenant-1", "workspace_client_id": 42, "user_id": "u1"}

        def save_state(_cur, **kw):
            saved.update(kw)

        with (
            patch.object(gor.db, "get_cursor", return_value=_CursorCtx()),
            patch.object(gor.google_store, "consume_state", side_effect=consume_state),
            patch.object(gor.google_store, "save_state", side_effect=save_state),
            patch.object(gor.google_oauth, "is_configured", return_value=True),
            patch.object(
                gor.google_oauth, "build_authorize_url", return_value="https://google.test/auth"
            ),
            patch.object(gor.secrets, "token_urlsafe", return_value="OAUTHSTATE"),
        ):
            resp = await gor.api_connect(_request(), launch="LAUNCH")

        self.assertEqual(consumed["state"], "launch:LAUNCH")
        self.assertEqual(saved["state"], "OAUTHSTATE")
        self.assertEqual(saved["tenant_id"], "tenant-1")
        self.assertEqual(saved["workspace_client_id"], 42)
        self.assertEqual(saved["user_id"], "u1")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["location"], "https://google.test/auth")
        self.assertEqual(resp.headers["cache-control"], "no-store")
        self.assertEqual(resp.headers["referrer-policy"], "no-referrer")


if __name__ == "__main__":
    unittest.main()

import unittest
from urllib.parse import parse_qs, urlparse
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import oauth_line_routes


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self):
        return self._payload


class _LineClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, **kwargs):
        if url.endswith("/token"):
            return _Response(200, {"id_token": "id-token", "access_token": "line-token"})
        if url.endswith("/verify"):
            return _Response(
                200,
                {
                    "sub": "U-cowork",
                    "name": "Pearnly Staff",
                    "picture": "https://example.test/avatar.png",
                    "email": "",
                },
            )
        return _Response(404, {})


_USER = {
    "id": "user-1",
    "username": "staff",
    "tenant_id": "tenant-1",
    "plan": "free",
    "role": "member",
}


class CoworkLineOAuthCleanRoomTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(oauth_line_routes.router)
        self.client = TestClient(app)

        self.legacy_bind = mock.Mock(return_value=True)
        self.find_login_user = mock.Mock(return_value=dict(_USER))

        self._patches = [
            mock.patch.object(oauth_line_routes, "_LINE_LOGIN_CHANNEL_ID", "channel-id"),
            mock.patch.object(oauth_line_routes, "_LINE_LOGIN_CHANNEL_SECRET", "secret"),
            mock.patch.object(oauth_line_routes, "_verify_oauth_state", return_value=True),
            mock.patch.object(oauth_line_routes, "_oauth_state_entry", return_value="main"),
            mock.patch.object(oauth_line_routes, "_login_entrance_allowed", return_value=True),
            mock.patch.object(oauth_line_routes, "create_access_token", return_value="jwt"),
            mock.patch.object(oauth_line_routes, "_login_redirect_path", return_value="/home"),
            mock.patch("httpx.AsyncClient", _LineClient),
            mock.patch.object(oauth_line_routes.db, "find_user_by_line_uid", self.find_login_user),
            mock.patch.object(
                oauth_line_routes.db, "create_or_update_line_binding", self.legacy_bind
            ),
            mock.patch.object(oauth_line_routes.db, "update_last_login", return_value=None),
            mock.patch.object(oauth_line_routes.db, "update_user_avatar", return_value=None),
        ]
        for patcher in self._patches:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self._patches):
            patcher.stop()

    def test_normal_line_login_never_writes_legacy_binding(self):
        response = self.client.get(
            "/api/auth/line/callback?code=code&state=login-state",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("mrpilot_token", response.text)
        self.legacy_bind.assert_not_called()

    def test_cowork_login_never_accepts_a_binding_token_or_prompts_for_bot(self):
        response = self.client.get(
            "/api/auth/line/start?entry=cowork&connect_token=clc_once",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlparse(response.headers["location"]).query)
        self.assertNotEqual(query["state"], ["cowork_line:clc_once"])
        self.assertNotIn("bot_prompt", query)
        self.assertEqual(self.client.get("/api/me/connect-line/start").status_code, 404)


if __name__ == "__main__":
    unittest.main()

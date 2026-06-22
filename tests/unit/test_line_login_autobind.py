# -*- coding: utf-8 -*-
"""LINE 登录回调 → 自动绑定 Bot(登录频道 2010411313 与 Bot 同 Provider:sub == Bot userId)。

best-effort:绑定失败不拦登录。测 happy path(用 sub 建绑定)+ 绑定异常仍发 JWT。
"""

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import oauth_line_routes


class _Resp:
    def __init__(self, status, data):
        self.status_code = status
        self._d = data
        self.text = ""

    def json(self):
        return self._d


class _FakeAsyncClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, **k):
        if url.endswith("/token"):
            return _Resp(200, {"id_token": "idtok"})
        if url.endswith("/verify"):
            return _Resp(200, {"sub": "Uabc123", "name": "Skin", "picture": "", "email": ""})
        return _Resp(404, {})


_USER = {"id": "u1", "username": "skin", "tenant_id": "t1", "plan": "free"}


class LineLoginAutoBindTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(oauth_line_routes.router)
        self.client = TestClient(app)
        self._patches = [
            mock.patch.object(oauth_line_routes, "_verify_oauth_state", lambda s: True),
            mock.patch.object(oauth_line_routes, "_LINE_LOGIN_CHANNEL_ID", "cid"),
            mock.patch.object(oauth_line_routes, "_LINE_LOGIN_CHANNEL_SECRET", "sec"),
            mock.patch.object(oauth_line_routes, "create_access_token", lambda **k: "jwt"),
            mock.patch.object(oauth_line_routes, "_login_redirect_path", lambda u: "/home"),
            mock.patch("httpx.AsyncClient", _FakeAsyncClient),
            mock.patch.object(
                oauth_line_routes.db, "find_user_by_line_uid", lambda uid: dict(_USER)
            ),
            mock.patch.object(oauth_line_routes.db, "update_last_login", lambda *a: None),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def test_login_auto_binds_bot_with_sub(self):
        bind = mock.Mock(return_value=True)
        with mock.patch.object(oauth_line_routes.db, "create_or_update_line_binding", bind):
            r = self.client.get("/api/auth/line/callback?code=c&state=s", follow_redirects=False)
        self.assertEqual(r.status_code, 200)
        bind.assert_called_once()
        kw = bind.call_args.kwargs
        self.assertEqual(kw["user_id"], "u1")
        self.assertEqual(kw["line_user_id"], "Uabc123")  # 用登录 sub 当 Bot userId

    def test_bind_failure_does_not_block_login(self):
        bind = mock.Mock(side_effect=RuntimeError("db down"))
        with mock.patch.object(oauth_line_routes.db, "create_or_update_line_binding", bind):
            r = self.client.get("/api/auth/line/callback?code=c&state=s", follow_redirects=False)
        self.assertEqual(r.status_code, 200)  # 仍发 JWT 登录成功
        self.assertIn("mrpilot_token", r.text)


class ConnectLineTests(unittest.TestCase):
    """已登录用户「用 LINE 连接」:state 签 user_id → 补绑当前账号(不建新号)。"""

    def setUp(self):
        app = FastAPI()
        app.include_router(oauth_line_routes.router)
        self.client = TestClient(app)
        self._patches = [
            mock.patch.object(oauth_line_routes, "_LINE_LOGIN_CHANNEL_ID", "cid"),
            mock.patch.object(oauth_line_routes, "_LINE_LOGIN_CHANNEL_SECRET", "sec"),
            mock.patch("httpx.AsyncClient", _FakeAsyncClient),
            mock.patch.object(
                oauth_line_routes.db, "find_user_by_id", lambda uid: dict(_USER, id=uid)
            ),
            mock.patch.object(oauth_line_routes.db, "link_line_uid_to_user", lambda *a: None),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def test_state_roundtrip(self):
        s = oauth_line_routes._gen_connect_state("u9")
        self.assertEqual(oauth_line_routes._parse_connect_state(s), "u9")
        self.assertIsNone(oauth_line_routes._parse_connect_state("x.y.z"))

    def test_connect_binds_current_user_not_login(self):
        bind = mock.Mock(return_value=True)
        state = oauth_line_routes._gen_connect_state("u9")
        with mock.patch.object(oauth_line_routes.db, "create_or_update_line_binding", bind):
            r = self.client.get(
                f"/api/auth/line/callback?code=c&state={state}", follow_redirects=False
            )
        self.assertEqual(r.status_code, 302)
        self.assertIn("line_connect=ok", r.headers["location"])
        kw = bind.call_args.kwargs
        self.assertEqual(kw["user_id"], "u9")  # 绑到 state 里的当前用户
        self.assertEqual(kw["line_user_id"], "Uabc123")

    def test_connect_conflict_redirects_honestly(self):
        state = oauth_line_routes._gen_connect_state("u9")
        with mock.patch.object(
            oauth_line_routes.db, "create_or_update_line_binding", lambda **k: False
        ):
            r = self.client.get(
                f"/api/auth/line/callback?code=c&state={state}", follow_redirects=False
            )
        self.assertIn("line_connect=conflict", r.headers["location"])


if __name__ == "__main__":
    unittest.main()

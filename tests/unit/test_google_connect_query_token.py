# -*- coding: utf-8 -*-
"""connect 的 ?t= query token 网关(整页导航带不上 Authorization 头时用)。

只锁注入逻辑:?t= 注入后既有鉴权链能从 request.headers 读到同一个 Bearer;
权限码不放宽(仍走 auth_member),真 OAuth 跳转是用户验收范围。
"""

import unittest

from starlette.requests import Request

from routes import google_oauth_routes as gor


def _make_request(headers=None):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/integrations/google/connect",
            "query_string": b"",
            "headers": headers or [],
        }
    )


class InjectBearerTests(unittest.TestCase):
    def test_sets_authorization_when_absent(self):
        req = _make_request()
        gor._inject_bearer_from_query(req, "TOK123")
        self.assertEqual(req.headers["authorization"], "Bearer TOK123")

    def test_replaces_existing_authorization(self):
        req = _make_request(headers=[(b"authorization", b"Bearer OLD")])
        gor._inject_bearer_from_query(req, "NEW")
        self.assertEqual(req.headers["authorization"], "Bearer NEW")

    def test_preserves_other_headers(self):
        req = _make_request(headers=[(b"x-keep", b"1")])
        gor._inject_bearer_from_query(req, "TOK")
        self.assertEqual(req.headers["x-keep"], "1")
        self.assertEqual(req.headers["authorization"], "Bearer TOK")


if __name__ == "__main__":
    unittest.main()

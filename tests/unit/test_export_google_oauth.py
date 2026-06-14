# -*- coding: utf-8 -*-
"""Google OAuth 流(export.google_oauth)· mock requests(阶段二)。

锁:授权 URL 含 offline/state/scope · code 换 token 结构 · refresh · 过期判定。真授权(浏览器
跳转 + 写真 Drive)是用户验收范围,本测只锁 HTTP 拼装/解析逻辑。
"""

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from services.export import google_oauth as go


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


class AuthorizeUrlTests(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("GOOGLE_EXPORT_CLIENT_ID")
        os.environ["GOOGLE_EXPORT_CLIENT_ID"] = "cid-123"

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("GOOGLE_EXPORT_CLIENT_ID", None)
        else:
            os.environ["GOOGLE_EXPORT_CLIENT_ID"] = self._saved

    def test_url_has_offline_state_scope(self):
        url = go.build_authorize_url(state="st-1", redirect="https://app/cb")
        self.assertIn("client_id=cid-123", url)
        self.assertIn("access_type=offline", url)
        self.assertIn("state=st-1", url)
        self.assertIn("drive.file", url)
        self.assertIn("spreadsheets", url)


class ExchangeRefreshTests(unittest.TestCase):
    def test_exchange_code_parses_tokens_and_email(self):
        with (
            mock.patch.object(
                go.requests,
                "post",
                return_value=_Resp(
                    {
                        "access_token": "AT",
                        "refresh_token": "RT",
                        "expires_in": 3600,
                        "scope": "drive",
                    }
                ),
            ),
            mock.patch.object(go, "fetch_email", return_value="a@b.com"),
        ):
            out = go.exchange_code(code="c", redirect="https://app/cb")
        self.assertEqual(out["access_token"], "AT")
        self.assertEqual(out["refresh_token"], "RT")
        self.assertEqual(out["email"], "a@b.com")
        self.assertGreater(out["expires_at"], datetime.now(timezone.utc))

    def test_refresh_access_token(self):
        with mock.patch.object(
            go.requests, "post", return_value=_Resp({"access_token": "AT2", "expires_in": 3600})
        ):
            out = go.refresh_access_token(refresh_token="RT")
        self.assertEqual(out["access_token"], "AT2")
        self.assertGreater(out["expires_at"], datetime.now(timezone.utc))


class ExpiryTests(unittest.TestCase):
    def test_no_expiry_is_expired(self):
        self.assertTrue(go._is_expired(None))

    def test_future_not_expired(self):
        self.assertFalse(go._is_expired(datetime.now(timezone.utc) + timedelta(hours=1)))

    def test_past_is_expired(self):
        self.assertTrue(go._is_expired(datetime.now(timezone.utc) - timedelta(minutes=1)))

    def test_iso_string_parsed(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        self.assertFalse(go._is_expired(future))


class ValidAccessTokenTests(unittest.TestCase):
    def test_returns_none_without_credential(self):
        with mock.patch.object(go.google_store, "get_credential", return_value=None):
            self.assertIsNone(go.valid_access_token(None, tenant_id="t1", workspace_client_id=11))

    def test_returns_cached_when_not_expired(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        with mock.patch.object(
            go.google_store,
            "get_credential",
            return_value={"access_token": "AT", "refresh_token": "RT", "expires_at": future},
        ):
            tok = go.valid_access_token(None, tenant_id="t1", workspace_client_id=11)
        self.assertEqual(tok, "AT")

    def test_refreshes_when_expired(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        with (
            mock.patch.object(
                go.google_store,
                "get_credential",
                return_value={"access_token": "old", "refresh_token": "RT", "expires_at": past},
            ),
            mock.patch.object(
                go,
                "refresh_access_token",
                return_value={"access_token": "new", "expires_at": past},
            ),
            mock.patch.object(go.google_store, "update_access_token", return_value=True) as upd,
        ):
            tok = go.valid_access_token(None, tenant_id="t1", workspace_client_id=11)
        self.assertEqual(tok, "new")
        upd.assert_called_once()


if __name__ == "__main__":
    unittest.main()

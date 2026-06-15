# -*- coding: utf-8 -*-
"""LINE LIFF 鉴权端点(routes.line_liff_routes)· mock LINE verify + db(阶段三)。

锁:id_token 验签拿 sub · 未绑定拒 403 · 绑定 → 签 Pearnly token。真 LINE verify + LIFF
webview = 用户验收(需真 channel)。
"""

import asyncio
import os
import unittest
from unittest import mock

from routes import line_liff_routes as liff
from core.pos_api import PosError


class _Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._p = payload

    def json(self):
        return self._p


class VerifyIdTokenTests(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("LINE_LOGIN_CHANNEL_ID")
        os.environ["LINE_LOGIN_CHANNEL_ID"] = "ch-1"

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("LINE_LOGIN_CHANNEL_ID", None)
        else:
            os.environ["LINE_LOGIN_CHANNEL_ID"] = self._saved

    def test_verify_ok(self):
        with mock.patch.object(liff.requests, "post", return_value=_Resp(200, {"sub": "U123"})):
            self.assertEqual(liff._verify_id_token("tok")["sub"], "U123")

    def test_verify_non200_none(self):
        with mock.patch.object(liff.requests, "post", return_value=_Resp(400, {})):
            self.assertIsNone(liff._verify_id_token("tok"))

    def test_verify_no_channel_none(self):
        os.environ.pop("LINE_LOGIN_CHANNEL_ID", None)
        self.assertIsNone(liff._verify_id_token("tok"))


class LiffAuthRouteTests(unittest.TestCase):
    def test_unverified_raises_401(self):
        with mock.patch.object(liff, "_verify_id_token", return_value=None):
            with self.assertRaises(PosError) as ctx:
                asyncio.run(liff.api_liff_auth(liff.LiffAuthIn(id_token="bad")))
        self.assertEqual(ctx.exception.http_status, 401)

    def test_unbound_raises_403(self):
        with (
            mock.patch.object(liff, "_verify_id_token", return_value={"sub": "U1"}),
            mock.patch.object(liff.db, "get_user_by_line_user_id", return_value=None),
        ):
            with self.assertRaises(PosError) as ctx:
                asyncio.run(liff.api_liff_auth(liff.LiffAuthIn(id_token="ok")))
        self.assertEqual(ctx.exception.http_status, 403)

    def test_bound_issues_token(self):
        user = {"id": "u1", "username": "bob", "plan": "free", "tenant_id": "t1", "role": "owner"}
        with (
            mock.patch.object(liff, "_verify_id_token", return_value={"sub": "U1"}),
            mock.patch.object(liff.db, "get_user_by_line_user_id", return_value=user),
            mock.patch.object(liff, "create_access_token", return_value="JWT-XYZ"),
        ):
            res = asyncio.run(liff.api_liff_auth(liff.LiffAuthIn(id_token="ok")))
        self.assertEqual(res["data"]["token"], "JWT-XYZ")


class LiffEntryRedirectTests(unittest.TestCase):
    """LIFF 深链入口跳 /home 带参(PO-4):doc → 复核屏该单;inbox → 待归类该项。"""

    def test_purchase_entry_redirects_with_doc(self):
        res = asyncio.run(liff.liff_purchase_entry("D1", None))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["location"], "/home?liff=purchase&doc=D1")

    def test_inbox_entry_redirects_with_item(self):
        res = asyncio.run(liff.liff_purchase_inbox_entry("IT1", None))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["location"], "/home?liff=purchase&inbox=IT1")


if __name__ == "__main__":
    unittest.main()

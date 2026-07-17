# -*- coding: utf-8 -*-
"""DMS LINE webhook(DL-1 · B2 隔离 / B3 闸关静默 / B4 闸开绑定)。

B2/B3 走 TestClient(最小 app 只挂本 router);B4 直调 async 处理函数(拆分即为单测)。
"""

import base64
import hashlib
import hmac
import os
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import line_dms_webhook_routes as w


def _sign(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(w.router)
    return TestClient(app)


class SignatureIsolationTests(unittest.TestCase):
    def test_default_signed_body_rejected_400(self):
        """B2:用 default channel secret 签的 body → DMS webhook 400(通道隔离)。"""
        body = b'{"events":[]}'
        with mock.patch.dict(
            os.environ,
            {"LINE_CHANNEL_SECRET": "legacy-sec", "LINE_DMS_CHANNEL_SECRET": "dms-sec"},
            clear=False,
        ):
            resp = _client().post(
                "/api/line/dms/webhook",
                content=body,
                headers={"x-line-signature": _sign(body, "legacy-sec")},
            )
        self.assertEqual(resp.status_code, 400)


class GateClosedSilentTests(unittest.TestCase):
    def test_valid_dms_sig_gate_closed_200_zero_reply(self):
        """B3:闸关 + 正确 dms 签名 → 200 且 reply spy 零调用。"""
        body = b'{"events":[{"type":"follow","source":{"userId":"L1"},"replyToken":"rt"}]}'
        with mock.patch.dict(os.environ, {"LINE_DMS_CHANNEL_SECRET": "dms-sec"}, clear=False):
            with (
                mock.patch.object(w.store, "get_binding_by_line_user", return_value=None),
                mock.patch.object(w, "dms_line_enabled_for", return_value=False),
                mock.patch.object(w.line_client, "reply_text") as reply_spy,
                mock.patch.object(w.line_client, "push_text") as push_spy,
            ):
                resp = _client().post(
                    "/api/line/dms/webhook",
                    content=body,
                    headers={"x-line-signature": _sign(body, "dms-sec")},
                )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})
        reply_spy.assert_not_called()
        push_spy.assert_not_called()


class GateOpenBindTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_code_creates_binding_and_replies_ok(self):
        """B4:闸开 + 6 位有效码 → consume + create_or_update_binding(tenant/user 对)+ 成功回执。"""
        with (
            mock.patch.object(w, "dms_line_enabled_for", return_value=True),
            mock.patch.object(
                w.store, "consume_bind_code", return_value={"tenant_id": "t1", "user_id": "u1"}
            ),
            mock.patch.object(
                w.line_client, "get_user_profile", return_value={"displayName": "Som"}
            ),
            mock.patch.object(w.store, "create_or_update_binding", return_value=True) as create,
            mock.patch.object(w.line_client, "reply_text") as reply,
        ):
            await w._handle_dms_text("L1", "rt", "123456")
        create.assert_called_once_with("t1", "u1", "L1", display_name="Som")
        self.assertEqual(reply.call_args.args[1], w._MSG_BIND_OK)
        self.assertEqual(reply.call_args.kwargs.get("channel"), "dms")

    async def test_invalid_code_replies_resend(self):
        """B4:无效/过期码 → 不建绑定 + 重发码提示。"""
        with (
            mock.patch.object(w, "dms_line_enabled_for", return_value=True),
            mock.patch.object(w.store, "consume_bind_code", return_value=None),
            mock.patch.object(w.store, "create_or_update_binding") as create,
            mock.patch.object(w.line_client, "reply_text") as reply,
        ):
            await w._handle_dms_text("L1", "rt", "654321")
        create.assert_not_called()
        self.assertEqual(reply.call_args.args[1], w._MSG_BIND_BAD)

    async def test_unbind_command(self):
        with (
            mock.patch.object(w.store, "unbind_by_line_user", return_value=True) as unbind,
            mock.patch.object(w.line_client, "reply_text") as reply,
        ):
            await w._handle_dms_text("L1", "rt", w._UNBIND_CMD)
        unbind.assert_called_once_with("L1")
        self.assertEqual(reply.call_args.args[1], w._MSG_UNBOUND)

    async def test_follow_welcomes_when_gate_open(self):
        ev = {"type": "follow", "source": {"userId": "L1"}, "replyToken": "rt"}
        with (
            mock.patch.object(w.store, "get_binding_by_line_user", return_value=None),
            mock.patch.object(w, "dms_line_enabled_for", return_value=True),
            mock.patch.object(w.line_client, "reply_text") as reply,
        ):
            await w._handle_dms_event(ev)
        self.assertEqual(reply.call_args.args[1], w._MSG_WELCOME)

    async def test_unfollow_unbinds_silently(self):
        ev = {"type": "unfollow", "source": {"userId": "L1"}}
        with (
            mock.patch.object(w.store, "get_binding_by_line_user", return_value=None),
            mock.patch.object(w, "dms_line_enabled_for", return_value=True),
            mock.patch.object(w.store, "unbind_by_line_user", return_value=True) as unbind,
            mock.patch.object(w.line_client, "reply_text") as reply,
        ):
            await w._handle_dms_event(ev)
        unbind.assert_called_once_with("L1")
        reply.assert_not_called()  # unfollow 无回复


if __name__ == "__main__":
    unittest.main()

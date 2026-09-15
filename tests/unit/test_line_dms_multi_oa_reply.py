# -*- coding: utf-8 -*-
"""DMS outbound channel selection: reply/push must use the OA of the binding in scope."""

from __future__ import annotations

import unittest
from unittest import mock

from services.line_dms import _out, binding_guard

_BINDING = {
    "id": "b1",
    "line_user_id": "L1",
    "tenant_id": "t1",
    "user_id": "u1",
    "channel_key": "dms_b",
}


class ReplyChannelTests(unittest.TestCase):
    def test_no_scope_defaults_to_legacy(self):
        self.assertEqual(binding_guard.current_channel(), "dms")

    def test_scope_channel_is_used(self):
        with binding_guard.scope(_BINDING):
            self.assertEqual(binding_guard.current_channel(), "dms_b")

    def test_unknown_scope_channel_never_sends_through_legacy(self):
        with binding_guard.scope({**_BINDING, "channel_key": "nope"}):
            with self.assertRaises(binding_guard.BindingChanged):
                binding_guard.current_channel()

    def test_reply_uses_binding_channel(self):
        with (
            mock.patch.object(_out, "require_current"),
            mock.patch.object(_out.line_client, "reply_text") as reply,
            binding_guard.scope(_BINDING),
        ):
            _out._reply("tok", "hi")
        reply.assert_called_once_with("tok", "hi", channel="dms_b")

    def test_push_uses_binding_channel(self):
        with (
            mock.patch.object(_out, "require_current"),
            mock.patch.object(_out.line_client, "push_text") as push,
            binding_guard.scope(_BINDING),
        ):
            _out._push("L1", "hi")
        push.assert_called_once_with("L1", "hi", channel="dms_b")

    def test_structured_send_reply_and_push_use_same_channel(self):
        msg = {"type": "text", "text": "x"}
        with (
            mock.patch.object(_out, "require_current"),
            mock.patch.object(_out.line_client, "reply_messages") as reply,
            mock.patch.object(_out.line_client, "push_messages") as push,
            binding_guard.scope(_BINDING),
        ):
            _out._send("L1", msg, reply_token="tok")
            _out._send("L1", msg)
        reply.assert_called_once_with("tok", [msg], channel="dms_b")
        push.assert_called_once_with("L1", [msg], channel="dms_b")


if __name__ == "__main__":
    unittest.main()

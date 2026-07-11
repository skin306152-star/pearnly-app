# -*- coding: utf-8 -*-
"""客户绑定码消费编排(services/line_binding/line_client_bind_intake)· D2-S2 契约。

闸关/非客户码/故障全部 fail-open 回 False(绝不误耗一次性码、绝不挡 webhook 主路);
闸开且码有效才真消费并回执成功文案。
"""

import unittest
from unittest.mock import patch

from services.line_binding import line_client_bind_intake as m


class TryConsumeTests(unittest.TestCase):
    def test_peek_miss_returns_false_without_consuming(self):
        with (
            patch(
                "services.line_binding.line_client_contact.peek_client_bind_code",
                return_value=None,
            ),
            patch("services.line_binding.line_client_contact.consume_client_bind_code") as consume,
        ):
            self.assertFalse(m.try_consume("999999", "U-1", "rt", "th", None))
        consume.assert_not_called()

    def test_gate_closed_returns_false_without_consuming(self):
        with (
            patch(
                "services.line_binding.line_client_contact.peek_client_bind_code",
                return_value={"tenant_id": "t-1", "workspace_client_id": 84},
            ),
            patch(
                "core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=False
            ) as gate,
            patch("services.line_binding.line_client_contact.consume_client_bind_code") as consume,
        ):
            self.assertFalse(m.try_consume("123456", "U-1", "rt", "th", None))
        gate.assert_called_once_with("t-1")
        consume.assert_not_called()  # 闸关 → 绝不误耗一次性码

    def test_consume_race_lost_returns_false(self):
        with (
            patch(
                "services.line_binding.line_client_contact.peek_client_bind_code",
                return_value={"tenant_id": "t-1", "workspace_client_id": 84},
            ),
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_contact.consume_client_bind_code",
                return_value=None,
            ),
        ):
            self.assertFalse(m.try_consume("123456", "U-1", "rt", "th", None))

    def test_bind_contact_failure_returns_false(self):
        with (
            patch(
                "services.line_binding.line_client_contact.peek_client_bind_code",
                return_value={"tenant_id": "t-1", "workspace_client_id": 84},
            ),
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_contact.consume_client_bind_code",
                return_value={"tenant_id": "t-1", "workspace_client_id": 84},
            ),
            patch("services.line_binding.line_client.get_user_profile", return_value={}),
            patch("services.line_binding.line_client_contact.bind_contact", return_value=False),
        ):
            self.assertFalse(m.try_consume("123456", "U-1", "rt", "th", None))

    def test_happy_path_binds_and_replies(self):
        with (
            patch(
                "services.line_binding.line_client_contact.peek_client_bind_code",
                return_value={"tenant_id": "t-1", "workspace_client_id": 84},
            ),
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_contact.consume_client_bind_code",
                return_value={"tenant_id": "t-1", "workspace_client_id": 84},
            ),
            patch(
                "services.line_binding.line_client.get_user_profile",
                return_value={"displayName": "Sister Makeup"},
            ),
            patch("services.line_binding.line_client_contact.bind_contact", return_value=True),
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            out = m.try_consume("123456", "U-163", "rt-1", "th", "qt-1")
        self.assertTrue(out)
        reply.assert_called_once()
        args, kwargs = reply.call_args
        self.assertEqual(args[0], "rt-1")
        self.assertEqual(kwargs["line_user_id"], "U-163")
        self.assertEqual(kwargs["tenant_id"], "t-1")

    def test_any_exception_fails_open(self):
        with patch(
            "services.line_binding.line_client_contact.peek_client_bind_code",
            side_effect=RuntimeError("db down"),
        ):
            self.assertFalse(m.try_consume("123456", "U-1", "rt", "th", None))


if __name__ == "__main__":
    unittest.main()

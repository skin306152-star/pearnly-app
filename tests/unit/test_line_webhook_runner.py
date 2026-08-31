"""DMS/ERP 共用 LINE webhook 失败回执底座。"""

import unittest
from unittest import mock

from services.line_binding import line_webhook_runner as runner


class NoticeDeliveryTests(unittest.TestCase):
    _EVENT = {
        "type": "message",
        "source": {"userId": "U1", "language": "th"},
        "replyToken": "rt",
    }

    def test_reply_first_and_no_push_when_reply_lands(self):
        with (
            mock.patch.object(runner.line_reply, "reply_text_context", return_value=True) as reply,
            mock.patch.object(runner.line_reply, "push_text_context") as push,
        ):
            runner.notify_failed(self._EVENT)
        push.assert_not_called()
        self.assertIn("ส่งใหม่", reply.call_args.args[1])

    def test_push_fallback_when_reply_token_is_unusable(self):
        with (
            mock.patch.object(runner.line_reply, "reply_text_context", return_value=False),
            mock.patch.object(runner.line_reply, "push_text_context") as push,
        ):
            runner.notify_failed(self._EVENT)
        push.assert_called_once()
        self.assertEqual(push.call_args.args[0], "U1")

    def test_unfollow_is_never_answered(self):
        with (
            mock.patch.object(runner.line_reply, "reply_text_context") as reply,
            mock.patch.object(runner.line_reply, "push_text_context") as push,
        ):
            runner.notify_failed({"type": "unfollow", "source": {"userId": "U1"}})
        reply.assert_not_called()
        push.assert_not_called()

    def test_dms_channel_uses_its_own_client(self):
        with (
            mock.patch.object(runner.line_client, "reply_text", return_value=True) as reply,
            mock.patch.object(runner.line_reply, "reply_text_context") as default_reply,
        ):
            runner.notify_failed(self._EVENT, channel="dms", text="ลองใหม่")
        default_reply.assert_not_called()
        self.assertEqual(reply.call_args.kwargs["channel"], "dms")

    def test_copy_follows_event_language(self):
        for lang, needle in (("en", "send it again"), ("zh", "重新发送"), ("ja", "もう一度")):
            event = dict(self._EVENT, source={"userId": "U1", "language": lang})
            with mock.patch.object(
                runner.line_reply, "reply_text_context", return_value=True
            ) as reply:
                runner.notify_failed(event)
            self.assertIn(needle, reply.call_args.args[1])


if __name__ == "__main__":
    unittest.main()

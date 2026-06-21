# -*- coding: utf-8 -*-
"""LINE 端主动解绑:关键词检测(不撞批量撤销)+ 确认/成功卡 + postback 执行。"""

import unittest
from unittest import mock

from services.line_binding import line_postback, line_unbind


class DetectTests(unittest.TestCase):
    def test_positive(self):
        for s in [
            "解绑",
            "我要解绑",
            "取消绑定",
            "unbind please",
            "ยกเลิกการเชื่อมต่อ",
            "連携解除",
        ]:
            self.assertTrue(line_unbind.detect_unbind(s), s)

    def test_negative_not_collide_with_undo_or_record(self):
        # 裸「取消/ยกเลิก」(批量撤销)+ 记账 + 空 → 不触发解绑。
        for s in ["取消三笔", "全部取消", "ยกเลิก", "咖啡 65", "ค่าน้ำ 50", ""]:
            self.assertFalse(line_unbind.detect_unbind(s), s)


class CardTests(unittest.TestCase):
    def test_confirm_card_hero_and_two_postback_buttons(self):
        card = line_unbind.confirm_card("tok")
        bubble = card["contents"]
        self.assertIn("A8a-unbind-confirm-banner", bubble["hero"]["url"])
        btns = bubble["footer"]["contents"]
        actions = [line_postback.parse(b["action"]["data"])["action"] for b in btns]
        self.assertIn(line_postback.ACTION_UNBIND_CONFIRM, actions)
        self.assertIn(line_postback.ACTION_UNBIND_CANCEL, actions)
        # 令牌随卡带上
        self.assertEqual(line_postback.parse(btns[0]["action"]["data"])["token"], "tok")

    def test_success_card_hero_no_footer(self):
        card = line_unbind.success_card()
        bubble = card["contents"]
        self.assertIn("A8b-unbind-success-banner", bubble["hero"]["url"])
        self.assertNotIn("footer", bubble)


class _CM:
    def __enter__(self):
        return mock.Mock()

    def __exit__(self, *a):
        return False


class PostbackTests(unittest.TestCase):
    def setUp(self):
        self.bound = {"id": "u1", "tenant_id": "t1", "line_user_id": "L1"}
        self.unbind = mock.Mock(return_value=True)
        self.reply_msgs = mock.Mock(return_value=True)
        self.reply_text = mock.Mock(return_value=True)
        self._p = [
            mock.patch.object(line_unbind.db, "get_cursor", lambda *a, **k: _CM()),
            mock.patch.object(line_unbind.db, "unbind_line_by_line_user_id", self.unbind),
            mock.patch.object(line_unbind.line_reply, "reply_messages_context", self.reply_msgs),
            mock.patch.object(line_unbind.line_reply, "reply_text_context", self.reply_text),
        ]
        for p in self._p:
            p.start()

    def tearDown(self):
        for p in self._p:
            p.stop()

    def _consume(self, status):
        import services.line_binding.line_action_nonce as nonce

        return mock.patch.object(nonce, "consume", lambda *a, **k: {"status": status})

    def test_confirm_ok_unbinds_and_sends_success(self):
        with self._consume("ok"):
            line_unbind.handle_postback(
                self.bound, "r", line_postback.ACTION_UNBIND_CONFIRM, "tok", "th"
            )
        self.unbind.assert_called_once_with("L1")
        self.reply_msgs.assert_called_once()

    def test_confirm_used_still_idempotent_unbind(self):
        with self._consume("used"):
            line_unbind.handle_postback(
                self.bound, "r", line_postback.ACTION_UNBIND_CONFIRM, "tok", "th"
            )
        self.unbind.assert_called_once()

    def test_confirm_missing_token_does_not_unbind(self):
        with self._consume("missing"):
            line_unbind.handle_postback(
                self.bound, "r", line_postback.ACTION_UNBIND_CONFIRM, "", "th"
            )
        self.unbind.assert_not_called()
        self.reply_text.assert_called_once()

    def test_cancel_does_not_unbind(self):
        with self._consume("ok"):
            line_unbind.handle_postback(
                self.bound, "r", line_postback.ACTION_UNBIND_CANCEL, "tok", "th"
            )
        self.unbind.assert_not_called()
        self.reply_text.assert_called_once()


if __name__ == "__main__":
    unittest.main()

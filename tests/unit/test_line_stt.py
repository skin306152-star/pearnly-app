# -*- coding: utf-8 -*-
"""LINE 语音转写(services/expense/line_stt)守门。

闸关/未绑定 = False(入口落 unsupported 现状逐字节不变);成功路 = 回显在前 + 转写文本
走注入的 text_handler(与打字同路);网关失败/听不清/超长 = 诚实回复绝不静默吞。
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.expense import line_stt


def _outcome(ok=True, data=None):
    o = MagicMock()
    o.ok = ok
    o.data = data
    return o


class TestTryHandleAudio(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = AsyncMock()
        self.msg = {"id": "m1", "duration": 6000, "quoteToken": "qt"}
        patch(
            "core.db.get_user_by_line_user_id", return_value={"id": "u1", "tenant_id": "t1"}
        ).start()
        patch("core.feature_flags.agent_voice_enabled_for", return_value=True).start()
        patch("services.expense.line_lang.card_lang", return_value="th").start()
        self.reply = patch("services.line_binding.line_reply.reply_text_context").start()
        self.push = patch("services.line_binding.line_reply.push_text_context").start()
        patch("services.line_binding.line_reply.begin_loading").start()
        self.download = patch(
            "services.line_binding.line_client.download_message_content", return_value=b"aac"
        ).start()
        self.gw = patch(
            "services.ai_gateway.transport.multimodal_to_json",
            return_value=_outcome(data={"text": "กาแฟ 50"}),
        ).start()
        self.addCleanup(patch.stopall)

    async def _run(self):
        return await line_stt.try_handle_audio(
            self.msg, "U1", "rt", {"ev": 1}, "th", text_handler=self.handler
        )

    async def test_gate_off_returns_false_untouched(self):
        with patch("core.feature_flags.agent_voice_enabled_for", return_value=False):
            self.assertFalse(await self._run())
        self.download.assert_not_called()
        self.handler.assert_not_awaited()

    async def test_unbound_returns_false(self):
        with patch("core.db.get_user_by_line_user_id", return_value=None):
            self.assertFalse(await self._run())

    async def test_success_echoes_then_feeds_text_path(self):
        self.assertTrue(await self._run())
        self.assertIn("กาแฟ 50", self.push.call_args.args[1])  # 回显在前(钱路诚实)
        self.handler.assert_awaited_once()
        self.assertEqual(self.handler.await_args.args[2], "กาแฟ 50")  # 转写=打字同一路
        _, mime = self.gw.call_args.args[1][0]
        self.assertEqual(mime, "audio/aac")

    async def test_gateway_failure_is_honest(self):
        self.gw.return_value = _outcome(ok=False)
        self.assertTrue(await self._run())
        self.assertIn("ฟังไม่ชัด", self.reply.call_args.args[1])
        self.handler.assert_not_awaited()

    async def test_empty_transcript_is_honest(self):
        self.gw.return_value = _outcome(data={"text": "  "})
        self.assertTrue(await self._run())
        self.handler.assert_not_awaited()

    async def test_too_long_rejected_before_download(self):
        self.msg["duration"] = line_stt.MAX_DURATION_MS + 1
        self.assertTrue(await self._run())
        self.download.assert_not_called()
        self.assertIn("ยาวเกินไป", self.reply.call_args.args[1])

    async def test_crash_swallowed_with_honest_reply(self):
        self.download.side_effect = RuntimeError("net down")
        self.assertTrue(await self._run())
        self.handler.assert_not_awaited()
        self.reply.assert_called_once()


if __name__ == "__main__":
    unittest.main()

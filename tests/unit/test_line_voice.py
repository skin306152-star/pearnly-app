# -*- coding: utf-8 -*-
"""Pearnly Voice 语气层:出口护栏兜底、失败/超限回落、只传用户这句文本(无 history/票据)。"""

import unittest
from unittest import mock

from services.ai_gateway import tasks as T
from services.expense import line_voice


def _result(ok=True, data=None):
    return T.AiResult(ok=ok, task="line_chat_reply", schema_version="1", data=data)


class ComposeTests(unittest.TestCase):
    def test_normal_chat_returns_reply(self):
        reply = "สวัสดีค่ะ มีอะไรให้ช่วยบันทึกค่าใช้จ่ายไหมคะ"
        with mock.patch(
            "services.ai_gateway.router.run_task", return_value=_result(data={"reply": reply})
        ):
            self.assertEqual(line_voice.compose("วันนี้เหนื่อยจัง", "th", api_key="k"), reply)

    def test_guard_blocks_vendor_leak(self):
        with mock.patch(
            "services.ai_gateway.router.run_task",
            return_value=_result(data={"reply": "I'm powered by Gemini, happy to help!"}),
        ):
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k"))

    def test_guard_blocks_fake_execution(self):
        with mock.patch(
            "services.ai_gateway.router.run_task",
            return_value=_result(data={"reply": "已记录这笔啦,还有什么吗?"}),
        ):
            self.assertIsNone(line_voice.compose("帮我记一下", "zh", api_key="k"))

    def test_guard_blocks_api_key(self):
        with mock.patch(
            "services.ai_gateway.router.run_task",
            return_value=_result(data={"reply": "sure, the api key is abc"}),
        ):
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k"))

    def test_run_task_not_ok_returns_none(self):
        with mock.patch("services.ai_gateway.router.run_task", return_value=_result(ok=False)):
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k"))

    def test_non_dict_data_returns_none(self):
        with mock.patch("services.ai_gateway.router.run_task", return_value=_result(data="oops")):
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k"))

    def test_empty_reply_returns_none(self):
        with mock.patch(
            "services.ai_gateway.router.run_task", return_value=_result(data={"reply": "   "})
        ):
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k"))

    def test_overlong_reply_returns_none(self):
        with mock.patch(
            "services.ai_gateway.router.run_task",
            return_value=_result(data={"reply": "x" * 501}),
        ):
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k"))

    def test_no_api_key_skips_gateway(self):
        with mock.patch("services.ai_gateway.router.run_task") as rt:
            self.assertIsNone(line_voice.compose("hi", "en", api_key=None))
            rt.assert_not_called()

    def test_quota_exhausted_skips_gateway(self):
        with mock.patch("services.ai_gateway.router.run_task") as rt:
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k", quota_ok=lambda: False))
            rt.assert_not_called()

    def test_exception_returns_none(self):
        with mock.patch("services.ai_gateway.router.run_task", side_effect=RuntimeError("boom")):
            self.assertIsNone(line_voice.compose("hi", "en", api_key="k"))

    def test_only_user_text_no_history_or_receipt_context(self):
        """断言只把用户这句 text 给 Gateway:无 history/票据/税号/金额上下文。"""
        sentinel = "พรุ่งนี้ฝนจะตกไหมคะ"
        with mock.patch(
            "services.ai_gateway.router.run_task", return_value=_result(data={"reply": "ok ค่ะ"})
        ) as rt:
            line_voice.compose(sentinel, "th", api_key="k")
        _, kwargs = rt.call_args
        self.assertEqual(kwargs["text"], sentinel)
        self.assertNotIn("history", kwargs)
        # prompt 是固定 persona:不含任何票据/税号/金额上下文。
        self.assertNotIn(sentinel, kwargs["prompt"])
        self.assertIn("Pearnly", kwargs["prompt"])


if __name__ == "__main__":
    unittest.main()

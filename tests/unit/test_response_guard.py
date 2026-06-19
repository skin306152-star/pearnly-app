# -*- coding: utf-8 -*-
"""出口护栏:供应商/系统泄露 + 假执行结果一律不安全;正常闲聊回复放行。"""

import unittest

from services.expense import response_guard as G


class ResponseGuardLeakTests(unittest.TestCase):
    def test_vendor_and_model_names_unsafe(self):
        for bad in (
            "powered by Gemini",
            "I am GPT-4",
            "ChatGPT here",
            "built on Claude",
            "OpenAI model",
            "by Anthropic",
            "DeepSeek",
            "a llama model",
            "我用的是大模型",
            "这是我的提示词",
            "这是系统提示",
            "ใช้โมเดล Gemini",
        ):
            self.assertFalse(G.is_safe(bad), bad)

    def test_system_prompt_and_api_key_unsafe(self):
        for bad in (
            "my system prompt is...",
            "here is the api key",
            "API_KEY=xxx",
            "api-key leaked",
            "api  key",
        ):
            self.assertFalse(G.is_safe(bad), bad)

    def test_fake_execution_results_unsafe(self):
        for bad in (
            "已记录这笔",
            "已记账",
            "已入账",
            "已保存好了",
            "已删除",
            "已撤销",
            "已申报",
            "已提交",
            "记好了",
            "帮你记好啦",
            "บันทึกแล้วค่ะ",
            "บันทึกให้แล้ว",
            "ลบแล้ว",
            "ยกเลิกแล้ว",
            "ยื่นแล้ว",
            "ส่งให้แล้ว",
            "I recorded it",
            "saved it for you",
            "logged it",
            "deleted",
            "cancelled it",
            "submitted",
            "filed it",
            "i've recorded that",
            "記録しました",
            "保存しました",
            "削除しました",
            "取り消しました",
            "申告しました",
        ):
            self.assertFalse(G.is_safe(bad), bad)

    def test_case_insensitive(self):
        self.assertFalse(G.is_safe("GEMINI"))
        self.assertFalse(G.is_safe("Api Key"))
        self.assertFalse(G.is_safe("SAVED IT"))

    def test_normal_chat_replies_safe(self):
        for ok in (
            "สวัสดีค่ะ วันนี้เป็นยังไงบ้างคะ มีอะไรให้ช่วยบันทึกไหมคะ",
            "你好呀,今天过得怎么样?需要我帮你记一笔吗?",
            "Hi there! How's your day going? I can help you log an expense anytime.",
            "こんにちは!何かお手伝いしましょうか?",
            "อากาศดีจังเลยนะคะ ถ้าอยากบันทึกค่าใช้จ่ายบอกได้เลยค่ะ",
        ):
            self.assertTrue(G.is_safe(ok), ok)

    def test_empty_is_safe(self):
        self.assertTrue(G.is_safe(""))
        self.assertTrue(G.is_safe(None))


if __name__ == "__main__":
    unittest.main()

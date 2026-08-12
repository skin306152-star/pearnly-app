# -*- coding: utf-8 -*-
"""http_common(OpenAI 兼容 provider 公共件)契约:状态码分类 + 多模态 parts + 单源守门。

单源断言锁住下沉本身:openai/selfhost/qwen 必须共用同一函数对象,谁再复制一份本地副本
就红。anthropic 有意不入列(529→timeout 是它的专属差异),此处不设断言。
"""

import json
import unittest

from services.ai_gateway.providers import http_common, openai, qwen, selfhost


class ErrorKindForStatusTests(unittest.TestCase):
    def test_status_classification_table(self):
        for status, kind in (
            (401, "auth"),
            (403, "auth"),
            (429, "quota"),
            (500, "timeout"),
            (502, "timeout"),
            (503, "timeout"),
            (504, "timeout"),
            (400, "provider"),
            (418, "provider"),
        ):
            with self.subTest(status=status):
                self.assertEqual(http_common.error_kind_for_status(status), kind)


class ImageContentPartsTests(unittest.TestCase):
    def test_prompt_first_then_data_uri_per_image(self):
        parts = http_common.image_content_parts("read it", [(b"\x89PNG", "image/png")])
        self.assertEqual(parts[0], {"type": "text", "text": "read it"})
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/png;base64,"))


class SingleSourceTests(unittest.TestCase):
    def test_image_parts_shared_by_all_openai_compatible_providers(self):
        for provider in (openai, selfhost, qwen):
            with self.subTest(provider=provider.NAME):
                self.assertIs(provider.image_content_parts, http_common.image_content_parts)

    def test_http_plumbing_shared_by_selfhost_and_qwen(self):
        # 两家走同一条 POST + 取文本用量的水管(状态码分类在 post_json 内部),不许各写一份
        for provider in (selfhost, qwen):
            with self.subTest(provider=provider.NAME):
                self.assertIs(provider.post_json, http_common.post_json)
                self.assertIs(provider.chat_text_and_usage, http_common.chat_text_and_usage)

    def test_openai_shares_status_classification(self):
        self.assertIs(openai.error_kind_for_status, http_common.error_kind_for_status)


class ChatJsonOutcomeTests(unittest.TestCase):
    """chat_json_outcome 重试→ProviderOutcome 循环三路:传输错 / 解析重读 / 用尽落 parse。"""

    def test_transport_kind_returns_failure_without_retry(self):
        calls = []

        def do_call():
            calls.append(1)
            return "", "timeout", (0, 0)

        out = http_common.chat_json_outcome(do_call, json.loads, "m", 3)
        self.assertFalse(out.ok)
        self.assertEqual(out.error_kind, "timeout")
        self.assertEqual(out.model, "m")
        self.assertIsNone(out.data)
        self.assertEqual(len(calls), 1)

    def test_parse_failure_then_success_retries(self):
        calls = []

        def do_call():
            calls.append(1)
            if len(calls) == 1:
                return "not json", None, (1, 2)
            return '{"ok": true}', None, (3, 4)

        out = http_common.chat_json_outcome(do_call, json.loads, "m", 2)
        self.assertTrue(out.ok)
        self.assertEqual(out.data, {"ok": True})
        self.assertEqual(out.input_tokens, 3)
        self.assertEqual(out.output_tokens, 4)
        self.assertEqual(len(calls), 2)

    def test_all_parse_failures_return_parse_with_last_raw(self):
        calls = []

        def do_call():
            calls.append(1)
            return '{"broken', None, (5, 6)

        out = http_common.chat_json_outcome(do_call, json.loads, "m", 2)
        self.assertFalse(out.ok)
        self.assertEqual(out.error_kind, "parse")
        self.assertEqual(out.raw, '{"broken')
        self.assertEqual(out.input_tokens, 0)
        self.assertEqual(out.output_tokens, 0)
        self.assertEqual(len(calls), 3)  # max_retries + 1


class BearerHeadersTests(unittest.TestCase):
    def test_key_adds_authorization(self):
        h = http_common.bearer_headers("sk-123")
        self.assertEqual(h, {"Content-Type": "application/json", "Authorization": "Bearer sk-123"})

    def test_no_key_omits_authorization(self):
        for key in (None, ""):
            with self.subTest(key=key):
                self.assertEqual(
                    http_common.bearer_headers(key), {"Content-Type": "application/json"}
                )


if __name__ == "__main__":
    unittest.main()

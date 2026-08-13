# -*- coding: utf-8 -*-
"""http_common(OpenAI 兼容 provider 公共件)契约:状态码分类 + 多模态 parts + 单源守门。

单源断言锁住下沉本身:openai/selfhost/qwen 必须共用同一函数对象,谁再复制一份本地副本
就红。anthropic 有意不入列(529→timeout 是它的专属差异),此处不设断言。
"""

import base64
import json
import unittest
from unittest import mock

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


def _make_pdf(pages: int) -> bytes:
    import fitz

    doc = fitz.open()
    for i in range(pages):
        doc.new_page(width=200, height=100).insert_text((10, 50), f"page {i + 1}")
    data = doc.tobytes()
    doc.close()
    return data


class ImageContentPartsTests(unittest.TestCase):
    def test_prompt_first_then_data_uri_per_image(self):
        parts = http_common.image_content_parts("read it", [(b"\x89PNG", "image/png")])
        self.assertEqual(parts[0], {"type": "text", "text": "read it"})
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_pdf_part_expands_to_one_png_per_page(self):
        # OpenAI 兼容 image_url 不吃 PDF(DashScope 400「The image format is illegal」,
        # 2026-08-12 生产 vat_report 15/15 批全灭)——PDF 必须在组请求这层逐页转图。
        parts = http_common.image_content_parts("read it", [(_make_pdf(2), "application/pdf")])
        self.assertEqual(len(parts), 3)  # text + 2 页
        for part in parts[1:]:
            url = part["image_url"]["url"]
            self.assertTrue(url.startswith("data:image/png;base64,"))
            raw = base64.b64decode(url.split(",", 1)[1])
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")

    def test_pdf_pages_capped_per_request(self):
        with mock.patch.object(http_common, "_PDF_MAX_PAGES", 1):
            parts = http_common.image_content_parts("p", [(_make_pdf(3), "application/pdf")])
        self.assertEqual(len(parts), 2)  # text + 只留第 1 页

    def test_unreadable_pdf_falls_through_unchanged(self):
        # 渲染不了 → 按原 mime 发出:服务端照旧拒收,错误路径与修前一致,不新造失败形态
        parts = http_common.image_content_parts("p", [(b"not a pdf", "application/pdf")])
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:application/pdf;base64,"))

    def test_mixed_image_and_pdf_keep_order(self):
        parts = http_common.image_content_parts(
            "p", [(b"\xff\xd8jpg", "image/jpeg"), (_make_pdf(1), "application/pdf")]
        )
        self.assertEqual(len(parts), 3)
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertTrue(parts[2]["image_url"]["url"].startswith("data:image/png;base64,"))


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

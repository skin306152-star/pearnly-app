# -*- coding: utf-8 -*-
"""http_common(OpenAI 兼容 provider 公共件)契约:状态码分类 + 多模态 parts + 单源守门。

单源断言锁住下沉本身:openai/selfhost 必须共用同一函数对象,谁再复制一份本地副本
就红。anthropic 有意不入列(529→timeout 是它的专属差异),此处不设断言。
"""

import unittest

from services.ai_gateway.providers import http_common, openai, selfhost


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
    def test_openai_and_selfhost_share_the_same_functions(self):
        self.assertIs(openai.error_kind_for_status, http_common.error_kind_for_status)
        self.assertIs(selfhost.error_kind_for_status, http_common.error_kind_for_status)
        self.assertIs(openai.image_content_parts, http_common.image_content_parts)
        self.assertIs(selfhost.image_content_parts, http_common.image_content_parts)


if __name__ == "__main__":
    unittest.main()

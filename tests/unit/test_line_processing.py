# -*- coding: utf-8 -*-
"""LINE「识别中」短句(docs/smart-intake/15 §2 · 短句 + 原生转圈,不留大卡)。"""

import unittest

from services.line_binding import line_processing


class ProcessingTextTests(unittest.TestCase):
    def test_four_langs(self):
        for lang in ("zh", "th", "en", "ja"):
            t = line_processing.processing_text(lang)
            self.assertTrue(t)
            self.assertIn("🐱", t)

    def test_unknown_lang_falls_to_zh(self):
        self.assertIn("正在", line_processing.processing_text("xx"))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""LINE「识别中」处理卡(docs/smart-intake/15 §2)。"""

import unittest

from services.line_binding import line_processing


class ProcessingCardTests(unittest.TestCase):
    def test_four_langs_render(self):
        for lang in ("zh", "th", "en", "ja"):
            c = line_processing.processing_card(lang)
            self.assertEqual(c["type"], "flex")
            flat = str(c)
            self.assertIn("kb-cat", flat)  # 猫咪图
            self.assertIn("image", flat)

    def test_unknown_lang_falls_to_zh(self):
        c = line_processing.processing_card("xx")
        self.assertIn("正在帮你看票", str(c))


if __name__ == "__main__":
    unittest.main()

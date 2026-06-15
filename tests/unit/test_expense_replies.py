# -*- coding: utf-8 -*-
"""智能回复:greeting/thanks 识别 + 轮选不复读(docs/smart-intake/15 §5)。"""

import unittest

from services.expense import replies


class DetectTests(unittest.TestCase):
    def test_greeting(self):
        for t in ("你好", "สวัสดีครับ", "hello", "こんにちは"):
            self.assertEqual(replies.detect_smalltalk(t), "greeting")

    def test_thanks(self):
        for t in ("谢谢你", "ขอบคุณมาก", "thanks!", "ありがとう"):
            self.assertEqual(replies.detect_smalltalk(t), "thanks")

    def test_neither(self):
        self.assertIsNone(replies.detect_smalltalk("ค่าน้ำ 50"))
        self.assertIsNone(replies.detect_smalltalk(""))


class PickTests(unittest.TestCase):
    def test_varies_by_text(self):
        # 不同输入 → 至少出现两种不同回复(不复读)。
        outs = {replies.pick("scope", t, "zh") for t in ("你好", "你在干嘛", "在不在", "随便")}
        self.assertGreater(len(outs), 1)

    def test_deterministic_same_text(self):
        self.assertEqual(replies.pick("greeting", "hi", "en"), replies.pick("greeting", "hi", "en"))

    def test_four_langs(self):
        for lang in ("zh", "th", "en", "ja"):
            self.assertTrue(replies.pick("greeting", "hi", lang))
            self.assertTrue(replies.pick("thanks", "thx", lang))
            self.assertTrue(replies.pick("scope", "x", lang))
            self.assertTrue(replies.pick("support", "x", lang))

    def test_unknown_kind_falls_to_scope(self):
        self.assertIn(replies.pick("bogus", "x", "zh"), replies._POOLS["scope"]["zh"])


if __name__ == "__main__":
    unittest.main()

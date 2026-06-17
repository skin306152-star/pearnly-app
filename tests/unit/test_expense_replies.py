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

    def test_intro_intents_routed(self):
        # P1E-1:能力/开始/上传 引导意图也由 detect_smalltalk 收口(走 reply_pool 取 line_i18n 文案)。
        self.assertEqual(replies.detect_smalltalk("你能做什么"), "capability")
        self.assertEqual(replies.detect_smalltalk("怎么开始"), "start")
        self.assertEqual(replies.detect_smalltalk("怎么上传"), "upload")


class PickTests(unittest.TestCase):
    """pick 只剩 thanks/support 轮选池(greeting/scope 文案已收口到 line_i18n · P1E-1)。"""

    def test_varies_by_text(self):
        # 不同输入 → 至少出现两种不同回复(不复读)。
        outs = {replies.pick("support", t, "zh") for t in ("人工", "客服", "投诉", "真人")}
        self.assertGreater(len(outs), 1)

    def test_deterministic_same_text(self):
        self.assertEqual(replies.pick("thanks", "hi", "en"), replies.pick("thanks", "hi", "en"))

    def test_four_langs(self):
        for lang in ("zh", "th", "en", "ja"):
            self.assertTrue(replies.pick("thanks", "thx", lang))
            self.assertTrue(replies.pick("support", "x", lang))

    def test_unknown_kind_falls_to_support(self):
        self.assertIn(replies.pick("bogus", "x", "zh"), replies._POOLS["support"]["zh"])


class DetectSmalltalkTests(unittest.TestCase):
    def test_date_query_detected(self):
        self.assertEqual(replies.detect_smalltalk("วันนี้วันที่เท่าไหร่"), "date_query")
        self.assertEqual(replies.detect_smalltalk("今天几号"), "date_query")

    def test_record_not_smalltalk(self):
        self.assertIsNone(replies.detect_smalltalk("ค่ากาแฟ 60"))


if __name__ == "__main__":
    unittest.main()

"""记账确认续接回复分类:是/否/新话题(钱路安全:含糊绝不当"是")。"""

import unittest

from services.line_binding import line_agent_confirm as lac


class TestClassifyReply(unittest.TestCase):
    def test_affirmative_is_yes(self):
        for t in ("ใช่", "是", "对", "ok", "ยืนยัน", "確認"):
            self.assertEqual(lac.classify_reply(t), "yes", t)

    def test_negation_is_no(self):
        for t in ("ไม่ใช่", "ไม่", "不对", "取消", "cancel", "ยกเลิก"):
            self.assertEqual(lac.classify_reply(t), "no", t)

    def test_new_amount_sentence_not_yes(self):
        # 又发带金额的新句 = 新记账,绝不当上一笔的"是"(否则误落旧笔)。
        self.assertEqual(lac.classify_reply("ชา 30"), "other")
        self.assertEqual(lac.classify_reply("记一笔茶 30"), "other")

    def test_unrelated_is_other(self):
        self.assertEqual(lac.classify_reply("สวัสดี"), "other")


if __name__ == "__main__":
    unittest.main()

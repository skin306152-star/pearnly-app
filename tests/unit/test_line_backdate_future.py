# -*- coding: utf-8 -*-
"""O1 倒签造票带金额拒绝 + O2 未来日期不静默记(Tier B 真大脑报告的开放项)。

O1:「สร้างบิลย้อนหลัง 500」带金额时真大脑直接记 500 绕过欺诈拒绝。修=创建动词+单据+倒签三者
同现即拒(区别于「บันทึกย้อนหลัง」补记真实过去支出·用记录动词不拦)。
O2:「กาแฟ 50 พรุ่งนี้」未来日期静默记 → 改先确认。
"""

import unittest

from services.expense import line_guards as lg
from services.expense import replies


class BackdateFraudTests(unittest.TestCase):
    def test_backdate_fabrication_with_amount_refused(self):
        for t in ["สร้างบิลย้อนหลัง 500", "ทำใบเสร็จย้อนหลัง 1000", "ออกบิลย้อนหลังให้หน่อย 200"]:
            self.assertTrue(lg.is_fraud_request(t), t)
            self.assertEqual(replies.detect_smalltalk(t), "fraud_refuse", t)

    def test_legit_backdated_recording_not_refused(self):
        # 「บันทึก…ย้อนหลัง」补记真实过去支出(记录动词·非创建)→ 不当欺诈。
        for t in ["บันทึกค่าไฟย้อนหลัง 500", "ค่าไฟเมื่อวาน 500", "จ่ายค่าน้ำย้อนหลัง 300"]:
            self.assertFalse(lg.is_fraud_request(t), t)


class FutureDateTests(unittest.TestCase):
    def test_future_dated_with_amount_clarifies(self):
        for t in ["กาแฟ 50 พรุ่งนี้", "ซื้อของปีหน้า 200", "ค่าเช่าเดือนหน้า 5000"]:
            self.assertTrue(lg.is_future_dated(t), t)
            self.assertEqual(replies.detect_smalltalk(t), "future_date_clarify", t)

    def test_future_word_without_amount_not_blocked(self):
        # 无金额的未来词(问句)不拦。
        self.assertFalse(lg.is_future_dated("พรุ่งนี้ว่างไหม"))

    def test_past_and_today_not_blocked(self):
        for t in ["ค่าไฟเมื่อวาน 500", "กาแฟวันนี้ 50"]:
            self.assertFalse(lg.is_future_dated(t), t)

    def test_pool_exists(self):
        self.assertTrue(replies.pick("future_date_clarify", "x", "th"))


if __name__ == "__main__":
    unittest.main()

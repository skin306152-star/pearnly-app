# -*- coding: utf-8 -*-
"""LINE 文本分类(line_classify):费用类型 + 付款方式 关键词归类(确定性·无信号不猜)。"""

import unittest

from services.expense import line_classify as lc


class ExpenseTypeTests(unittest.TestCase):
    def test_service_vs_goods(self):
        self.assertEqual(lc.classify_expense_type("ค่าซ่อม"), "service")
        self.assertEqual(lc.classify_expense_type("水费"), "service")
        self.assertEqual(lc.classify_expense_type("โค้ก"), "goods")
        self.assertEqual(lc.classify_expense_type(""), "goods")


class PaymentMethodTests(unittest.TestCase):
    def test_transfer(self):
        self.assertEqual(lc.detect_payment_method("ค่าของ 100 โอนเงิน"), "transfer")
        self.assertEqual(lc.detect_payment_method("买菜40 转账"), "transfer")

    def test_cash_card_promptpay(self):
        self.assertEqual(lc.detect_payment_method("กาแฟ 60 เงินสด"), "cash")
        self.assertEqual(lc.detect_payment_method("付了500 刷卡"), "card")
        self.assertEqual(lc.detect_payment_method("จ่ายผ่านพร้อมเพย์"), "promptpay")

    def test_no_signal_empty(self):
        self.assertEqual(lc.detect_payment_method("ค่าน้ำ 50"), "")


class IntroIntentTests(unittest.TestCase):
    """P1E-1:能力/开始/上传 引导意图(记账短语不误判)。"""

    def test_capability_start_upload(self):
        self.assertEqual(lc.intro_intent("你能做什么"), "capability")
        self.assertEqual(lc.intro_intent("help"), "capability")
        self.assertEqual(lc.intro_intent("ทำอะไรได้บ้าง"), "capability")
        self.assertEqual(lc.intro_intent("怎么开始"), "start")
        self.assertEqual(lc.intro_intent("เริ่มยังไง"), "start")
        self.assertEqual(lc.intro_intent("怎么上传"), "upload")
        self.assertEqual(lc.intro_intent("อัปโหลด"), "upload")

    def test_capability_synonyms_unified(self):
        # 验收:同义能力问句都收敛到 capability(不再绕过 P1E-1 文案 → 旧 demo)。
        for p in (
            "คุณทำอะไรได้บ้าง",
            "คุณสามารถทำอะไรให้ฉันได้บ้าง",
            "ช่วยบันทึกค่าใช้จ่ายได้ไหม",
            "What can you do?",
            "你能做什么",
            "能帮我做什么",
        ):
            self.assertEqual(lc.intro_intent(p), "capability", p)

    def test_record_not_misread(self):
        for t in ("ค่าน้ำ 50", "买2杯咖啡120", "打车 120", "เมื่อวานกาแฟ 60"):
            self.assertEqual(lc.intro_intent(t), "")


class DateQueryTests(unittest.TestCase):
    def test_date_questions(self):
        for t in ("วันนี้วันที่เท่าไหร่", "今天几号", "what's the date today", "今日は何日"):
            self.assertTrue(lc.is_date_query(t), t)

    def test_not_date(self):
        for t in ("ค่าน้ำ 50", "买咖啡 60", "สวัสดี"):
            self.assertFalse(lc.is_date_query(t), t)

    def test_time_questions(self):
        for t in ("现在几点了", "几点", "ตอนนี้กี่โมง", "what time is it now", "今何時"):
            self.assertTrue(lc.is_time_query(t), t)

    def test_time_not_confused_with_date_or_expense(self):
        for t in ("今天几号", "ค่าน้ำ 50", "买咖啡 60"):
            self.assertFalse(lc.is_time_query(t), t)


class CorrectionFeedbackTests(unittest.TestCase):
    def test_feedback_phrases(self):
        for t in ("这个你识别错了", "金额错了", "อ่านผิด", "ไม่ถูก", "this is wrong", "incorrect"):
            self.assertTrue(lc.is_correction_feedback(t), t)

    def test_not_feedback(self):
        for t in ("买咖啡 60", "金额改成 70", "สวัสดี"):
            self.assertFalse(lc.is_correction_feedback(t), t)


class TextLangTests(unittest.TestCase):
    def test_script_detection(self):
        self.assertEqual(lc.detect_text_lang("这个识别错了"), "zh")
        self.assertEqual(lc.detect_text_lang("อ่านผิด"), "th")
        self.assertEqual(lc.detect_text_lang("this is wrong"), "en")
        self.assertEqual(lc.detect_text_lang("間違ってる"), "ja")
        self.assertEqual(lc.detect_text_lang("123"), "")


class PaymentNormalizeTests(unittest.TestCase):
    def test_ocr_payment_values(self):
        self.assertEqual(lc.normalize_payment_method("QRPayment(API)"), "promptpay")
        self.assertEqual(lc.normalize_payment_method("พร้อมเพย์"), "promptpay")
        self.assertEqual(lc.normalize_payment_method("เงินสด"), "cash")
        self.assertEqual(lc.normalize_payment_method("card"), "card")
        self.assertEqual(lc.normalize_payment_method("โอนเงิน"), "transfer")
        self.assertEqual(lc.normalize_payment_method("xyz"), "")
        self.assertEqual(lc.normalize_payment_method(""), "")

    def test_payment_from_ocr_keeps_raw_when_unknown(self):
        # 卡片/落库同口径:认得出 → 规范码;认不出 → 留原文;空 → ''。
        self.assertEqual(lc.payment_from_ocr("QRPayment(API)"), "promptpay")
        self.assertEqual(lc.payment_from_ocr("เก็บปลายทาง"), "เก็บปลายทาง")
        self.assertEqual(lc.payment_from_ocr(None), "")


class CorrectionFieldTests(unittest.TestCase):
    """改错点名字段(P1E-2):amount/date/seller/category/payment/items。"""

    def test_each_field(self):
        self.assertEqual(lc.detect_correction_field("金额不对"), "amount")
        self.assertEqual(lc.detect_correction_field("ยอดเงินผิด"), "amount")
        self.assertEqual(lc.detect_correction_field("日期错了"), "date")
        self.assertEqual(lc.detect_correction_field("卖家不是这个"), "seller")
        self.assertEqual(lc.detect_correction_field("ร้านค้าไม่ถูก"), "seller")
        self.assertEqual(lc.detect_correction_field("分类改一下"), "category")
        self.assertEqual(lc.detect_correction_field("付款方式不对"), "payment")
        self.assertEqual(lc.detect_correction_field("明细错了"), "items")
        self.assertEqual(lc.detect_correction_field("รายการย่อยไม่ครบ"), "items")

    def test_no_field(self):
        self.assertEqual(lc.detect_correction_field("这个识别错了"), "")
        self.assertEqual(lc.detect_correction_field(""), "")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""输入契约:松散字段 → SalesDoc。行金额口径、日期口径、取值口径都在这一层定死。

单独成文件而不是跟配方测试挤在一起:这一层不产工作簿,喂的是上游 OCR 真会给的字段形状,
断言的是「读出来的数和日期对不对」。工作簿那一层验的是「表里算出来的数对不对」。
"""

import unittest
from decimal import Decimal

from services.ledger import fields as fld
from services.ledger.doc_date import (
    DATE_FROM_PRINTED,
    DATE_FROM_TIME_OUT,
    REASON_CROSS_MONTH,
    REASON_NO_DATE,
)
from services.ledger.models import parse_sales_doc
from tests.unit._ledger_golden import GOLDEN_SESSION_RAW

D = Decimal


class LineAmountTests(unittest.TestCase):
    """行金额的口径:票面有就用票面的,没有才按数量×单价派生。"""

    @staticmethod
    def _line(item):
        return parse_sales_doc({"invoice_number": "X1", "items": [item]}).lines[0]

    def test_printed_amount_wins_over_qty_times_price(self):
        """票面单价是四舍五入过的:3 × 33.33 = 99.99,而票面行金额印的是 100.00。"""
        line = self._line({"name": "a", "qty": "3", "price": "33.33", "subtotal": "100.00"})
        self.assertEqual(line.amount, D("100.00"))
        self.assertEqual(line.unit_price, D("33.33"))

    def test_derived_amount_rounds_half_up_like_excel(self):
        """派生时必须 HALF_UP —— 与 split_gross 和表里的 ROUND 同口径。Python 默认的
        HALF_EVEN 在 0.125 这类分位上给 0.12,同一张票于是有两个数。"""
        self.assertEqual(self._line({"name": "a", "qty": "1", "price": "0.125"}).amount, D("0.13"))
        self.assertEqual(self._line({"name": "b", "qty": "1", "price": "0.135"}).amount, D("0.14"))


class DocDateRuleTests(unittest.TestCase):
    """日期口径只认上游真会给的字段:date / date_raw / notes。"""

    @staticmethod
    def _date(**fields):
        return parse_sales_doc({"invoice_number": "X1", "items": [{"subtotal": "10"}], **fields})

    def test_session_times_read_from_printed_text(self):
        doc = self._date(date="27/05/2569", date_raw=GOLDEN_SESSION_RAW)
        self.assertEqual(doc.doc_date.isoformat(), "2026-05-28")
        self.assertEqual(doc.date_source, DATE_FROM_TIME_OUT)

    def test_session_times_read_from_notes(self):
        doc = self._date(notes="เวลาเข้า 27/05/2569 18:12 เวลาออก 28/05/2569 01:05")
        self.assertEqual(doc.doc_date.isoformat(), "2026-05-28")

    def test_time_in_without_its_own_date_does_not_steal_the_out_date(self):
        """「Time In 18:12 Time Out 28/05/2569」—— in 那截没有日期,不许把 out 的读过去。"""
        doc = self._date(date_raw="Time In 18:12 Time Out 28/05/2569 01:05")
        self.assertEqual(doc.doc_date.isoformat(), "2026-05-28")
        self.assertNotEqual(doc.pending_reason, REASON_CROSS_MONTH, "in 那截没日期,不该判跨月")

    def test_plain_invoice_keeps_printed_date(self):
        doc = self._date(date="28/05/2569", date_raw="28/05/2569", notes="ขอบคุณค่ะ")
        self.assertEqual(doc.doc_date.isoformat(), "2026-05-28")
        self.assertEqual(doc.date_source, DATE_FROM_PRINTED)

    def test_hotel_check_in_out_is_not_a_session(self):
        """酒店票印的是入住/退房,它自己另有开票日期 —— 拿退房日盖过开票日就是改法定日期。"""
        doc = self._date(date="28/05/2569", notes="Check-in 27/05/2569 Check-out 30/06/2569")
        self.assertEqual(doc.doc_date.isoformat(), "2026-05-28")
        self.assertEqual(doc.date_source, DATE_FROM_PRINTED)

    def test_no_date_anywhere_goes_pending(self):
        self.assertEqual(self._date(notes="ขอบคุณ").pending_reason, REASON_NO_DATE)


class FieldPickTests(unittest.TestCase):
    """松散字段取值:上游把空值 JSON 化成 "None"/"null" 时不能当有值。"""

    def test_nullish_strings_are_empty(self):
        for raw in (None, "", "  ", "None", "null", "NaN"):
            self.assertEqual(fld.text(raw), "", repr(raw))

    def test_pick_follows_key_order(self):
        self.assertEqual(fld.pick({"b": "2", "a": "1"}, "a", "b"), "1")
        self.assertEqual(fld.pick({"b": "2"}, "a", "b"), "2")
        self.assertIsNone(fld.pick({"a": ""}, "a"))


if __name__ == "__main__":
    unittest.main()

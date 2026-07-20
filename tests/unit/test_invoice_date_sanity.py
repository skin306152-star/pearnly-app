# -*- coding: utf-8 -*-
"""票面日期合理性闸(两条识别链共用)。

2026-07-20 事故的兜底:佛历 2569 被读成 2559 → 归一出 2016-05-31 → 全链零告警
推进 Express(连税期都落到 2559-05)。年份读错一位必然落在"十年前",此闸抓的就是它。
软闸不阻断:回落 Vision 路救不了日期(那条路读日期更差),交人判是补录旧账还是读错年。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.ocr import direct_read as dr
from services.ocr.date_sanity import validate_invoice_date
from services.ocr.schemas import ThaiInvoice

_TODAY = date(2026, 7, 20)


def _inv(date_value, **kw):
    return ThaiInvoice(
        invoice_number=kw.pop("invoice_number", "IV69/00475"),
        date=date_value,
        total_amount=kw.pop("total_amount", "70.00"),
        subtotal=kw.pop("subtotal", "65.42"),
        vat=kw.pop("vat", "4.58"),
        seller_tax=kw.pop("seller_tax", "0107561000013"),
        **kw,
    )


class _Provider:
    def __init__(self, data):
        self._data = data

    def multimodal_to_json(self, prompt, images, **kw):
        return ProviderOutcome(ok=True, data=self._data, model="fake")


def _read_page_with(invoice: ThaiInvoice):
    """跑真实 read_page,验日期闸对 band/needs_manual_review 的实际影响。"""
    data = invoice.model_dump(mode="json")
    with mock.patch("services.ai_gateway.backends.get_provider", return_value=_Provider(data)):
        return dr.read_page(b"\xff\xd8x", page_number=1, document_type="invoice")


class ValidateInvoiceDateTests(unittest.TestCase):
    def test_flags_year_misread_ten_years_early(self):
        # 事故原值:票面 31/5/2569,Vision 读成 2559 → 归一 2016-05-31
        warns = validate_invoice_date(_inv("2016-05-31"), today=_TODAY)
        self.assertEqual(len(warns), 1)
        self.assertIn("2016-05-31", warns[0])

    def test_accepts_current_date(self):
        self.assertEqual(validate_invoice_date(_inv("2026-05-31"), today=_TODAY), [])

    def test_accepts_backdated_within_retention_window(self):
        # 代账补录旧账是常态,5 年内不报(泰国凭证保存期)
        self.assertEqual(validate_invoice_date(_inv("2022-01-15"), today=_TODAY), [])

    def test_flags_future_date(self):
        warns = validate_invoice_date(_inv("2027-01-01"), today=_TODAY)
        self.assertEqual(len(warns), 1)
        self.assertIn("future", warns[0])

    def test_tolerates_one_day_ahead_for_timezone_skew(self):
        self.assertEqual(validate_invoice_date(_inv("2026-07-21"), today=_TODAY), [])

    def test_silent_on_missing_or_unparsable_date(self):
        for v in ("", None, "31/5/2569", "not-a-date", "2026-13-45"):
            self.assertEqual(validate_invoice_date(_inv(v), today=_TODAY), [], v)


class DirectReadWiringTests(unittest.TestCase):
    """判据只有一份实现 —— 两条链手抄两套是漂移的老病根。"""

    def test_date_gate_does_not_trigger_fallback(self):
        # 不回落:Vision 路读日期更差,回落是净亏
        dr._invoice_hard_gates(_inv("2016-05-31"), page_number=1)

    def test_stale_date_forces_manual_review(self):
        """降 0.05 置信压不到 needs_review —— 必须强制人工,否则照样自动推。"""
        page = _read_page_with(_inv("2016-05-31"))
        self.assertEqual(page.confidence_band, "needs_review")
        self.assertTrue(page.needs_manual_review)
        self.assertTrue(any("2016-05-31" in w for w in page.validation_warnings))

    def test_current_date_stays_auto(self):
        page = _read_page_with(_inv(date.today().isoformat()))
        self.assertNotEqual(page.confidence_band, "needs_review")
        self.assertFalse(page.needs_manual_review)


if __name__ == "__main__":
    unittest.main(verbosity=2)

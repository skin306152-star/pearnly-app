# -*- coding: utf-8 -*-
"""image-first 两阶段编排(services/ocr/image_first)· 灰度开关 + 升级臂(阶段二)。

注入假 refine / field_conf_fn,纯逻辑测两条路:主抽够好(单调)、主抽低置信(升级)。
不连 Gemini。锁:开关默认关、关键字段缺/低置信触发升级、升级把主抽结果当 hint、token 累加。
"""

import os
import unittest
from types import SimpleNamespace

from services.ocr import image_first as imf


def _inv(invoice_number="INV123456", total_amount="1070.00"):
    return SimpleNamespace(invoice_number=invoice_number, total_amount=total_amount)


def _page_result(invoice, in_tok=10, out_tok=20, ms=100):
    return SimpleNamespace(
        invoice=invoice, input_tokens=in_tok, output_tokens=out_tok, elapsed_ms=ms
    )


class _Refiner:
    """假 refine_page:按 model_name 返回预置结果,记录每次调用。"""

    def __init__(self, by_model):
        self.by_model = by_model
        self.calls = []

    def __call__(self, *, model_name, layer2_invoice, **kw):
        self.calls.append({"model": model_name, "hint": layer2_invoice})
        return self.by_model[model_name]


class IsEnabledTests(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("OCR_IMAGE_FIRST")
        os.environ.pop("OCR_IMAGE_FIRST", None)

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("OCR_IMAGE_FIRST", None)
        else:
            os.environ["OCR_IMAGE_FIRST"] = self._saved

    def test_default_off(self):
        self.assertFalse(imf.is_enabled())

    def test_on_values(self):
        for v in ("1", "true", "YES", "on"):
            os.environ["OCR_IMAGE_FIRST"] = v
            self.assertTrue(imf.is_enabled(), v)

    def test_off_values(self):
        for v in ("0", "false", "", "no"):
            os.environ["OCR_IMAGE_FIRST"] = v
            self.assertFalse(imf.is_enabled(), v)


class NeedsEscalationTests(unittest.TestCase):
    def test_missing_key_field_escalates(self):
        self.assertTrue(imf.needs_escalation({}, _inv(invoice_number="")))

    def test_low_confidence_escalates(self):
        self.assertTrue(imf.needs_escalation({"invoice_number": 0.60}, _inv()))

    def test_all_good_no_escalation(self):
        fc = {"invoice_number": 0.97, "total_amount": 0.99}
        self.assertFalse(imf.needs_escalation(fc, _inv()))

    def test_no_word_conf_signal_does_not_escalate_on_that_field(self):
        # 字段在但无词级置信(None)→ 不因该字段升级(只缺/低才升)。
        self.assertFalse(imf.needs_escalation({"total_amount": 0.99}, _inv()))


class RunTests(unittest.TestCase):
    def _fc_high(self, l1_page, invoice):
        return {"invoice_number": 0.97, "total_amount": 0.98}

    def _fc_low(self, l1_page, invoice):
        return {"invoice_number": 0.55, "total_amount": 0.98}

    def test_primary_good_no_escalation(self):
        refine = _Refiner({"g2.5": _page_result(_inv(), 10, 20, 100)})
        out = imf.run(
            image_bytes=b"x",
            l1_page=object(),
            l2_invoice=_inv(),
            trigger_reasons=[],
            api_key="k",
            document_type="auto",
            refine=refine,
            field_conf_fn=self._fc_high,
            primary_model="g2.5",
            escalate_model="g3.5",
        )
        self.assertEqual(len(refine.calls), 1)
        self.assertEqual(out["layers"], ["IF:g2.5"])
        self.assertFalse(out["escalated"])
        self.assertEqual((out["in_tokens"], out["out_tokens"], out["ms"]), (10, 20, 100))

    def test_low_confidence_escalates_and_sums_tokens(self):
        prim = _inv(invoice_number="HZ01")  # 主抽糊了发票号
        better = _inv(invoice_number="NZ01000017838")
        refine = _Refiner(
            {"g2.5": _page_result(prim, 10, 20, 100), "g3.5": _page_result(better, 30, 40, 200)}
        )
        out = imf.run(
            image_bytes=b"x",
            l1_page=object(),
            l2_invoice=_inv(),
            trigger_reasons=[],
            api_key="k",
            document_type="auto",
            refine=refine,
            field_conf_fn=self._fc_low,
            primary_model="g2.5",
            escalate_model="g3.5",
        )
        self.assertEqual(len(refine.calls), 2)
        self.assertEqual(out["layers"], ["IF:g2.5", "ESC:g3.5"])
        self.assertTrue(out["escalated"])
        self.assertIs(out["invoice"], better)
        # 升级把主抽结果当 hint 喂更强模型
        self.assertIs(refine.calls[1]["hint"], prim)
        # token/ms 两段累加
        self.assertEqual((out["in_tokens"], out["out_tokens"], out["ms"]), (40, 60, 300))

    def test_same_primary_and_escalate_model_no_double_call(self):
        refine = _Refiner({"g3.5": _page_result(_inv(invoice_number=""), 10, 20, 100)})
        out = imf.run(
            image_bytes=b"x",
            l1_page=object(),
            l2_invoice=_inv(),
            trigger_reasons=[],
            api_key="k",
            document_type="auto",
            refine=refine,
            field_conf_fn=self._fc_low,
            primary_model="g3.5",
            escalate_model="g3.5",
        )
        self.assertEqual(len(refine.calls), 1)
        self.assertFalse(out["escalated"])


if __name__ == "__main__":
    unittest.main()

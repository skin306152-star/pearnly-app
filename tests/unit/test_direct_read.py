# -*- coding: utf-8 -*-
"""image-direct 直读守门:路由分流、钱面硬闸回落、软标注、税号校验和、pipeline 接线。

S2 分流(2026-07-05 Vision 消融定案)的行为契约:
  短文档直读跳 Vision;长表/多页对账件留 Vision 路;直读不可信整件回落且 engine 打标;
  OCR_IMAGE_DIRECT=0 秒级回退全 Vision 链。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.ocr import direct_read as dr
from services.ocr import pipeline
from services.ocr.schemas import PipelinePageResult, ThaiInvoice

# 真值票(tests/eval/ground_truth_local/invoices/amazon_70.json·票面亲核):
# 勾稽自洽 65.42+4.58=70.00,税号过 mod-11。
_GOOD_INVOICE = {
    "document_type": "simplified_tax_invoice",
    "is_not_invoice": False,
    "invoice_number": "INV-001",
    "seller_name": "Cafe Amazon",
    "seller_tax": "0107561000013",
    "subtotal": "65.42",
    "vat": "4.58",
    "total_amount": "70.00",
}


class _FakeProvider:
    def __init__(self, outcome):
        self._o = outcome
        self.calls = []

    def multimodal_to_json(self, prompt, images, **kw):
        self.calls.append({"prompt": prompt, "images": images, **kw})
        return self._o


def _patch_provider(outcome):
    return mock.patch(
        "services.ai_gateway.backends.get_provider", return_value=_FakeProvider(outcome)
    )


class RouteDirectTests(unittest.TestCase):
    def test_short_docs_go_direct(self):
        self.assertTrue(dr.route_direct(1, "auto"))
        self.assertTrue(dr.route_direct(3, "invoice"))
        self.assertTrue(dr.route_direct(1, "bank_statement"))  # 单页拍照对账单=短表
        self.assertTrue(dr.route_direct(1, "vat_report"))

    def test_long_and_multipage_recon_stay_on_vision(self):
        self.assertFalse(dr.route_direct(4, "invoice"))  # 长文档
        self.assertFalse(dr.route_direct(2, "bank_statement"))  # 多页对账件门槛更严
        self.assertFalse(dr.route_direct(2, "general_ledger"))
        self.assertFalse(dr.route_direct(29, "bank_statement"))  # TTB 真件案例

    def test_kill_switch(self):
        with mock.patch.dict("os.environ", {"OCR_IMAGE_DIRECT": "0"}):
            self.assertFalse(dr.enabled())
        with mock.patch.dict("os.environ", {"OCR_IMAGE_DIRECT": ""}):
            self.assertTrue(dr.enabled())  # 默认开


class ReadPageTests(unittest.TestCase):
    def test_clean_invoice_yields_confirm_band(self):
        outcome = ProviderOutcome(
            ok=True,
            data=dict(_GOOD_INVOICE),
            model="gemini-3.1-flash-lite",
            input_tokens=900,
            output_tokens=200,
        )
        with _patch_provider(outcome):
            pr = dr.read_page(b"\xff\xd8fakejpeg", page_number=1)
        self.assertEqual(pr.layer_chain, ["ID"])
        self.assertEqual(pr.invoice.total_amount, "70.00")
        self.assertEqual(pr.layer2_model, "gemini-3.1-flash-lite")
        self.assertEqual(pr.confidence_band, "yellow_confirm")  # 永不 auto·confirm-first 不变
        self.assertFalse(pr.needs_manual_review)
        self.assertEqual(pr.validation_warnings, [])

    def test_money_mismatch_falls_back(self):
        bad = {**_GOOD_INVOICE, "total_amount": "170.00"}  # 65.42+4.58 ≠ 170
        with _patch_provider(ProviderOutcome(ok=True, data=bad, model="m")):
            with self.assertRaises(dr.DirectReadFallback):
                dr.read_page(b"\xff\xd8x", page_number=1)

    def test_missing_total_falls_back(self):
        bad = {**_GOOD_INVOICE, "total_amount": ""}
        with _patch_provider(ProviderOutcome(ok=True, data=bad, model="m")):
            with self.assertRaises(dr.DirectReadFallback):
                dr.read_page(b"\xff\xd8x", page_number=1)

    def test_provider_failure_falls_back(self):
        with _patch_provider(ProviderOutcome(ok=False, error_kind="parse")):
            with self.assertRaises(dr.DirectReadFallback):
                dr.read_page(b"\xff\xd8x", page_number=1)

    def test_tax_checksum_failure_falls_back_via_sanity(self):
        # P6:税号读错一位(mod-11 不过)由现有 sanity 硬闸接住 → 回落 Vision 路对质
        bad = {**_GOOD_INVOICE, "seller_tax": "0107561000014"}
        with _patch_provider(ProviderOutcome(ok=True, data=bad, model="m")):
            with self.assertRaises(dr.DirectReadFallback):
                dr.read_page(b"\xff\xd8x", page_number=1)

    def test_missing_invoice_number_soft_flag_not_fallback(self):
        # 实测 B 读单号比 Vision 路准 → 缺单号只降置信标注,不回落
        soft = {**_GOOD_INVOICE, "invoice_number": ""}
        with _patch_provider(ProviderOutcome(ok=True, data=soft, model="m")):
            pr = dr.read_page(b"\xff\xd8x", page_number=1)
        self.assertEqual(len(pr.validation_warnings), 1)
        self.assertEqual(pr.confidence_band, "yellow_confirm")  # 0.90 恰在 confirm 档
        self.assertFalse(pr.needs_manual_review)

    def test_not_invoice_passes_through(self):
        # 猫的照片:直读判非票直接返回,不回落(Vision 路也救不出发票)
        with _patch_provider(
            ProviderOutcome(ok=True, data={"is_not_invoice": True}, model="m")
        ):
            pr = dr.read_page(b"\x89PNG\r\n\x1a\nx", page_number=1)
        self.assertTrue(pr.invoice.is_not_invoice)

    def test_bank_document_parsed(self):
        doc = {"document_type": "bank_statement", "entries": []}
        with _patch_provider(ProviderOutcome(ok=True, data=doc, model="m")):
            pr = dr.read_page(b"\xff\xd8x", page_number=1, document_type="bank_statement")
        self.assertIsNotNone(pr.document)
        self.assertEqual(pr.layer_chain, ["ID"])


class PipelineWiringTests(unittest.TestCase):
    def _fake_page(self):
        return PipelinePageResult(
            page_number=1, invoice=ThaiInvoice(**_GOOD_INVOICE), layer_chain=["ID"]
        )

    def test_image_goes_direct_with_engine_tag(self):
        with mock.patch.object(dr, "read_page", return_value=self._fake_page()) as rp:
            res = pipeline.run_on_image_bytes(b"\xff\xd8x")
        rp.assert_called_once()
        self.assertEqual(res.engine, dr.ENGINE_DIRECT)

    def test_image_fallback_tags_engine(self):
        legacy = self._fake_page()
        with mock.patch.object(dr, "read_page", side_effect=dr.DirectReadFallback("boom")):
            with mock.patch.object(pipeline, "_process_one_page", return_value=legacy):
                res = pipeline.run_on_image_bytes(b"\xff\xd8x")
        self.assertEqual(res.engine, dr.ENGINE_FALLBACK)

    def test_kill_switch_routes_legacy_with_plain_engine(self):
        legacy = self._fake_page()
        with mock.patch.dict("os.environ", {"OCR_IMAGE_DIRECT": "0"}):
            with mock.patch.object(dr, "read_page") as rp:
                with mock.patch.object(pipeline, "_process_one_page", return_value=legacy):
                    res = pipeline.run_on_image_bytes(b"\xff\xd8x")
        rp.assert_not_called()
        self.assertEqual(res.engine, "pipeline_v1")

    def test_long_pdf_stays_on_vision_path(self):
        import fitz

        doc = fitz.open()
        for _ in range(4):
            doc.new_page(width=200, height=200)
        pdf_bytes = doc.tobytes()
        doc.close()
        with mock.patch.object(dr, "read_page") as rp:
            with mock.patch.object(
                pipeline, "_process_pages", return_value=[self._fake_page()]
            ) as pp:
                res = pipeline.run_on_pdf_bytes(pdf_bytes, enable_text_path=False)
        rp.assert_not_called()
        pp.assert_called_once()
        self.assertEqual(res.engine, "pipeline_v1")

    def test_short_scan_pdf_goes_direct(self):
        import fitz

        doc = fitz.open()
        doc.new_page(width=200, height=200)
        pdf_bytes = doc.tobytes()
        doc.close()
        with mock.patch.object(dr, "read_page", return_value=self._fake_page()) as rp:
            res = pipeline.run_on_pdf_bytes(pdf_bytes, enable_text_path=False)
        rp.assert_called_once()
        self.assertEqual(res.engine, dr.ENGINE_DIRECT)


if __name__ == "__main__":
    unittest.main(verbosity=2)

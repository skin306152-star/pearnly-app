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
    """单 outcome = 每次调用同稿(双读读到一致);列表 = 按序出稿(造两读分歧)。"""

    def __init__(self, outcome):
        self._seq = list(outcome) if isinstance(outcome, list) else [outcome]
        self.calls = []

    def multimodal_to_json(self, prompt, images, **kw):
        self.calls.append({"prompt": prompt, "images": images, **kw})
        i = min(len(self.calls) - 1, len(self._seq) - 1)
        return self._seq[i]


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

    def test_multi_page_invoice_batch_goes_direct(self):
        """多票打包(一份 PDF 装 N 张独立发票)按票走直读,不按页数当长表拦。

        2026-07-20 事故:8 张冰厂销项票打成一份 PDF,被纯页数闸判成长表推去 Vision 路,
        L1 Vision 把佛历 2569 读成 2559(8/8 全错),而 L2 只吃 L1 文本看不到原图,无从纠正。
        同批图走直读逐页读 8/8 正确。页数不是崩点判据,文档类型才是。
        """
        self.assertTrue(dr.route_direct(4, "invoice"))
        self.assertTrue(dr.route_direct(8, "invoice"))
        self.assertTrue(dr.route_direct(dr.MAX_DIRECT_PAGES, "auto"))

    def test_table_docs_and_oversized_stay_on_vision(self):
        self.assertFalse(dr.route_direct(2, "bank_statement"))  # 多页对账件要跨页续表
        self.assertFalse(dr.route_direct(2, "general_ledger"))
        self.assertFalse(dr.route_direct(29, "bank_statement"))  # TTB 真件案例
        self.assertFalse(dr.route_direct(dr.MAX_DIRECT_PAGES + 1, "invoice"))

    def test_kill_switch(self):
        with mock.patch.dict("os.environ", {"OCR_IMAGE_DIRECT": "0"}):
            self.assertFalse(dr.enabled())
        with mock.patch.dict("os.environ", {"OCR_IMAGE_DIRECT": ""}):
            self.assertTrue(dr.enabled())  # 默认开

    def test_bank_image_uses_compact_prompt_and_larger_output_budget(self):
        provider = _FakeProvider(ProviderOutcome(ok=False, error_kind="parse"))
        with mock.patch("services.ai_gateway.backends.get_provider", return_value=provider):
            dr._call_model(b"\xff\xd8x", "bank_statement", api_key=None)
        call = provider.calls[0]
        self.assertIn("Read EVERY visible transaction row", call["prompt"])
        self.assertIn("description, max 80 characters", call["prompt"])
        self.assertIn("two-digit year 26 mean 2026", call["prompt"])
        self.assertNotIn("deposit_ref", call["prompt"])
        self.assertNotIn('"reference"', call["prompt"])
        self.assertEqual(call["max_tokens"], 16384)

    def test_invoice_keeps_standard_output_budget(self):
        provider = _FakeProvider(ProviderOutcome(ok=False, error_kind="parse"))
        with mock.patch("services.ai_gateway.backends.get_provider", return_value=provider):
            dr._call_model(b"\xff\xd8x", "invoice", api_key=None)
        self.assertNotIn("max_tokens", provider.calls[0])


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
        self.assertEqual(pr.layer_chain, ["ID"])  # 双读默认关(ROI 实验=0 独家保护)·单读
        self.assertEqual(pr.invoice.total_amount, "70.00")
        self.assertEqual(pr.layer2_model, "gemini-3.1-flash-lite")
        self.assertEqual(pr.layer3_input_tokens, 0)  # 单读·无二读 token
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
        with _patch_provider(ProviderOutcome(ok=True, data={"is_not_invoice": True}, model="m")):
            pr = dr.read_page(b"\x89PNG\r\n\x1a\nx", page_number=1)
        self.assertTrue(pr.invoice.is_not_invoice)

    def test_credit_note_negative_kept_and_forced_review(self):
        # P1 台账 #8:贷记单负数不回落(数学对负数成立·sanity 豁免),但强制人工确认方向
        cn = {
            **_GOOD_INVOICE,
            "document_type": "credit_note",
            "subtotal": "-65.42",
            "vat": "-4.58",
            "total_amount": "-70.00",
        }
        with _patch_provider(ProviderOutcome(ok=True, data=cn, model="m")):
            pr = dr.read_page(b"\xff\xd8x", page_number=1)
        self.assertEqual(pr.invoice.total_amount, "-70.00")  # 负号保留
        self.assertTrue(pr.needs_manual_review)
        self.assertEqual(pr.confidence_band, "needs_review")
        self.assertTrue(any("credit_note" in w for w in pr.validation_warnings))

    def test_bank_document_parsed(self):
        doc = {"document_type": "bank_statement", "entries": []}
        with _patch_provider(ProviderOutcome(ok=True, data=doc, model="m")):
            pr = dr.read_page(b"\xff\xd8x", page_number=1, document_type="bank_statement")
        self.assertIsNotNone(pr.document)
        self.assertEqual(pr.layer_chain, ["ID"])  # 非发票不双读(下游对账有自己的勾稽)


@mock.patch.dict("os.environ", {"OCR_DOUBLE_READ": "1"})  # 双读默认关·本类显式启用测机制本身
class DoubleReadTests(unittest.TestCase):
    # 04 号方案 B 档:自洽性幻觉(trap05 5518897)唯一机器解=两次独立读比对钱面四件

    def _outcomes(self, second_data):
        first = ProviderOutcome(ok=True, data=dict(_GOOD_INVOICE), model="lite", input_tokens=9)
        return [first, ProviderOutcome(ok=True, data=second_data, model="m2", input_tokens=9)]

    def test_mismatch_forces_review_with_both_readings(self):
        # 二读总额不同(自洽性幻觉的样子)→ 人工 + 差异原样进警告,不机器仲裁谁对
        second = {**_GOOD_INVOICE, "total_amount": "5518897", "subtotal": "5518890", "vat": "7.00"}
        with _patch_provider(self._outcomes(second)):
            pr = dr.read_page(b"\xff\xd8x", page_number=1)
        self.assertTrue(pr.needs_manual_review)
        self.assertEqual(pr.confidence_band, "needs_review")
        self.assertTrue(any("total_amount" in w and "5518897" in w for w in pr.validation_warnings))

    def test_small_ticket_uses_lite_with_perturbed_image(self):
        fp = _FakeProvider(self._outcomes(dict(_GOOD_INVOICE)))  # total 70 < 2000
        with mock.patch("services.ai_gateway.backends.get_provider", return_value=fp):
            dr.read_page(b"\xff\xd8x", page_number=1)
        self.assertEqual(len(fp.calls), 2)
        self.assertEqual(fp.calls[1]["tier"], "flash_lite")

    def test_big_ticket_escalates_to_fallback_tier(self):
        big = {**_GOOD_INVOICE, "subtotal": "4672.90", "vat": "327.10", "total_amount": "5000.00"}
        fp = _FakeProvider(
            [
                ProviderOutcome(ok=True, data=big, model="lite"),
                ProviderOutcome(ok=True, data=dict(big), model="m35"),
            ]
        )
        with mock.patch("services.ai_gateway.backends.get_provider", return_value=fp):
            pr = dr.read_page(b"\xff\xd8x", page_number=1)
        self.assertEqual(fp.calls[1]["tier"], "fallback")  # ≥฿2000 跨模型二读防共病
        self.assertFalse(pr.needs_manual_review)

    def test_kill_switch_single_read(self):
        fp = _FakeProvider(ProviderOutcome(ok=True, data=dict(_GOOD_INVOICE), model="m"))
        with mock.patch.dict("os.environ", {"OCR_DOUBLE_READ": "0"}):
            with mock.patch("services.ai_gateway.backends.get_provider", return_value=fp):
                pr = dr.read_page(b"\xff\xd8x", page_number=1)
        self.assertEqual(len(fp.calls), 1)
        self.assertEqual(pr.layer_chain, ["ID"])

    def test_second_read_failure_falls_back(self):
        seq = [
            ProviderOutcome(ok=True, data=dict(_GOOD_INVOICE), model="m"),
            ProviderOutcome(ok=False, error_kind="parse"),
        ]
        with _patch_provider(seq):
            with self.assertRaises(dr.DirectReadFallback):
                dr.read_page(b"\xff\xd8x", page_number=1)


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

    @staticmethod
    def _blank_pdf(n_pages: int) -> bytes:
        import fitz

        doc = fitz.open()
        for _ in range(n_pages):
            doc.new_page(width=200, height=200)
        out = doc.tobytes()
        doc.close()
        return out

    def test_oversized_pdf_stays_on_vision_path(self):
        pdf_bytes = self._blank_pdf(4)
        with mock.patch.object(dr, "MAX_DIRECT_PAGES", 3):
            with mock.patch.object(dr, "read_page") as rp:
                with mock.patch.object(
                    pipeline, "_process_pages", return_value=[self._fake_page()]
                ) as pp:
                    res = pipeline.run_on_pdf_bytes(pdf_bytes, enable_text_path=False)
        rp.assert_not_called()
        pp.assert_called_once()
        self.assertEqual(res.engine, "pipeline_v1")

    def test_short_scan_pdf_goes_direct(self):
        with mock.patch.object(dr, "read_page", return_value=self._fake_page()) as rp:
            res = pipeline.run_on_pdf_bytes(self._blank_pdf(1), enable_text_path=False)
        rp.assert_called_once()
        self.assertEqual(res.engine, dr.ENGINE_DIRECT)

    def test_multi_page_invoice_pdf_goes_direct(self):
        """多票打包的 PDF 走直读——2026-07-20 佛历误读事故的回归闸。"""
        with mock.patch.object(dr, "read_page", return_value=self._fake_page()) as rp:
            res = pipeline.run_on_pdf_bytes(self._blank_pdf(8), enable_text_path=False)
        self.assertEqual(rp.call_count, 8)
        self.assertEqual(res.engine, dr.ENGINE_DIRECT)


class RunFileConcurrencyTests(unittest.TestCase):
    """多页并发调度:页序必须按 page_number 还原,与串行输出逐项一致。

    串行时 8 页实测 82s(每页 8-13s),用户等不起 —— 放宽多页直读必须同时并发,
    否则把 Vision 路 14s 的体验换成 80s。
    """

    @staticmethod
    def _page(n: int) -> PipelinePageResult:
        return PipelinePageResult(
            page_number=n, invoice=ThaiInvoice(**_GOOD_INVOICE), layer_chain=["ID"]
        )

    def _run(self, n_pages: int, workers: int):
        import time as _t

        def _slow(image_bytes, page_number, document_type, api_key):
            # 后面的页先返回 → 逼出乱序完成,验证还原靠 page_number 不靠完成顺序
            _t.sleep(0.02 * (n_pages - page_number))
            return self._page(page_number)

        with mock.patch.object(dr, "DIRECT_PAGE_WORKERS", workers):
            with mock.patch.object(dr, "read_page", side_effect=_slow):
                return dr.run_file([b"img"] * n_pages, document_type="invoice")

    def test_pages_returned_in_page_order_despite_out_of_order_completion(self):
        res = self._run(6, workers=4)
        self.assertEqual([p.page_number for p in res.pages], [1, 2, 3, 4, 5, 6])
        self.assertEqual(res.page_count, 6)
        self.assertEqual(res.engine, dr.ENGINE_DIRECT)

    def test_concurrent_and_serial_agree(self):
        concurrent = [p.page_number for p in self._run(5, workers=4).pages]
        serial = [p.page_number for p in self._run(5, workers=1).pages]
        self.assertEqual(concurrent, serial)

    def test_single_page_stays_serial(self):
        res = self._run(1, workers=4)
        self.assertEqual([p.page_number for p in res.pages], [1])


if __name__ == "__main__":
    unittest.main(verbosity=2)

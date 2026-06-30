# -*- coding: utf-8 -*-
"""三个直调 OCR 入口的「首读不可用 → 升级 OCR_FALLBACK_MODEL(3.5-flash)」单测。

锁住:便宜首读(flash/flash_lite)结果不可用时,确实再调一次且走 fallback 档(tier="fallback");
首读即可用时不浪费升级。覆盖入口:身份证、VAT 报表 PDF、VAT 批量发票。
共享地基 = services/ocr/gemini_models.try_with_fallback(见 test_gemini_models)。
"""

import os
import unittest
from types import SimpleNamespace
from unittest import mock

from services.ocr import id_card_extract
from services.vat import vat_parser_gemini, vat_ocr_batch

# 清掉 env 覆盖 → 默认档(flash_lite=2.5-flash-lite / flash=2.5-flash / fallback=3.5-flash),
# 使 tier_for_model 映射稳定:首读档→flash/flash_lite,升级档→fallback。
_MODEL_ENV = ("OCR_FLASH_MODEL", "OCR_FLASHLITE_MODEL", "OCR_FALLBACK_MODEL", "OCR_ESCALATE_MODEL")


def _res(ok=True, data=None, error_kind=None):
    return SimpleNamespace(
        ok=ok, data=data, error_kind=error_kind, model="", input_tokens=0, output_tokens=0
    )


class _BaseEscalationTest(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in _MODEL_ENV}
        for k in _MODEL_ENV:
            os.environ.pop(k, None)
        self.tiers = []  # 按调用顺序记录每次 multimodal 的 tier

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _patched(self, results):
        # patch 网关 multimodal:按次序返回脚本结果,同时记录每次 tier(验是否升级到 fallback)。
        return mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            side_effect=lambda *a, **k: (self.tiers.append(k.get("tier")) or results.pop(0)),
        )


class IdCardEscalationTests(_BaseEscalationTest):
    def _run(self, results):
        with self._patched(results):
            return id_card_extract.extract_thai_id_card(b"\xff\xd8\xffXfakejpg", api_key="k")

    def test_first_read_no_id_escalates_to_fallback(self):
        # 首读(flash_lite)读不出 13 位号 → 升级 fallback(3.5)再读,拿到合规号。
        out = self._run([_res(data={"people_id": ""}), _res(data={"people_id": "1101700230705"})])
        self.assertEqual(out["id_card"]["people_id"], "1101700230705")
        self.assertEqual(self.tiers, ["flash_lite", "fallback"])

    def test_first_read_valid_no_escalation(self):
        # 首读即出合规号 → 不升级(只一次调用,省钱)。
        out = self._run([_res(data={"people_id": "1101700230705"})])
        self.assertEqual(out["id_card"]["people_id"], "1101700230705")
        self.assertEqual(self.tiers, ["flash_lite"])


class VatParserEscalationTests(_BaseEscalationTest):
    def _run(self, results):
        with self._patched(results):
            return vat_parser_gemini.parse_with_gemini(b"%PDF-fake", "application/pdf", api_key="k")

    def test_parse_failure_escalates_to_fallback(self):
        # 首读(flash)非 JSON → 升级 fallback(3.5)再读,成功拿到 rows。
        out = self._run([_res(ok=False, error_kind="parse"), _res(data={"rows": []})])
        self.assertTrue(out["ok"])
        self.assertEqual(self.tiers, ["flash", "fallback"])

    def test_first_read_ok_no_escalation(self):
        out = self._run([_res(data={"rows": []})])
        self.assertTrue(out["ok"])
        self.assertEqual(self.tiers, ["flash"])


class VatBatchEscalationTests(_BaseEscalationTest):
    def _run(self, results):
        files = [
            {"filename": "a.jpg", "bytes": b"\xff\xd8\xffA"},
            {"filename": "b.jpg", "bytes": b"\xff\xd8\xffB"},
        ]
        with self._patched(results):
            return vat_ocr_batch.extract_invoice_fields_batch(files, api_key="k")

    def test_empty_invoices_escalates_to_fallback(self):
        # 首读(flash)解析不出任何发票 → 升级 fallback(3.5)再读一批。
        out = self._run(
            [_res(data={"invoices": []}), _res(data={"invoices": [{"index": 1}, {"index": 2}]})]
        )
        self.assertTrue(out[0]["ok"])
        self.assertEqual(self.tiers, ["flash", "fallback"])

    def test_first_batch_ok_no_escalation(self):
        out = self._run([_res(data={"invoices": [{"index": 1}, {"index": 2}]})])
        self.assertTrue(out[0]["ok"])
        self.assertEqual(self.tiers, ["flash"])


if __name__ == "__main__":
    unittest.main()

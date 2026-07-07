# -*- coding: utf-8 -*-
"""services/ocr/totals_rescue.py 单测(L3 全量复读失败后的窄口径金额救援)。

只重抽 4 个金额字段,响应短→出错概率低;贴回后必须勾稽 + VAT-7% 都自洽才采纳,
否则原样交还调用方(page_runner)走 needs_manual_review——救援本身绝不吞掉真错。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.ocr import totals_rescue
from services.ocr.schemas import ThaiInvoice

# NBC 折扣票实案(2026-07-08):sub+vat=total 仍自洽(自洽性幻觉),但 VAT 不再是 7%。
_MISREAD_INVOICE = ThaiInvoice(
    document_type="tax_invoice",
    subtotal="53129.00",
    vat="4060.05",
    total_amount="57189.05",
)


class RescueTotalsTests(unittest.TestCase):
    def test_gateway_success_returns_present_fields_only(self):
        outcome = ProviderOutcome(
            ok=True,
            data={
                "subtotal": "58129.35",
                "vat": "4069.05",
                "discount": None,
                "total_amount": "62198.40",
            },
            model="m",
            input_tokens=10,
            output_tokens=5,
        )
        with mock.patch("services.ocr.model_client.json_from_images", return_value=outcome):
            out = totals_rescue.rescue_totals(b"\xff\xd8x", None, "m")
        # discount=None 被丢弃 — 不该拿一个空字段覆盖 L2 原有的(可能非空)discount
        self.assertEqual(
            out, {"subtotal": "58129.35", "vat": "4069.05", "total_amount": "62198.40"}
        )

    def test_gateway_failure_returns_none(self):
        with mock.patch(
            "services.ocr.model_client.json_from_images",
            return_value=ProviderOutcome(ok=False, error_kind="parse"),
        ):
            self.assertIsNone(totals_rescue.rescue_totals(b"\xff\xd8x", None, "m"))

    def test_gateway_raise_returns_none(self):
        # 救援步骤绝不能把异常抛给调用方 — 否则会拖垮既有 needs_manual_review 兜底。
        with mock.patch(
            "services.ocr.model_client.json_from_images", side_effect=RuntimeError("boom")
        ):
            self.assertIsNone(totals_rescue.rescue_totals(b"\xff\xd8x", None, "m"))

    def test_empty_image_bytes_returns_none(self):
        self.assertIsNone(totals_rescue.rescue_totals(b"", None, "m"))


class ApplyRescueTests(unittest.TestCase):
    def test_no_rescue_data_rejected(self):
        # rescue_totals 拿不到任何字段(None / 空字典)→ 直接判救援失败,不碰 invoice。
        self.assertIsNone(totals_rescue.apply_rescue(_MISREAD_INVOICE, None))
        self.assertIsNone(totals_rescue.apply_rescue(_MISREAD_INVOICE, {}))

    def test_fixed_totals_accepted(self):
        rescued = {"subtotal": "58129.35", "vat": "4069.05", "total_amount": "62198.40"}
        patched = totals_rescue.apply_rescue(_MISREAD_INVOICE, rescued)
        self.assertIsNotNone(patched)
        self.assertEqual(patched.subtotal, "58129.35")
        self.assertEqual(patched.vat, "4069.05")
        self.assertEqual(patched.total_amount, "62198.40")
        # 原对象不可变 — 救援失败时调用方应仍能安全落回 L2 原值
        self.assertEqual(_MISREAD_INVOICE.subtotal, "53129.00")

    def test_still_unbalanced_totals_rejected(self):
        rescued = {"subtotal": "53129.00", "vat": "4060.05", "total_amount": "1.00"}
        self.assertIsNone(totals_rescue.apply_rescue(_MISREAD_INVOICE, rescued))

    def test_self_consistent_but_wrong_ratio_rejected(self):
        # 三者互相对平但 VAT 不是净额 7% → 仍判自洽性幻觉,不采纳(vat_ratio_mismatch 兜底)
        rescued = {"subtotal": "53129.00", "vat": "4060.05", "total_amount": "57189.05"}
        self.assertIsNone(totals_rescue.apply_rescue(_MISREAD_INVOICE, rescued))


if __name__ == "__main__":
    unittest.main()

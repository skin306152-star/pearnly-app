# -*- coding: utf-8 -*-
"""Bug#4 · VAT 税率合理性闸(对抗票 06:10% 内部自洽仍应转人工)。

税基取 total−vat(对折扣稳健)· 隐含税率非 ≈7% → ERR_VAT_RATE_ANOMALY(转人工)。

★形状铁律(2026-07-02 真站点复测教训):真实推送流的 history 经
flatten_history_for_mrerp 产出——顶层只有 total_amount 等 SELECT 列,OCR 的 vat
只在 fields 嵌套里。本文件的 history 必须照抄这个真实形状;此前顶层塞 vat 的
单测形状让闸绿测、线上对所有真实单据空转。
"""

from __future__ import annotations

import unittest

from services.erp import mrerp_xlsx_generator as gen
from services.erp.erp_payload import flatten_history_for_mrerp
from services.erp.mrerp_xlsx_fmt import history_number
from services.erp.mrerp_xlsx_purchase import validate_purchase_history

_CLIENTS = {"clients": [{"erp_type": "mrerp", "client_id": 1, "erp_code": "0006"}]}


def _sales(total, vat, **fields_extra):
    """真实 flatten 形状:total_amount 顶层 · vat 在 fields 嵌套。"""
    fields = {"vat": vat}
    fields.update(fields_extra)
    return {
        "client_id": 1,
        "invoice_number": "IV1",
        "invoice_date": "2026-07-01",
        "total_amount": total,
        "fields": fields,
    }


class VatRateAnomalyHelperTests(unittest.TestCase):
    def test_10pct_is_anomaly(self):  # 对抗票 06
        self.assertTrue(gen.vat_rate_anomaly(_sales("2970.00", "270.00")))

    def test_7pct_is_ok(self):
        self.assertFalse(gen.vat_rate_anomaly(_sales("107.00", "7.00")))

    def test_7pct_with_discount_ok(self):
        # 折扣已含在 total → 税基=total−vat=90 → 6.30/90=7% · 不误杀
        self.assertFalse(gen.vat_rate_anomaly(_sales("96.30", "6.30", subtotal="100.00")))

    def test_zero_vat_skipped(self):
        self.assertFalse(gen.vat_rate_anomaly(_sales("100.00", "0")))

    def test_missing_vat_skipped(self):
        self.assertFalse(gen.vat_rate_anomaly({"total_amount": "100.00", "fields": {}}))

    def test_rounding_noise_on_7pct_ok(self):
        # 小额四舍五入:base=1.50 → 7%=0.105→0.11 → 7.3% · 仍在带内
        self.assertFalse(gen.vat_rate_anomaly(_sales("1.61", "0.11")))

    def test_top_level_vat_still_supported(self):
        # 手工构造/旧调用方把 vat 放顶层也照判(history_number 顶层优先)。
        self.assertTrue(
            gen.vat_rate_anomaly(
                {"total_amount": "2970.00", "vat": "270.00"},
            )
        )


class HistoryNumberTests(unittest.TestCase):
    """history_number:顶层优先 · fields 兜底 · 键序生效。"""

    def test_top_level_wins(self):
        h = {"vat": "7.00", "fields": {"vat": "999"}}
        self.assertEqual(history_number(h, "vat"), 7.0)

    def test_fields_fallback(self):
        self.assertEqual(history_number({"fields": {"vat": "7.00"}}, "vat"), 7.0)

    def test_key_order_and_missing(self):
        h = {"fields": {"amount_before_tax": "100"}}
        self.assertEqual(history_number(h, "subtotal", "amount_before_tax"), 100.0)
        self.assertIsNone(history_number(h, "nope"))
        self.assertIsNone(history_number(None, "vat"))


class FlattenShapeContractTests(unittest.TestCase):
    """闸必须吃得下 flatten_history_for_mrerp 的真实产出(防止再次绿测空转)。"""

    def test_gate_fires_on_flattened_real_record(self):
        record = {
            "id": "h1",
            "total_amount": 2970.0,
            "invoice_no": "IV69/00106",
            "invoice_date": "2026-07-01",
            "pages": [{"fields": {"vat": "270.00", "seller_tax": "0105546015062"}}],
        }
        self.assertTrue(gen.vat_rate_anomaly(flatten_history_for_mrerp(record)))

    def test_gate_passes_flattened_7pct(self):
        record = {
            "id": "h2",
            "total_amount": 107.0,
            "pages": [{"fields": {"vat": "7.00"}}],
        }
        self.assertFalse(gen.vat_rate_anomaly(flatten_history_for_mrerp(record)))


class VatRateAnomalyValidatorTests(unittest.TestCase):
    def test_sales_validator_blocks_10pct(self):
        ok, code, _ = gen.validate_history_for_sales_credit(
            _sales("2970.00", "270.00", subtotal="2700.00"), _CLIENTS
        )
        self.assertFalse(ok)
        self.assertEqual(code, "ERR_VAT_RATE_ANOMALY")

    def test_sales_validator_passes_7pct(self):
        ok, code, _ = gen.validate_history_for_sales_credit(_sales("107.00", "7.00"), _CLIENTS)
        self.assertTrue(ok)
        self.assertIsNone(code)

    def test_purchase_validator_blocks_10pct(self):
        h = {
            "invoice_date": "2026-07-01",
            "total_amount": "2970.00",
            "fields": {"vat": "270.00", "seller_tax": "0999888777666"},  # 供应商码回退卖方税号
        }
        ok, code, _ = validate_purchase_history(h, {})
        self.assertFalse(ok)
        self.assertEqual(code, "ERR_VAT_RATE_ANOMALY")

    def test_friendly_translation_exists(self):
        from services.erp.mrerp_business_friendly import translate_reasons

        out = translate_reasons(["ERR_VAT_RATE_ANOMALY"])
        self.assertTrue(out and isinstance(out[0], dict))
        self.assertIn("en", out[0])


if __name__ == "__main__":
    unittest.main()

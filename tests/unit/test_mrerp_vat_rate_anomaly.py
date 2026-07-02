# -*- coding: utf-8 -*-
"""Bug#4 · VAT 税率合理性闸(对抗票 06:10% 内部自洽仍应转人工)。

税基取 total−vat(对折扣稳健)· 隐含税率非 ≈7% → ERR_VAT_RATE_ANOMALY(转人工)。
"""

from __future__ import annotations

import unittest

from services.erp import mrerp_xlsx_generator as gen
from services.erp.mrerp_xlsx_purchase import validate_purchase_history

_CLIENTS = {"clients": [{"erp_type": "mrerp", "client_id": 1, "erp_code": "0006"}]}


def _sales(total, vat, **extra):
    h = {
        "client_id": 1,
        "invoice_number": "IV1",
        "invoice_date": "2026-07-01",
        "total_amount": total,
        "vat": vat,
    }
    h.update(extra)
    return h


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
        self.assertFalse(gen.vat_rate_anomaly({"total_amount": "100.00"}))

    def test_rounding_noise_on_7pct_ok(self):
        # 小额四舍五入:base=1.50 → 7%=0.105→0.11 → 7.3% · 仍在带内
        self.assertFalse(gen.vat_rate_anomaly(_sales("1.61", "0.11")))


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
            "vat": "270.00",
            "fields": {"seller_tax": "0999888777666"},  # 供应商码回退卖方税号
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

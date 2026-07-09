# -*- coding: utf-8 -*-
"""Express 映射器单测 · 确定性纯函数(无 DB/网络)。

钉死:PTT 样例(税前 375347.20 / 7% / 含税 401621.50)→ 三行借贷平衡、佛历日期、
RR/HP 按付款分流;数不自洽/缺日期/缺科目 → ok=False(留人工);VAT=0 走两行。
"""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.mapper import build_express_payload  # noqa: E402

_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}


def _ptt_history(**over):
    fields = {
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "seller_tax": "0107561000013",
        "subtotal": "375347.20",
        "vat": "26274.30",
        "invoice_number": "RR581231-002",
    }
    fields.update(over.pop("fields", {}))
    h = {
        "id": "hist-ptt",
        "invoice_date": "2015-12-31",
        "invoice_no": "RR581231-002",
        "total_amount": "401621.50",
        "fields": fields,
    }
    h.update(over)
    return h


class ExpressMapperTests(unittest.TestCase):
    def test_ptt_sample_balanced_entry(self):
        r = build_express_payload(_ptt_history(), config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        p = r.payload
        self.assertEqual(p["account_set"], "DATAT")
        self.assertEqual(p["base_amount"], "375347.20")
        self.assertEqual(p["vat_amount"], "26274.30")
        self.assertEqual(p["total_amount"], "401621.50")
        # 佛历:2015 + 543 = 2558 → 末两位 58 · 12/31
        self.assertEqual(p["docdate_be"], "581231")
        self.assertEqual(p["vat_period_be"], "581201")
        self.assertEqual(p["doctype"], "RR")  # 默认未付 → 赊购
        # 三行借贷平衡
        dr = sum(Decimal(ln["amount"]) for ln in p["lines"] if ln["side"] == "D")
        cr = sum(Decimal(ln["amount"]) for ln in p["lines"] if ln["side"] == "C")
        self.assertEqual(dr, cr)
        self.assertEqual(len(p["lines"]), 3)
        accs = {ln["acc"] for ln in p["lines"]}
        self.assertEqual(accs, {"11-04-02-00", "11-05-04-01", "21-02-01-00"})
        # 采购科目落账套默认(无品类映射)→ 来源诚实标 config_default · 待核。
        self.assertEqual(p["account_source"], "config_default")
        self.assertTrue(p["account_review"])

    def test_verified_official_name_preferred(self):
        # ③ 官方名核验:已核验 → 行摘要用税局 RD 官方抬头(进账更干净)
        r = build_express_payload(
            _ptt_history(
                seller_name_official="บริษัท ปตท จำกัด (มหาชน) [OFFICIAL]",
                seller_name_verified=True,
            ),
            config=_CONFIG,
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["lines"][0]["desc"], "บริษัท ปตท จำกัด (มหาชน) [OFFICIAL]")

    def test_unverified_official_name_ignored(self):
        # 未核验 → 回落 AI 名(不冒用未确认的官方名)
        r = build_express_payload(
            _ptt_history(
                seller_name_official="บริษัท ปตท จำกัด (มหาชน) [OFFICIAL]",
                seller_name_verified=False,
            ),
            config=_CONFIG,
        )
        self.assertEqual(r.payload["lines"][0]["desc"], "บริษัท ปตท จำกัด (มหาชน)")

    def test_paid_routes_to_hp(self):
        r = build_express_payload(_ptt_history(fields={"payment_status": "paid"}), config=_CONFIG)
        self.assertTrue(r.ok)
        self.assertEqual(r.payload["doctype"], "HP")

    def test_receipt_doc_type_without_explicit_field_routes_to_hp(self):
        # F3:receipt 在场即便无显式 payment_status/method,票种语义已足够判现购。
        r = build_express_payload(_ptt_history(fields={"document_type": "receipt"}), config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["doctype"], "HP")

    def test_tax_invoice_doc_type_without_explicit_field_stays_rr(self):
        # F3:完整税票无显式付款字段 → 明确赊(仍是 RR,只是语义从「默认」升级为「明确」)。
        r = build_express_payload(
            _ptt_history(fields={"document_type": "tax_invoice"}), config=_CONFIG
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["doctype"], "RR")

    def test_supplier_new_when_unmapped(self):
        r = build_express_payload(_ptt_history(), config=_CONFIG)
        self.assertTrue(r.payload["supplier"]["supplier_new"])
        self.assertEqual(r.payload["supplier"]["tax_id"], "0107561000013")
        self.assertEqual(r.payload["supplier"]["prename"], "บริษัท")

    def test_supplier_address_carried(self):
        # 自建供应商:卖方地址进 payload → companion 落 APMAS(进项一致)。
        addr = "555 ถนนวิภาวดีรังสิต แขวงจตุจักร กรุงเทพฯ 10900"
        r = build_express_payload(_ptt_history(fields={"seller_addr": addr}), config=_CONFIG)
        self.assertEqual(r.payload["supplier"]["address"], addr)

    def test_supplier_code_from_mapping(self):
        mappings = {
            "accounts": [],
            "clients": [{"client_id": 42, "erp_type": "express", "erp_code": "ก005"}],
        }
        r = build_express_payload(_ptt_history(client_id=42), config=_CONFIG, mappings=mappings)
        self.assertEqual(r.payload["supplier"]["code"], "ก005")
        self.assertFalse(r.payload["supplier"]["supplier_new"])

    def test_account_from_mappings_bundle(self):
        mappings = {
            "accounts": [
                {"erp_type": "express", "pearnly_category": "fuel", "erp_code": "11-04-09-00"},
                {"erp_type": "express", "pearnly_category": "input_vat", "erp_code": "11-05-04-01"},
                {
                    "erp_type": "express",
                    "pearnly_category": "accounts_payable",
                    "erp_code": "21-02-01-00",
                },
            ],
            "clients": [],
        }
        r = build_express_payload(
            _ptt_history(), config={"account_set": "DATAT"}, mappings=mappings, category="fuel"
        )
        self.assertTrue(r.ok, r.reason)
        purchase = [ln for ln in r.payload["lines"] if ln["side"] == "D"][0]
        self.assertEqual(purchase["acc"], "11-04-09-00")
        # 品类映射命中 → 来源 category_map · 不待核(规则可信)。
        self.assertEqual(r.payload["account_source"], "category_map")
        self.assertFalse(r.payload["account_review"])

    def test_inconsistent_amounts_manual(self):
        h = _ptt_history(fields={"subtotal": "100.00", "vat": "7.00"}, total_amount="999.00")
        r = build_express_payload(h, config=_CONFIG)
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "amounts_not_consistent")

    def test_missing_date_manual(self):
        h = _ptt_history(invoice_date="")
        h["fields"].pop("date", None)
        r = build_express_payload(h, config=_CONFIG)
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "bad_or_missing_date")

    def test_missing_purchase_account_manual(self):
        r = build_express_payload(_ptt_history(), config={"account_set": "DATAT"})
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "no_purchase_account")

    def test_no_account_set_manual(self):
        r = build_express_payload(_ptt_history(), config={"fallback_acc": "11-04-02-00"})
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "no_account_set")

    def test_vat_derived_from_subtotal(self):
        # 缺 VAT · 用 总额−税前 推
        h = _ptt_history(fields={"subtotal": "375347.20", "vat": ""})
        r = build_express_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["vat_amount"], "26274.30")

    def test_vat_zero_two_line_entry(self):
        h = _ptt_history(fields={"subtotal": "100.00", "vat": "0"}, total_amount="100.00")
        r = build_express_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(len(r.payload["lines"]), 2)
        self.assertEqual(r.payload["vat_rate"], 0.0)
        dr = sum(Decimal(ln["amount"]) for ln in r.payload["lines"] if ln["side"] == "D")
        cr = sum(Decimal(ln["amount"]) for ln in r.payload["lines"] if ln["side"] == "C")
        self.assertEqual(dr, cr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

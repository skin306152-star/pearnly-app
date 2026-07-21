# -*- coding: utf-8 -*-
"""记账画像 → mapper 端到端接线守门(证明 escalation 真穿透 build_*_payload,非仅 infer 单测)。

- 永续客户(指纹)+ 库存路未开 → goods/销售 mapper 返回 ok=False · reason=posting_needs_review。
- 无库存客户 / 无指纹 → ok=True 正常入队(=今日默认,行为不变)。
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.mapper import build_express_payload  # noqa: E402
from services.erp.express_push.sales_mapper import build_express_sales_payload  # noqa: E402

_PERPETUAL_FP = {"stock_master_count": 672, "stcrd_lines": 9300, "stcrd_lines_moving_stock": 8102}
_NONE_FP = {"stock_master_count": 4, "stcrd_lines": 1530, "stcrd_lines_moving_stock": 75}

_PURCHASE_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}
_SALES_CONFIG = {
    "account_set": "DATAT",
    "revenue_acc": "41-01-01-00",
    "vat_output_acc": "21-05-01-00",
    "ar_acc": "11-03-01-00",
}


def _purchase_history():
    return {
        "id": "h1",
        "invoice_date": "2015-12-31",
        "invoice_no": "RR581231-002",
        "total_amount": "401621.50",
        "fields": {
            "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
            "seller_tax": "0107561000013",
            "subtotal": "375347.20",
            "vat": "26274.30",
            "invoice_number": "RR581231-002",
            "posting_item_type_manual": "goods",
            "items": [{"name": "เหล็กเส้น", "subtotal": "375347.20"}],
        },
    }


def _sales_history():
    return {
        "id": "s1",
        "invoice_date": "2015-12-31",
        "invoice_no": "IV581231-001",
        "total_amount": "107.00",
        "fields": {
            "buyer_name": "เงินสด",
            "subtotal": "100.00",
            "vat": "7.00",
            "invoice_number": "IV581231-001",
        },
    }


class PurchaseWireTests(unittest.TestCase):
    def test_perpetual_goods_escalates(self):
        cfg = {**_PURCHASE_CONFIG, "catalog_fingerprint": _PERPETUAL_FP}
        r = build_express_payload(_purchase_history(), config=cfg)
        self.assertFalse(r.ok)
        self.assertTrue(r.reason.startswith("posting_needs_review"), r.reason)

    def test_none_client_posts_normally(self):
        cfg = {**_PURCHASE_CONFIG, "catalog_fingerprint": _NONE_FP}
        r = build_express_payload(_purchase_history(), config=cfg)
        self.assertTrue(r.ok, r.reason)
        # 无库存客户 → 明细行落非库存(=今日默认 · 零回归 · 钉死 item_mode 标签)。
        self.assertTrue(r.payload["items"])
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "non_stock_item")

    def test_no_fingerprint_unchanged_default(self):
        r = build_express_payload(_purchase_history(), config=dict(_PURCHASE_CONFIG))
        self.assertTrue(r.ok, r.reason)


class SalesWireTests(unittest.TestCase):
    def test_perpetual_sale_escalates(self):
        cfg = {**_SALES_CONFIG, "catalog_fingerprint": _PERPETUAL_FP}
        r = build_express_sales_payload(_sales_history(), config=cfg)
        self.assertFalse(r.ok)
        self.assertTrue(r.reason.startswith("posting_needs_review"), r.reason)

    def test_none_client_sale_posts_normally(self):
        cfg = {**_SALES_CONFIG, "catalog_fingerprint": _NONE_FP}
        r = build_express_sales_payload(_sales_history(), config=cfg)
        self.assertTrue(r.ok, r.reason)


if __name__ == "__main__":
    unittest.main()

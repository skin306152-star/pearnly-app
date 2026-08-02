#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门测试 · 「没声明过账去向」这条失败在后端一路走到失败卡有料可渲染。

链条:mapper escalate(带票面商品行)→ classify 归 posting_kind_needed → derive_posting_fix
出 usage + items。断掉任何一环,失败卡就退回 2026-07-31 之前那个死胡同(卡上一个可点的
东西都没有,摘要教人回上传页重新识别 = 重扣一次 OCR 费)。

E2E 夹具 tests/fixtures/postkind_escalated_log.json 就是这条链的产物,这里一并比对,
防它被手改成产品不会产出的形状。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from gen_postkind_fixture import FIXTURE_PATH, build_fixture  # noqa: E402
from services.erp.express_push.mapper import build_express_payload  # noqa: E402
from services.erp.express_push.sales_mapper import build_express_sales_payload  # noqa: E402
from services.erp.push_exception_classify import (  # noqa: E402
    classify_push_exception,
    derive_posting_fix,
)

_PERPETUAL_FP = {"stock_master_count": 672, "stcrd_lines": 9300, "stcrd_lines_moving_stock": 8102}
_PURCHASE_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
    "catalog_fingerprint": _PERPETUAL_FP,
}
_SALES_CONFIG = {
    "account_set": "DATAT",
    "revenue_acc": "41-01-01-00",
    "vat_output_acc": "21-05-01-00",
    "ar_acc": "11-03-01-00",
    "catalog_fingerprint": _PERPETUAL_FP,
}
_ITEMS = [
    {"name": "แชมพู 500ml", "subtotal": "700.00"},
    {"name": "ครีมนวดผม", "subtotal": "300.00"},
]


def _purchase():
    return {
        "id": "h1",
        "invoice_date": "2026-07-15",
        "invoice_no": "RR690715-001",
        "total_amount": "1070.00",
        "fields": {
            "seller_name": "บริษัท ตัวอย่าง จำกัด",
            "seller_tax": "0107561000013",
            "subtotal": "1000.00",
            "vat": "70.00",
            "invoice_number": "RR690715-001",
            "posting_item_type_manual": "goods",
            "items": list(_ITEMS),
        },
    }


def _sales():
    return {
        "id": "s1",
        "invoice_date": "2026-07-15",
        "invoice_no": "IV690715-001",
        "total_amount": "1070.00",
        "fields": {
            "buyer_name": "เงินสด",
            "subtotal": "1000.00",
            "vat": "70.00",
            "invoice_number": "IV690715-001",
            "items": list(_ITEMS),
        },
    }


class EscalateCarriesItemsTests(unittest.TestCase):
    def test_purchase_escalate_carries_line_items(self):
        r = build_express_payload(_purchase(), config=_PURCHASE_CONFIG)
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "posting_needs_review:perpetual")
        self.assertEqual([i["name"] for i in r.items or []], ["แชมพู 500ml", "ครีมนวดผม"])

    def test_sales_escalate_carries_line_items(self):
        r = build_express_sales_payload(_sales(), config=_SALES_CONFIG)
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "posting_needs_review:perpetual")
        self.assertEqual([i["name"] for i in r.items or []], ["แชมพู 500ml", "ครีมนวดผม"])

    def test_declared_batch_does_not_escalate(self):
        for kind in ("stock", "service"):
            with self.subTest(kind=kind):
                r = build_express_payload(_purchase(), config=_PURCHASE_CONFIG, posting_kind=kind)
                self.assertTrue(r.ok, r.reason)


class ClassifyAndDeriveTests(unittest.TestCase):
    def test_classified_as_its_own_bucket(self):
        self.assertEqual(
            classify_push_exception("EXPRESS_MANUAL: posting_needs_review:perpetual"),
            "posting_kind_needed",
        )
        self.assertEqual(
            classify_push_exception("EXPRESS_MANUAL: posting_needs_review:mixed"),
            "posting_kind_needed",
        )

    def test_other_failures_unchanged(self):
        # 这条分支排在通用桶之前,不许把别的失败一起吞进来。
        self.assertEqual(
            classify_push_exception("EXPRESS_MANUAL: no_revenue_account"), "account_missing"
        )
        self.assertEqual(
            classify_push_exception("EXPRESS_MANUAL: stock_no_master_in_account_set"),
            "stock_opening_needed",
        )
        self.assertEqual(classify_push_exception("ERR_TIMEOUT"), "other")

    def test_derive_gives_usage_and_items(self):
        fix = derive_posting_fix(
            "EXPRESS_MANUAL: posting_needs_review:mixed",
            {"adapter": "express", "items": [{"name": "น้ำมันเครื่อง", "stkcod": "OIL-1"}]},
        )
        self.assertEqual(fix["usage"], "mixed")
        self.assertEqual(fix["items"], [{"name": "น้ำมันเครื่อง", "stkcod": "OIL-1"}])

    def test_derive_returns_none_for_other_reasons(self):
        self.assertIsNone(derive_posting_fix("EXPRESS_MANUAL: no_ap_account", {}))
        self.assertIsNone(derive_posting_fix(None, None))

    def test_derive_survives_missing_items(self):
        # 老日志(2026-07-31 之前 escalate 的行)载荷里没有 items · 卡显空态不该崩。
        fix = derive_posting_fix("EXPRESS_MANUAL: posting_needs_review:perpetual", None)
        self.assertEqual(fix, {"usage": "perpetual", "items": []})


class FixtureIsRealTests(unittest.TestCase):
    def test_e2e_fixture_matches_what_the_product_produces(self):
        on_disk = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(on_disk, build_fixture())


if __name__ == "__main__":
    unittest.main(verbosity=2)

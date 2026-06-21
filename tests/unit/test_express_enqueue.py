# -*- coding: utf-8 -*-
"""Express 入队闸门 + classify 哨兵单测(mock db · 无网络)。

钉死:高置信+映射成功 → EXPRESS_QUEUED(classify→pending);低置信/判脏/账套拒 →
EXPRESS_MANUAL(classify→manual);特性开关 off → 短路 failed;其它 adapter 哨兵零影响。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push import account_set_allowed, express_push_enabled  # noqa: E402
from services.erp.express_push.enqueue import enqueue_express  # noqa: E402
from services.erp.push_retry import classify_push_status  # noqa: E402

_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}

OWN_TAX = "0994000333444"  # 账套自家公司税号(方向判定锚点)
VENDOR_TAX = "0107561000013"
CUSTOMER_TAX = "0105551234567"


def _endpoint(**over):
    cfg = dict(_CONFIG)
    cfg.update(over.pop("config", {}))
    ep = {"id": "ep-1", "adapter": "express", "user_id": "u1", "enabled": True, "config": cfg}
    ep.update(over)
    return ep


def _history(confidence="high", **fover):
    # 进项:自家是买方(buyer_tax==OWN_TAX) → 方向自动判 purchase。
    fields = {
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "seller_tax": VENDOR_TAX,
        "buyer_tax": OWN_TAX,
        "subtotal": "375347.20",
        "vat": "26274.30",
        "invoice_number": "RR581231-002",
        "document_type": "tax_invoice",
    }
    fields.update(fover)
    return {
        "id": "hist-1",
        "invoice_date": "2015-12-31",
        "invoice_no": "RR581231-002",
        "total_amount": "401621.50",
        "confidence": confidence,
        "workspace_client_id": 7,
        "pages": [{"fields": fields}],
    }


class ClassifySentinelTests(unittest.TestCase):
    def test_queued_to_pending(self):
        self.assertEqual(classify_push_status(False, "EXPRESS_QUEUED"), "pending")

    def test_manual_sentinel(self):
        self.assertEqual(classify_push_status(False, "EXPRESS_MANUAL: low_confidence:x"), "manual")

    def test_other_adapters_unaffected(self):
        self.assertEqual(classify_push_status(True, None), "success")
        self.assertEqual(classify_push_status(False, "boom"), "failed")
        self.assertEqual(classify_push_status(False, "ERR_DUPLICATE_INVOICE"), "skipped_dup")


class EnqueueTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "true"})
        self._env.start()
        # tenant=None → 不查 mappings;mapper 用 config 兜底科目。
        self._tid = mock.patch("core.db.get_user_tenant_id", return_value=None)
        self._tid.start()
        # 锚点:账套自家公司税号 = OWN_TAX(方向判定用)。
        self._wc = mock.patch("core.db.get_workspace_client", return_value={"tax_id": OWN_TAX})
        self._wc.start()

    def tearDown(self):
        self._wc.stop()
        self._tid.stop()
        self._env.stop()

    def test_high_confidence_queued(self):
        r = enqueue_express(_endpoint(), _history())
        self.assertEqual(r["adapter"], "express")
        self.assertEqual(r["error_msg"], "EXPRESS_QUEUED")
        self.assertEqual(classify_push_status(r["success"], r["error_msg"]), "pending")
        self.assertEqual(r["request_body"]["account_set"], "DATAT")
        self.assertEqual(r["request_body"]["total_amount"], "401621.50")

    def test_low_confidence_manual(self):
        r = enqueue_express(_endpoint(), _history(confidence="low"))
        self.assertTrue(r["error_msg"].startswith("EXPRESS_MANUAL"))
        self.assertEqual(classify_push_status(r["success"], r["error_msg"]), "manual")
        self.assertIn("low_confidence", r["error_msg"])

    def test_dirty_mapping_manual(self):
        # 数不自洽 → mapper 判脏 → manual
        r = enqueue_express(_endpoint(), _history(subtotal="100.00", vat="7.00"))
        self.assertTrue(r["error_msg"].startswith("EXPRESS_MANUAL"))
        self.assertIn("amounts_not_consistent", r["error_msg"])

    def test_account_set_whitelist_reject(self):
        r = enqueue_express(_endpoint(config={"account_set": "PDATAT"}), _history())
        self.assertTrue(r["error_msg"].startswith("EXPRESS_MANUAL"))
        self.assertIn("account_set_not_allowed", r["error_msg"])
        self.assertEqual(classify_push_status(r["success"], r["error_msg"]), "manual")

    def test_flag_off_short_circuit(self):
        with mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "false"}):
            r = enqueue_express(_endpoint(), _history())
        self.assertEqual(r["error_msg"], "ERR_EXPRESS_DISABLED")
        self.assertEqual(classify_push_status(r["success"], r["error_msg"]), "failed")


_SALES_CONFIG = {
    "account_set": "DATAT",
    "revenue_acc": "41-01-00-00",
    "vat_output_acc": "11-05-04-02",
    "ar_acc": "11-02-01-00",
}


def _sales_endpoint(**over):
    cfg = dict(_SALES_CONFIG)
    cfg.update(over.pop("config", {}))
    ep = {"id": "ep-s", "adapter": "express", "user_id": "u1", "enabled": True, "config": cfg}
    ep.update(over)
    return ep


def _sales_history(confidence="high", **fover):
    # 销项:自家是卖方(seller_tax==OWN_TAX) → 方向自动判 sales(不靠显式标签)。
    fields = {
        "buyer_name": "บริษัท ลูกค้า จำกัด",
        "buyer_tax": CUSTOMER_TAX,
        "seller_tax": OWN_TAX,
        "subtotal": "23456.00",
        "vat": "1641.92",
        "invoice_number": "SO-9001",
        "document_type": "tax_invoice",
    }
    fields.update(fover)
    return {
        "id": "hist-s1",
        "invoice_date": "2015-12-15",
        "invoice_no": "SO-9001",
        "total_amount": "25097.92",
        "confidence": confidence,
        "workspace_client_id": 7,
        "pages": [{"fields": fields}],
    }


class DirectionRoutingTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "true"})
        self._env.start()
        self._tid = mock.patch("core.db.get_user_tenant_id", return_value=None)
        self._tid.start()
        self._wc = mock.patch("core.db.get_workspace_client", return_value={"tax_id": OWN_TAX})
        self._wc.start()

    def tearDown(self):
        self._wc.stop()
        self._tid.stop()
        self._env.stop()

    def test_sales_detected_routes_to_sales_mapper(self):
        # 自家=卖方 → 自动判 sales → 走 sales_mapper(产 customer 块)。
        r = enqueue_express(_sales_endpoint(), _sales_history())
        self.assertEqual(r["error_msg"], "EXPRESS_QUEUED")
        body = r["request_body"]
        self.assertEqual(body["direction"], "sales")
        self.assertEqual(body["doctype"], "IV")
        self.assertIn("customer", body)  # 销项产 customer 块
        self.assertNotIn("supplier", body)

    def test_purchase_detected_routes_to_purchase_mapper(self):
        # 自家=买方 → 自动判 purchase → 走 purchase_mapper(产 supplier 块)。
        r = enqueue_express(_endpoint(), _history())
        self.assertEqual(r["error_msg"], "EXPRESS_QUEUED")
        self.assertEqual(r["request_body"]["direction"], "purchase")
        self.assertIn("supplier", r["request_body"])

    def test_ambiguous_direction_to_manual(self):
        # 自家税号与票面 seller/buyer 都对不上 → ambiguous → EXPRESS_MANUAL: direction_unknown。
        h = _history(seller_tax=VENDOR_TAX, buyer_tax=CUSTOMER_TAX)
        r = enqueue_express(_endpoint(), h)
        self.assertTrue(r["error_msg"].startswith("EXPRESS_MANUAL"))
        self.assertIn("direction_unknown", r["error_msg"])
        self.assertEqual(classify_push_status(r["success"], r["error_msg"]), "manual")

    def test_own_tax_unread_to_manual(self):
        # 锚点(自家税号)读不到 → ambiguous → 留人工,绝不误推。
        with mock.patch("core.db.get_workspace_client", return_value={"tax_id": ""}):
            r = enqueue_express(_endpoint(), _history())
        self.assertTrue(r["error_msg"].startswith("EXPRESS_MANUAL"))
        self.assertIn("direction_unknown", r["error_msg"])

    def test_explicit_direction_label_wins(self):
        # 已带 sales 标签(用户确认)→ 即便缺锚点也按 sales。
        with mock.patch("core.db.get_workspace_client", return_value=None):
            h = _sales_history()
            h["direction"] = "sales"
            r = enqueue_express(_sales_endpoint(), h)
        self.assertEqual(r["request_body"]["direction"], "sales")

    def test_direction_not_enabled_manual(self):
        # 本连接只处理进项 → 销项票(自家=卖方)留人工。
        r = enqueue_express(_sales_endpoint(config={"directions": ["purchase"]}), _sales_history())
        self.assertTrue(r["error_msg"].startswith("EXPRESS_MANUAL"))
        self.assertIn("direction_not_enabled:sales", r["error_msg"])
        self.assertEqual(classify_push_status(r["success"], r["error_msg"]), "manual")


class FlagWhitelistTests(unittest.TestCase):
    def test_account_set_allowed(self):
        self.assertTrue(account_set_allowed("DATAT"))
        self.assertFalse(account_set_allowed("PDATAT"))
        self.assertFalse(account_set_allowed(""))

    def test_flag_default_off(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("ERP_PUSH_ENABLED", None)
            self.assertFalse(express_push_enabled())


if __name__ == "__main__":
    unittest.main(verbosity=2)

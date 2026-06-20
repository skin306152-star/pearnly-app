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


def _endpoint(**over):
    cfg = dict(_CONFIG)
    cfg.update(over.pop("config", {}))
    ep = {"id": "ep-1", "adapter": "express", "user_id": "u1", "enabled": True, "config": cfg}
    ep.update(over)
    return ep


def _history(confidence="high", **fover):
    fields = {
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "seller_tax": "0107561000013",
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

    def tearDown(self):
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

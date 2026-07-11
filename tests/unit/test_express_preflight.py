# -*- coding: utf-8 -*-
"""Express 前置条件体检(preflight)单测(mock db · 无网络)。

钉死:体检逐项 ok/blocked/pending 序与闸序一致;blocked 在正确项、其后 pending;ready 时
全 ok;enqueue 把体检写进 response_body(queued 与 manual 两路都带 preflight)。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.enqueue import enqueue_express  # noqa: E402
from services.erp.express_push.preflight import CHECK_KEYS, preflight_express  # noqa: E402

OWN_TAX = "0994000333444"
VENDOR_TAX = "0107561000013"
CUSTOMER_TAX = "0105551234567"

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


def _status_map(pf):
    return {c.key: c.status for c in pf.checks}


class PreflightBase(unittest.TestCase):
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


class ReadyTests(PreflightBase):
    def test_ready_all_ok(self):
        pf = preflight_express(_endpoint(), _history())
        self.assertTrue(pf.ready)
        self.assertFalse(pf.blocked)
        self.assertEqual([c.status for c in pf.checks], ["ok"] * len(CHECK_KEYS))
        self.assertEqual([c.key for c in pf.checks], list(CHECK_KEYS))
        self.assertEqual(pf.direction, "purchase")

    def test_checks_order_matches_check_keys(self):
        pf = preflight_express(_endpoint(), _history())
        self.assertEqual([c.key for c in pf.checks], list(CHECK_KEYS))


class BlockedTests(PreflightBase):
    def test_account_set_block_then_pending(self):
        pf = preflight_express(_endpoint(config={"account_set": ""}), _history())
        self.assertTrue(pf.blocked)
        self.assertTrue(pf.reason.startswith("account_set_not_allowed"))
        sm = _status_map(pf)
        self.assertEqual(sm["feature"], "ok")
        self.assertEqual(sm["account_set"], "blocked")
        self.assertEqual(sm["direction"], "pending")
        self.assertEqual(sm["confidence"], "pending")

    def test_direction_subject_unbound(self):
        # 自家税号读不到(主体没绑)→ direction blocked,sub=subject_unbound。
        with mock.patch("core.db.get_workspace_client", return_value={"tax_id": ""}):
            pf = preflight_express(_endpoint(), _history())
        self.assertEqual(pf.reason, "direction_unknown")
        dchk = next(c for c in pf.checks if c.key == "direction")
        self.assertEqual(dchk.status, "blocked")
        self.assertEqual(dchk.reason, "subject_unbound")

    def test_direction_ambiguous(self):
        # 自家税号在,但票面 seller/buyer 都对不上 → ambiguous。
        pf = preflight_express(_endpoint(), _history(seller_tax=VENDOR_TAX, buyer_tax=CUSTOMER_TAX))
        self.assertEqual(pf.reason, "direction_unknown")
        dchk = next(c for c in pf.checks if c.key == "direction")
        self.assertEqual(dchk.reason, "ambiguous")

    def test_chart_block_carries_bad_code(self):
        chart = [{"code": c, "name": c, "type": "1"} for c in ["11-05-04-01", "21-02-01-00"]]
        pf = preflight_express(_endpoint(config={"reported_accounts": chart}), _history())
        self.assertEqual(pf.reason, "account_not_in_chart:11-04-02-00")
        sm = _status_map(pf)
        self.assertEqual(sm["mapping"], "ok")
        self.assertEqual(sm["chart"], "blocked")
        self.assertEqual(sm["confidence"], "pending")

    def test_low_confidence_blocks_last(self):
        pf = preflight_express(_endpoint(), _history(confidence="low"))
        self.assertTrue(pf.reason.startswith("low_confidence"))
        sm = _status_map(pf)
        self.assertEqual(sm["chart"], "ok")
        self.assertEqual(sm["confidence"], "blocked")


class DocumentSanityTests(PreflightBase):
    """单据防呆闸:外币/贷项/押金/未来日期/坏税号 → blocked 在 document 项,其后 pending。"""

    def _assert_doc_blocked(self, pf, reason):
        self.assertTrue(pf.blocked)
        self.assertEqual(pf.reason, reason)
        sm = _status_map(pf)
        self.assertEqual(sm["direction_enabled"], "ok")
        self.assertEqual(sm["document"], "blocked")
        self.assertEqual(sm["mapping"], "pending")
        self.assertEqual(sm["confidence"], "pending")

    def test_foreign_currency_blocked(self):
        pf = preflight_express(_endpoint(), _history(currency="USD"))
        self._assert_doc_blocked(pf, "currency_not_thb:usd")

    def test_credit_note_blocked(self):
        pf = preflight_express(_endpoint(), _history(document_type="credit_note"))
        self._assert_doc_blocked(pf, "credit_note")

    def test_deposit_blocked(self):
        pf = preflight_express(_endpoint(), _history(notes="เงินมัดจำ ยังไม่ส่งมอบ"))
        self._assert_doc_blocked(pf, "deposit_receipt")

    def test_invalid_tax_id_blocked(self):
        pf = preflight_express(_endpoint(), _history(seller_tax="01055560123"))
        self._assert_doc_blocked(pf, "tax_id_invalid")

    def test_future_date_blocked(self):
        h = _history()
        h["invoice_date"] = "2099-12-31"
        pf = preflight_express(_endpoint(), h)
        self._assert_doc_blocked(pf, "date_future")

    def test_clean_invoice_passes_document(self):
        pf = preflight_express(_endpoint(), _history())
        self.assertTrue(pf.ready)
        sm = _status_map(pf)
        self.assertEqual(sm["document"], "ok")


class PayloadVersionTests(PreflightBase):
    """载荷版本协商:老小助手(未上报)不拦;上报低于当前契约拦;上报够新放行。"""

    def test_no_report_treated_as_supported_not_blocked(self):
        pf = preflight_express(_endpoint(), _history())
        self.assertTrue(pf.ready)
        pv = next(c for c in pf.checks if c.key == "payload_version")
        self.assertEqual(pv.status, "ok")

    def test_outdated_report_blocks(self):
        pf = preflight_express(_endpoint(config={"max_payload_version": 0}), _history())
        self.assertTrue(pf.blocked)
        self.assertEqual(pf.reason, "payload_version_outdated:0")
        sm = _status_map(pf)
        self.assertEqual(sm["account_set"], "ok")
        self.assertEqual(sm["payload_version"], "blocked")
        self.assertEqual(sm["direction"], "pending")
        self.assertEqual(sm["confidence"], "pending")

    def test_current_report_passes(self):
        pf = preflight_express(_endpoint(config={"max_payload_version": 1}), _history())
        self.assertTrue(pf.ready)
        pv = next(c for c in pf.checks if c.key == "payload_version")
        self.assertEqual(pv.status, "ok")


class DisabledTests(unittest.TestCase):
    def test_disabled_short_circuit(self):
        with mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "false"}):
            pf = preflight_express(_endpoint(), _history())
        self.assertTrue(pf.disabled)
        self.assertFalse(pf.ready)
        self.assertFalse(pf.blocked)
        feat = next(c for c in pf.checks if c.key == "feature")
        self.assertEqual(feat.status, "blocked")


class EnqueueCarriesPreflightTests(PreflightBase):
    def test_queued_response_carries_preflight(self):
        body = json.loads(enqueue_express(_endpoint(), _history())["response_body"])
        self.assertIn("preflight", body)
        self.assertTrue(all(c["status"] == "ok" for c in body["preflight"]))

    def test_manual_response_carries_preflight(self):
        r = enqueue_express(_endpoint(), _history(confidence="low"))
        body = json.loads(r["response_body"])
        self.assertEqual(body["queued"], False)
        self.assertIn("preflight", body)
        conf = next(c for c in body["preflight"] if c["key"] == "confidence")
        self.assertEqual(conf["status"], "blocked")


if __name__ == "__main__":
    unittest.main(verbosity=2)

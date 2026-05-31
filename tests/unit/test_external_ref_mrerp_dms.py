#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_external_ref_mrerp_dms.py

DMS 集成(2026-05-31)· external_ref 派生器守门。

push_mrerp_dms_id_card 把 booking_no/booking_id/customer_id 写进
erp_push_logs.response_body。日志列表/详情靠 derive_external_ref 把
booking_no 提到 external_doc_no 给用户看 + 提示去 DMS 订车单搜。
这个测试钉死 mrerp_dms 派生器的契约,防回归。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.external_ref import derive_external_ref  # noqa: E402


class DeriveMrerpDmsTests(unittest.TestCase):
    def test_booking_no_maps_to_external_doc_no(self):
        body = {
            "adapter": "mrerp_dms",
            "booking_no": "PN0010100531",
            "booking_id": "16",
            "customer_id": "65",
        }
        out = derive_external_ref("mrerp_dms", body, "success")
        self.assertEqual(out["external_doc_no"], "PN0010100531")
        self.assertEqual(out["external_doc_id"], "16")
        self.assertEqual(out["external_doc_hint"], "mrerp_dms_search")
        self.assertEqual(out["external_url"], "")

    def test_accepts_json_string_body(self):
        import json

        body = json.dumps({"booking_no": "PNABC", "booking_id": "9"})
        out = derive_external_ref("mrerp_dms", body, "success")
        self.assertEqual(out["external_doc_no"], "PNABC")
        self.assertEqual(out["external_doc_id"], "9")

    def test_booking_id_only_falls_back_to_doc_id(self):
        out = derive_external_ref("mrerp_dms", {"booking_id": "21"}, "success")
        self.assertEqual(out["external_doc_no"], "")
        self.assertEqual(out["external_doc_id"], "21")

    def test_empty_body_all_empty_never_raises(self):
        for bad in (None, {}, "", "not-json", {"booking_no": "", "booking_id": ""}):
            out = derive_external_ref("mrerp_dms", bad, "failed")
            self.assertEqual(out["external_doc_no"], "")
            self.assertEqual(out["external_doc_id"], "")
            self.assertEqual(out["external_doc_hint"], "")

    def test_mrerp_dms_does_not_use_invoice_mrerp_deriver(self):
        # mrerp(发票)派生器认 mrerp_bill_no;mrerp_dms 必须走自己的派生器,
        # 不能把 mrerp_bill_no 当订车单号(否则财务/订车单号串味)。
        body = {"mrerp_bill_no": "SI-123", "booking_no": "PNXYZ"}
        out = derive_external_ref("mrerp_dms", body, "success")
        self.assertEqual(out["external_doc_no"], "PNXYZ")
        self.assertNotEqual(out["external_doc_no"], "SI-123")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_dms_logs.py

DMS 集成(2026-05-31)· push_mrerp_dms_id_card 日志输入形状守门(离线 · patch adapter)。

dms_routes 把 push_mrerp_dms_id_card 的返回写进 erp_push_logs(history_id=None ·
trigger='id_card')。这个测试钉死成功/失败两种返回的形状,确保:
  - response_body(进 erp_push_logs.response_body)带 booking_no/booking_id/customer_id
    → external_ref 能派生订车单号。
  - 失败带 error_code/error_msg(进 erp_push_logs.error_msg)。
  - response_body 可 json.dumps(路由会序列化)。
  - 永不抛(铁律:DMS 失败不应 500)。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import erp_push as _erp  # noqa: E402
from services.erp.mrerp_dms_models import DMSPushResult  # noqa: E402


class _FakeAdapter:
    def __init__(self, result):
        self._result = result

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def push_id_card_booking(self, card, defaults):
        return self._result


_ENDPOINT = {
    "id": "ep-dms",
    "adapter": "mrerp_dms",
    "config": {
        "system_url": "https://www.mrerp4sme.com/dms/index.php",
        "username_enc": "gAAAAA_x",
        "password_enc": "gAAAAA_y",
        "booking_defaults": {"booking_prefix": "PN"},
    },
}

_ID_CARD = {
    "people_id": "9900000001010",
    "first_name": "ทดสอบ",
    "last_name": "เพียร์ลี่",
    "birthday_be": "01/01/2530",
    "prefix_name": "นาย",
    "address": {"house_no": "1/2", "province": "กรุงเทพมหานคร"},
}


class PushMrerpDmsLogShapeTests(unittest.TestCase):
    def test_success_shape_carries_booking_ids(self):
        ok = DMSPushResult(
            ok=True,
            customer_id="65",
            booking_id="16",
            booking_no="PN0010100531",
            response_code="sc::1",
        )
        with patch.object(_erp, "_build_mrerp_dms_adapter", return_value=(_FakeAdapter(ok), None)):
            res = _erp.push_mrerp_dms_id_card(_ENDPOINT, _ID_CARD)
        self.assertTrue(res["success"])
        self.assertEqual(res["adapter"], "mrerp_dms")
        self.assertEqual(res["customer_id"], "65")
        self.assertEqual(res["booking_id"], "16")
        self.assertEqual(res["booking_no"], "PN0010100531")
        self.assertIsNone(res["error_msg"])
        self.assertIn("elapsed_ms", res)
        # response_body → erp_push_logs.response_body · must carry booking_no + be JSON-safe.
        self.assertEqual(res["response_body"]["booking_no"], "PN0010100531")
        json.dumps(res["response_body"])  # must not raise

    def test_failure_shape_carries_error_code(self):
        bad = DMSPushResult(ok=False, error_code="ERR_DMS_IMPORT", error="boom")
        with patch.object(_erp, "_build_mrerp_dms_adapter", return_value=(_FakeAdapter(bad), None)):
            res = _erp.push_mrerp_dms_id_card(_ENDPOINT, _ID_CARD)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "ERR_DMS_IMPORT")
        self.assertEqual(res["error_msg"], "ERR_DMS_IMPORT")
        self.assertEqual(res["http_status"], 0)
        self.assertIsInstance(res["response_body"], dict)
        json.dumps(res["response_body"])

    def test_build_failure_returns_friendly_not_raise(self):
        # adapter construction failed (e.g. no creds) → never raises.
        with patch.object(
            _erp,
            "_build_mrerp_dms_adapter",
            return_value=(None, {"error_code": "ERR_NO_CREDS", "raw": "missing"}),
        ):
            res = _erp.push_mrerp_dms_id_card(_ENDPOINT, _ID_CARD)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "ERR_NO_CREDS")

    def test_never_raises_on_adapter_exception(self):
        class _Boom:
            def __enter__(self):
                raise RuntimeError("kaboom")

            def __exit__(self, *a):
                return False

        with patch.object(_erp, "_build_mrerp_dms_adapter", return_value=(_Boom(), None)):
            res = _erp.push_mrerp_dms_id_card(_ENDPOINT, _ID_CARD)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "ERR_DMS_UNEXPECTED")


if __name__ == "__main__":
    unittest.main()

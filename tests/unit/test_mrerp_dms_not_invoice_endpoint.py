#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_dms_not_invoice_endpoint.py

DMS 集成(2026-05-31)· 防误推守门(高危数据错投保护)。

mrerp_dms 是身份证→订车单适配器,绝不是发票推送目标。push_to_endpoint
(发票自动/手动推送主入口)收到 adapter='mrerp_dms' 必须硬拒,返回
ERR_DMS_NOT_INVOICE_ENDPOINT,绝不真去 DMS。否则发票 history 可能被推进
DMS 订车系统 —— 这是高危数据错投。

若此测试回归:有人放开了 push_to_endpoint 的 mrerp_dms 闸 —— yank 那个 commit。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import erp_push as _erp  # noqa: E402


class PushToEndpointRejectsDmsTests(unittest.TestCase):
    def _invoice_history(self):
        return {
            "id": "h-1",
            "invoice_no": "INV-1",
            "seller_name": "Some Seller",
            "total_amount": 100.0,
            "pages": [{"fields": {"buyer_name": "B"}}],
        }

    def test_push_to_endpoint_rejects_mrerp_dms_invoice(self):
        endpoint = {
            "id": "ep-dms",
            "adapter": "mrerp_dms",
            "config": {"system_url": "https://x.invalid", "username_enc": "u", "password_enc": "p"},
            "enabled": True,
        }
        result = _erp.push_to_endpoint(endpoint, self._invoice_history())
        self.assertFalse(result["success"])
        self.assertEqual(result["error_msg"], "ERR_DMS_NOT_INVOICE_ENDPOINT")
        self.assertEqual(result["adapter"], "mrerp_dms")
        # Must NOT have a successful http push body.
        self.assertEqual(result["http_status"], 0)

    def test_mrerp_dms_registry_stub_refuses(self):
        # The stub exists only for ADAPTER_REGISTRY membership; if ever
        # reached it must refuse (the early-reject in push_to_endpoint
        # shadows it, but a regression there would expose this).
        success, http_status, body = _erp.push_mrerp_dms({}, {"x": 1})
        self.assertFalse(success)
        self.assertEqual(http_status, 0)
        self.assertIn("not an invoice push target", body.lower())

    def test_mrerp_dms_in_registry_and_encrypted_sets(self):
        self.assertIn("mrerp_dms", _erp.ADAPTER_REGISTRY)
        self.assertIn("mrerp_dms", _erp.ENCRYPTED_CRED_ADAPTERS)

    def test_webhook_still_routes_normally(self):
        # The DMS early-reject must not break other adapters.
        original = _erp.ADAPTER_REGISTRY.get("webhook")
        from unittest.mock import MagicMock

        _erp.ADAPTER_REGISTRY["webhook"] = MagicMock(return_value=(True, 200, "ok"))
        try:
            endpoint = {"id": "w", "adapter": "webhook", "config": {"url": "https://x/"}}
            result = _erp.push_to_endpoint(endpoint, self._invoice_history())
        finally:
            _erp.ADAPTER_REGISTRY["webhook"] = original
        self.assertTrue(result["success"])
        self.assertEqual(result["adapter"], "webhook")


if __name__ == "__main__":
    unittest.main()

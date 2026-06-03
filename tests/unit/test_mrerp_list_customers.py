#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_list_customers.py

Offline coverage for `erp_push.list_mrerp_customers` — the helper the
new `GET /api/erp/endpoints/:id/customers` route dispatches to.

We only exercise the early-exit paths that don't need a real MR.ERP
session (no creds, bad encryption). The happy path is covered by the
existing customer-sync integration tests; this file confirms the
helper's contract (return shape, ERR codes, friendly catalogue lookup).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.erp_push import list_mrerp_customers  # noqa: E402


class ContractTests(unittest.TestCase):

    def test_no_creds_returns_friendly_error(self):
        r = list_mrerp_customers({})
        self.assertFalse(r["ok"])
        self.assertEqual(r["customers"], [])
        self.assertEqual(r["error_code"], "ERR_NO_CREDS")
        self.assertIn("th", r["error_friendly"])
        self.assertIn("en", r["error_friendly"])
        self.assertIn("zh", r["error_friendly"])
        self.assertIn("zh_TW", r["error_friendly"])
        self.assertIn("尚未填", r["error_friendly"]["zh"])

    def test_username_only_no_password(self):
        r = list_mrerp_customers({"username_enc": "abc"})
        self.assertFalse(r["ok"])
        self.assertEqual(r["error_code"], "ERR_NO_CREDS")

    def test_bad_encrypted_creds_returns_decrypt_error(self):
        # Garbage Fernet tokens — should raise InvalidToken inside
        # MRERPAdapter.from_encrypted and surface as ERR_CRED_DECRYPT.
        r = list_mrerp_customers(
            {
                "username_enc": "not-a-real-fernet-token",
                "password_enc": "not-a-real-fernet-token-either",
                "system_url": "https://www.mrerp4sme.com",
            }
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["error_code"], "ERR_CRED_DECRYPT")
        self.assertIn("zh", r["error_friendly"])

    def test_shape_has_required_keys(self):
        r = list_mrerp_customers({})
        for k in ("ok", "elapsed_ms", "customers", "error_code", "error_friendly", "raw_error"):
            self.assertIn(k, r, f"missing key: {k}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

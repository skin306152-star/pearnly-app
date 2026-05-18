#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_customer_sync.py

Integration tests for MRERPCustomerSyncService.lookup against the real
MR.ERP TEST2019 sandbox.

Relies on the test customer pre-created by Zihao 2026-05-18:
    code: 0006
    name: Skin Trading Co., Ltd.
    type: ลูกหนี้การค้า
(see docs/integrations/mrerp-known-facts.md §10.2)

Skipped automatically if .env.local lacks MR.ERP credentials.

Run directly:
    python tests/integration/test_mrerp_customer_sync.py
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_adapter import MRERPAdapter   # noqa: E402
from services.erp.mrerp_customer_sync import (    # noqa: E402
    BuyerInfo,
    MRERPCustomerSyncService,
)

from tests.integration._mrerp_common import require_credentials   # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


KNOWN_CUSTOMER_CODE = "0006"
KNOWN_CUSTOMER_NAME = "Skin Trading Co., Ltd."


class CustomerSyncLookupIntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.creds = require_credentials()
        cls.adapter = MRERPAdapter(
            login_url=cls.creds[0],
            username=cls.creds[1],
            password=cls.creds[2],
            comidyear=cls.creds[3],
            seldb=cls.creds[4],
            headless=True,
        )
        cls.adapter.__enter__()
        cls.svc = MRERPCustomerSyncService(cls.adapter)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.adapter.__exit__(None, None, None)
        except Exception:
            pass

    def setUp(self):
        # Clear the per-service cache so each test starts cold.
        self.svc.invalidate()

    def test_layer1_db_mapping_returns_code_without_listing_fetch(self):
        """Caller already has the mapping in hand — service should return
        the cached code without touching the listing."""
        buyer = BuyerInfo(
            name="anything goes here",
            client_id=99,
            tenant_id="test-tenant",
        )
        mappings = {"clients": [{
            "erp_type": "mrerp",
            "client_id": 99,
            "erp_code": KNOWN_CUSTOMER_CODE,
        }]}
        out = self.svc.lookup(buyer, mappings)
        self.assertIsNotNone(out, "L1 lookup must find the pre-set mapping")
        self.assertEqual(out.customer_code, KNOWN_CUSTOMER_CODE)
        self.assertEqual(out.source, "db_mapping")
        self.assertEqual(out.confidence, 1.0)

    def test_layer2_exact_name_match(self):
        """No mapping in hand; provide buyer.name exactly as MR.ERP holds
        it. After normalize, this collapses to the canonical form and
        scores 1.0 against the listing → 'erp_name_match'."""
        buyer = BuyerInfo(
            name=KNOWN_CUSTOMER_NAME,
            client_id=1001,           # unmapped client id
            tenant_id="test-tenant",
        )
        out = self.svc.lookup(buyer, {"clients": []})
        self.assertIsNotNone(out,
                             "L2 should find Skin Trading by name")
        self.assertEqual(out.customer_code, KNOWN_CUSTOMER_CODE)
        self.assertIn(out.source, ("erp_name_match", "erp_fuzzy_match"))
        self.assertGreaterEqual(out.confidence, 0.95)

    def test_layer3_fuzzy_with_typo(self):
        """Two-char typo in 'Skin Trading' — exercises Levenshtein 0.82
        threshold path (ratio should land around 0.833)."""
        buyer = BuyerInfo(
            name="Skn Tradng Co., Ltd.",
            client_id=1002,
            tenant_id="test-tenant",
        )
        out = self.svc.lookup(buyer, {"clients": []})
        self.assertIsNotNone(out, "L3 should fuzzy-match Skn Tradng → Skin Trading")
        self.assertEqual(out.customer_code, KNOWN_CUSTOMER_CODE)
        # Could be exact or fuzzy depending on how aggressive the
        # normalization is; both are acceptable hits.
        self.assertIn(out.source, ("erp_name_match", "erp_fuzzy_match"))
        self.assertGreaterEqual(out.confidence, 0.82)

    def test_no_match_returns_none(self):
        """A buyer whose name has no plausible counterpart in the listing
        must return None instead of guessing."""
        buyer = BuyerInfo(
            name="Pearnly Test Unknown Manufacturing PLC",
            client_id=1003,
            tenant_id="test-tenant",
        )
        out = self.svc.lookup(buyer, {"clients": []})
        self.assertIsNone(
            out,
            "no plausible match should NOT trigger a false-positive code",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

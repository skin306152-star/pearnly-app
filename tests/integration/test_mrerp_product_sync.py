#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_product_sync.py

Integration tests for MRERPProductSyncService.lookup against the real
MR.ERP TEST2019 sandbox.

Uses "P001" / "Pepsi 500ml" as the known-existing product (seen in the
captured stkmas listing).

Skipped automatically if .env.local lacks MR.ERP credentials.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_adapter import MRERPAdapter  # noqa: E402
from services.erp.mrerp_product_sync import (  # noqa: E402
    ItemInfo,
    MRERPProductSyncService,
)

from tests.integration._mrerp_common import require_credentials  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


KNOWN_PRODUCT_CODE = "P001"
KNOWN_PRODUCT_NAME = "Pepsi 500ml"


class ProductSyncLookupIntegrationTest(unittest.TestCase):

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
        cls.svc = MRERPProductSyncService(cls.adapter)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.adapter.__exit__(None, None, None)
        except Exception:
            pass

    def setUp(self):
        self.svc.invalidate()

    def test_product_lookup_via_existing_mapping(self):
        """Layer 1 hit — caller already has the (item_name_norm,
        erp_code) mapping stitched. Service returns without touching
        the network."""
        item = ItemInfo(
            name="some custom name from OCR",
            tenant_id="test-tenant",
        )
        mappings = {
            "products": [
                {
                    "erp_type": "mrerp",
                    "item_name": "some custom name from OCR",
                    "item_name_norm": "some custom name from ocr",
                    "erp_code": KNOWN_PRODUCT_CODE,
                }
            ]
        }
        out = self.svc.lookup(item, mappings)
        self.assertIsNotNone(out)
        self.assertEqual(out.product_code, KNOWN_PRODUCT_CODE)
        self.assertEqual(out.source, "db_mapping")

    def test_product_lookup_via_listing_exact_name(self):
        """Layer 2 — buyer name is the canonical form. After normalize
        it collapses to the listing's stored value → exact match."""
        item = ItemInfo(
            name=KNOWN_PRODUCT_NAME,
            tenant_id="test-tenant",
        )
        out = self.svc.lookup(item, {"products": []})
        self.assertIsNotNone(out)
        self.assertEqual(out.product_code, KNOWN_PRODUCT_CODE)
        self.assertIn(out.source, ("erp_name_match", "erp_fuzzy_match"))
        self.assertGreaterEqual(out.confidence, 0.90)

    def test_product_lookup_via_fuzzy_match(self):
        """Layer 3 — single-char typo in 'Pepsi' should still match at
        the 0.90 threshold (ratio ~0.91 on a 9-char normalized form)."""
        item = ItemInfo(
            name="Peosi 500ml",  # 'Peosi' instead of 'Pepsi'
            tenant_id="test-tenant",
        )
        out = self.svc.lookup(item, {"products": []})
        self.assertIsNotNone(out, "L3 should fuzzy-match Peosi → Pepsi")
        self.assertEqual(out.product_code, KNOWN_PRODUCT_CODE)
        self.assertIn(out.source, ("erp_name_match", "erp_fuzzy_match"))
        self.assertGreaterEqual(out.confidence, 0.90)

    def test_no_match_returns_none(self):
        item = ItemInfo(
            name="Pearnly Test Unknown Product PLC v999",
            tenant_id="test-tenant",
        )
        self.assertIsNone(self.svc.lookup(item, {"products": []}))


if __name__ == "__main__":
    unittest.main(verbosity=2)

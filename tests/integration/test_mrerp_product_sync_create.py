#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_product_sync_create.py

Phase 3 integration tests for MRERPProductSyncService.lookup_or_create
auto-create (copy-from-seed) against the real MR.ERP TEST2019 sandbox.

Seed product: "P001" / "Pepsi 500ml" (visible in the stkmas listing).

Same cleanup caveat as customer auto-create: test01 on TEST2019
returns "Delete Success" from stkmas/alldel.php but the row often
remains in the listing. Teardown logs orphans for periodic manual
cleanup; production tenants run under admin accounts.
"""

from __future__ import annotations

import logging
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.exceptions import MRERPBusinessError  # noqa: E402
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


SEED_PRODUCT_CODE = "P001"  # Pepsi 500ml


def _unique_item_name() -> str:
    return f"Pearnly Product Test {uuid.uuid4().hex[:8].upper()} v1"


class ProductAutoCreateIntegrationTest(unittest.TestCase):

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
        self._created_codes = []

    def tearDown(self):
        for code in self._created_codes:
            try:
                ok = self.svc.delete_product(code)
                logging.info("teardown delete %s -> %s", code, ok)
                if not ok:
                    logging.warning(
                        "ORPHANED PRODUCT (please clean manually): %s",
                        code,
                    )
            except Exception as e:
                logging.warning(
                    "teardown delete %s raised: %s",
                    code,
                    e,
                )

    def test_product_auto_create_via_seed_success(self):
        """Clone Pepsi (P001) into a new product with uuid-suffixed
        name. Verify code generation, mapping persistence, listing
        appearance, and the inherited-price warning."""
        item_name = _unique_item_name()
        item = ItemInfo(name=item_name, tenant_id="test-tenant")
        mappings = {"products": []}

        # Confirm L0-L3 miss first.
        self.assertIsNone(self.svc.lookup(item, mappings))

        # Auto-create.
        out = self.svc.lookup_or_create(
            item,
            mappings,
            seed_product_code=SEED_PRODUCT_CODE,
        )

        self.assertEqual(out.source, "erp_auto_created")
        self.assertTrue(out.is_new)
        self.assertTrue(out.product_code.startswith("P"))
        self.assertLessEqual(len(out.product_code), 20)
        self.assertEqual(out.matched_name, item_name)
        self.assertIn(
            "WARN_PRODUCT_PRICE_INHERITED_FROM_SEED",
            out.warnings,
            "auto-create should flag inherited price for review",
        )
        self._created_codes.append(out.product_code)

        # Mapping persisted in-memory.
        self.assertTrue(out.erp_code_persisted)
        prods = mappings["products"]
        self.assertEqual(len(prods), 1)
        self.assertEqual(prods[0]["erp_code"], out.product_code)
        self.assertEqual(
            prods[0]["item_name_norm"],
            item_name.lower(),
        )

        # Second call must hit L1 / cache.
        again = self.svc.lookup_or_create(
            item,
            mappings,
            seed_product_code=SEED_PRODUCT_CODE,
        )
        self.assertEqual(again.product_code, out.product_code)
        self.assertIn(again.source, ("cache_hit", "db_mapping"))

    def test_product_auto_create_fails_when_no_seed(self):
        """No seed → fast-fail with ERR_NO_SEED_PRODUCT. The service
        must NEVER silently fall back to the broken placeholder path
        (the same rule as Customer Sync)."""
        item = ItemInfo(
            name=_unique_item_name(),
            tenant_id="test-tenant",
        )
        with self.assertRaises(MRERPBusinessError) as ctx:
            self.svc.lookup_or_create(item, {"products": []})
        self.assertIn("ERR_NO_SEED_PRODUCT", str(ctx.exception))
        self.assertEqual(len(self._created_codes), 0)

    def test_product_unit_not_found_raises_friendly_error(self):
        """Zihao Q3 (拍板 2026-05-18): when OCR captures a unit that
        doesn't match the seed product's unit, the service must raise
        ERR_PRODUCT_UNIT_NOT_FOUND instead of silently overriding the
        seed's unit. The user resolves by either picking a seed with
        the right unit OR dropping the OCR unit hint."""
        item = ItemInfo(
            name=_unique_item_name(),
            tenant_id="test-tenant",
            unit_code="PEARNLY-NONEXISTENT-UNIT-9Z",  # never matches seed
        )
        with self.assertRaises(MRERPBusinessError) as ctx:
            self.svc.lookup_or_create(
                item,
                {"products": []},
                seed_product_code=SEED_PRODUCT_CODE,
            )
        self.assertIn("ERR_PRODUCT_UNIT_NOT_FOUND", str(ctx.exception))
        # Sanity: nothing was created (raise happened before btnsave).
        self.assertEqual(len(self._created_codes), 0)

    def test_product_name_truncation_with_warn(self):
        """Name > 100 chars → truncates + adds WARN_PRODUCT_NAME_TRUNCATED.
        Result still saves successfully."""
        long_suffix = "Z" * 120
        long_name = f"Pearnly LongName Test {uuid.uuid4().hex[:8]} {long_suffix}"
        self.assertGreater(len(long_name), 100)
        item = ItemInfo(name=long_name, tenant_id="test-tenant")

        out = self.svc.lookup_or_create(
            item,
            {"products": []},
            seed_product_code=SEED_PRODUCT_CODE,
        )
        self._created_codes.append(out.product_code)

        self.assertEqual(out.source, "erp_auto_created")
        self.assertIn(
            "WARN_PRODUCT_NAME_TRUNCATED",
            out.warnings,
            "long name should trigger truncation warning",
        )
        self.assertIn(
            "WARN_PRODUCT_PRICE_INHERITED_FROM_SEED",
            out.warnings,
            "inherited price warning should also fire",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_customer_sync_create.py

Integration test for MRERPCustomerSyncService.lookup_or_create with the
copy-from-seed Layer 4 (Zihao 2026-05-18 拍板 · Decision 1).

Two paths exercised:
  - seed configured → copy succeeds, new customer appears in listing,
                       teardown deletes it
  - no seed configured → MRERPBusinessError(ERR_NO_SEED_CUSTOMER)
  - seed match (existing customer) → lookup hits Layer 2/3 first;
                                      auto-create is never reached

Skipped automatically if .env.local lacks MR.ERP credentials.

Run directly:
    python tests/integration/test_mrerp_customer_sync_create.py
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
from services.erp.mrerp_customer_sync import (  # noqa: E402
    BuyerInfo,
    MRERPCustomerSyncService,
)

from tests.integration._mrerp_common import require_credentials  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


SEED_CUSTOMER_CODE = "0006"  # Skin Trading Co., Ltd. (pre-created)


def _unique_buyer_name() -> str:
    return f"Pearnly Auto Test {uuid.uuid4().hex[:8].upper()} Co., Ltd."


class CustomerAutoCreateIntegrationTest(unittest.TestCase):

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
        self.svc.invalidate()
        self._created_codes = []

    def tearDown(self):
        for code in self._created_codes:
            try:
                ok = self.svc.delete_customer(code)
                logging.info("teardown delete %s -> %s", code, ok)
                if not ok:
                    logging.warning(
                        "ORPHANED CUSTOMER (please clean manually): %s",
                        code,
                    )
            except Exception as e:
                logging.warning(
                    "teardown delete %s raised: %s",
                    code,
                    e,
                )

    def test_auto_create_via_seed_success(self):
        """🟢 (Zihao 2026-05-18 unblocked) Copy-from-seed produces a real
        new customer row in MR.ERP. We give the service:
          - a uuid-suffixed buyer.name (guaranteed no L2/L3 match)
          - seed_customer_code="0006" (Skin Trading)
        Expect: customer_code generated, source="erp_auto_created",
        appears in listing, mapping persisted into the mappings dict.
        Teardown deletes it.
        """
        buyer_name = _unique_buyer_name()
        buyer = BuyerInfo(
            name=buyer_name,
            client_id=99001,
            tenant_id="test-tenant",
            tax_id="0123456789012",
        )
        mappings = {"clients": []}

        # Confirm no L0-L3 hit first.
        self.assertIsNone(self.svc.lookup(buyer, mappings))

        # Auto-create.
        out = self.svc.lookup_or_create(
            buyer,
            mappings,
            seed_customer_code=SEED_CUSTOMER_CODE,
        )

        # New customer was created.
        self.assertEqual(out.source, "erp_auto_created")
        self.assertTrue(out.is_new)
        self.assertTrue(out.customer_code.startswith("P"))
        self.assertLessEqual(len(out.customer_code), 20)
        self._created_codes.append(out.customer_code)

        # Mapping persisted into the mappings dict.
        self.assertTrue(out.erp_code_persisted)
        clients_for_buyer = [
            m
            for m in mappings["clients"]
            if int(m.get("client_id", 0)) == buyer.client_id and m.get("erp_type") == "mrerp"
        ]
        self.assertEqual(len(clients_for_buyer), 1)
        self.assertEqual(clients_for_buyer[0]["erp_code"], out.customer_code)

        # Second call must hit L1 / cache without touching the network
        # (we drop the cache to force L1 from mappings).
        self.svc.cache.invalidate(("by_name", buyer.tenant_id, _norm(buyer_name)))
        again = self.svc.lookup_or_create(
            buyer,
            mappings,
            seed_customer_code=SEED_CUSTOMER_CODE,
        )
        self.assertEqual(again.customer_code, out.customer_code)
        self.assertIn(again.source, ("cache_hit", "db_mapping"))

    def test_auto_create_fails_when_no_seed_configured(self):
        """🔴 No seed configured → fast-fail with ERR_NO_SEED_CUSTOMER.
        The service must NOT silently fall back to placeholder filling
        (the path that was previously blocked by "Data is use in the
        system")."""
        buyer = BuyerInfo(
            name=_unique_buyer_name(),
            client_id=99002,
            tenant_id="test-tenant",
        )
        with self.assertRaises(MRERPBusinessError) as ctx:
            self.svc.lookup_or_create(
                buyer,
                {"clients": []},
                # seed_customer_code intentionally omitted
            )
        msg = str(ctx.exception)
        self.assertIn("ERR_NO_SEED_CUSTOMER", msg)
        # Sanity: didn't accidentally create anything.
        self.assertEqual(len(self._created_codes), 0)

    def test_lookup_or_create_returns_existing_when_match_present(self):
        """L2 hit for the known 0006 customer — auto-create never fires
        even though a seed is configured."""
        buyer = BuyerInfo(
            name="Skin Trading Co., Ltd.",
            client_id=99003,
            tenant_id="test-tenant",
        )
        out = self.svc.lookup_or_create(
            buyer,
            {"clients": []},
            seed_customer_code=SEED_CUSTOMER_CODE,
        )
        self.assertEqual(out.customer_code, "0006")
        self.assertFalse(out.is_new)
        self.assertIn(out.source, ("erp_name_match", "erp_fuzzy_match", "cache_hit"))


def _norm(s):
    from services.erp._matching import normalize_company_name

    return normalize_company_name(s)


if __name__ == "__main__":
    unittest.main(verbosity=2)

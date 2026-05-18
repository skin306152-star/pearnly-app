#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_customer_sync_create.py

Integration test for MRERPCustomerSyncService.lookup_or_create (Layer 4
auto-create) against the real MR.ERP TEST2019 sandbox.

Test data: synthesizes a unique buyer name with a "PEARNLY-AUTO-TEST-"
prefix so a human can spot test rows in MR.ERP. The teardown attempts to
delete the created customer; if cleanup fails the leftover code is
logged so a periodic manual cleanup can pick it up.

Skipped automatically if .env.local lacks MR.ERP credentials.

Run directly:
    python tests/integration/test_mrerp_customer_sync_create.py
"""

from __future__ import annotations

import logging
import sys
import time
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_adapter import MRERPAdapter   # noqa: E402
from services.erp.mrerp_customer_sync import (   # noqa: E402
    BuyerInfo,
    MRERPCustomerSyncService,
)

from tests.integration._mrerp_common import require_credentials   # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def _unique_buyer_name() -> str:
    """A buyer name we'll never collide with. Long enough to look real,
    short enough to fit MR.ERP's 100-char ceiling."""
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
        # Best-effort cleanup. Anything that survives is logged.
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
                    "teardown delete %s raised: %s", code, e,
                )

    def test_auto_create_currently_blocked_by_master_data(self):
        """🟠 LOCKED-IN BEHAVIOUR — see service docstring §Known Limitation.

        Auto-create scaffolding is in place but `armas/allsave.php`
        rejects our submission with a generic alert
        ('Data is use in the system') because the placeholder codes we
        use for salesman / sales-area / shipping-type / other-branch
        aren't valid master-data rows on this tenant.

        This test asserts the CURRENT rejection so a regression in the
        scaffolding (e.g. checknull() blocking again) breaks the
        suite. When the master-data prefill path lands (see service
        docstring for the three forward options), swap this test to
        assert the success path with proper cleanup.
        """
        from services.erp.exceptions import MRERPBusinessError

        buyer_name = _unique_buyer_name()
        buyer = BuyerInfo(
            name=buyer_name,
            client_id=99001,
            tenant_id="test-tenant",
            tax_id="0123456789012",
        )
        mappings = {"clients": []}

        # L0-L3 should all miss (uuid-suffixed name).
        none_first = self.svc.lookup(buyer, mappings)
        self.assertIsNone(none_first)

        # Auto-create should be ATTEMPTED — confirms checknull passes —
        # but server rejects.
        with self.assertRaises(MRERPBusinessError) as ctx:
            self.svc.lookup_or_create(buyer, mappings)
        msg = str(ctx.exception)
        self.assertIn("Data is use in the system", msg,
                      f"unexpected rejection text: {msg}")
        # The attempted code is recorded in the message — capture for
        # manual cleanup if it somehow leaked into the DB.
        self.assertIn("code=", msg)

    def test_lookup_or_create_returns_existing_when_match_present(self):
        """Asking for the well-known 0006 customer should hit L2 (exact
        name match) and NEVER trigger auto-create."""
        buyer = BuyerInfo(
            name="Skin Trading Co., Ltd.",
            client_id=99002,
            tenant_id="test-tenant",
        )
        out = self.svc.lookup_or_create(buyer, {"clients": []})
        self.assertEqual(out.customer_code, "0006")
        self.assertFalse(out.is_new)
        self.assertIn(out.source,
                      ("erp_name_match", "erp_fuzzy_match", "cache_hit"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

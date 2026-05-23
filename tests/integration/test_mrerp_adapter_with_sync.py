#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_adapter_with_sync.py

End-to-end test for MRERPAdapter with master-data sync enabled
(P1-B Phase 5).

The history input deliberately OMITS the upfront client→erp_code
mapping. With `enable_master_data_sync=True`, the adapter's preflight
calls MRERPCustomerSyncService.lookup, which finds Skin Trading
Co., Ltd. by name (existing customer 0006 on TEST2019), enriches the
mappings dict, then proceeds with the normal upload.

Skipped automatically if .env.local lacks MR.ERP credentials.
"""

from __future__ import annotations

import logging
import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mrerp_xlsx_generator  # noqa: E402

from services.erp.mrerp_adapter import MRERPAdapter  # noqa: E402

from tests.integration._mrerp_common import (  # noqa: E402
    SCREENSHOT_ROOT,
    make_test_history,
    make_test_invoice_no,
    require_credentials,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


class AdapterWithSyncIntegrationTest(unittest.TestCase):

    def setUp(self):
        self.creds = require_credentials()
        self.invoice_no = make_test_invoice_no()
        self._original_derive = mrerp_xlsx_generator.derive_mrerp_invoice_no
        inv = self.invoice_no
        mrerp_xlsx_generator.derive_mrerp_invoice_no = lambda h: inv

        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
        self.shot_dir = SCREENSHOT_ROOT / f"with-sync-{int(time.time())}"

        self.adapter = MRERPAdapter(
            login_url=self.creds[0],
            username=self.creds[1],
            password=self.creds[2],
            comidyear=self.creds[3],
            seldb=self.creds[4],
            headless=True,
            screenshot_dir=self.shot_dir,
            # Master-data sync ON, auto-create OFF (the auto-create
            # path is blocked on this tenant by the
            # "Data is use in the system" rejection; see
            # mrerp_customer_sync._layer4_auto_create docstring).
            enable_master_data_sync=True,
            master_data_auto_create=False,
        )
        self.adapter.__enter__()
        self._cleanup_db_id = None

    def tearDown(self):
        try:
            mrerp_xlsx_generator.derive_mrerp_invoice_no = self._original_derive
        except Exception:
            pass
        try:
            if self._cleanup_db_id is not None:
                self.adapter.delete_invoice(self._cleanup_db_id)
            else:
                rec = self.adapter.search_invoice(self.invoice_no)
                if rec is not None:
                    self.adapter.delete_invoice(rec.db_row_id)
        except Exception as e:
            logging.warning("teardown delete failed: %s", e)
        try:
            self.adapter.__exit__(None, None, None)
        except Exception:
            pass

    def test_sync_resolves_customer_by_name_then_uploads(self):
        # History has buyer_name but NO matching client mapping.
        history = make_test_history(self.invoice_no)
        history["buyer_name"] = "Skin Trading Co., Ltd."
        history["buyer_tax"] = "0123456789012"  # OCR-style fake TIN

        # Empty mappings — adapter must enrich via sync.
        mappings = {
            "clients": [],
            "accounts": [],
            "taxes": [],
            "products": [],
        }

        result = self.adapter.upload_invoice_batch([history], mappings)

        self.assertEqual(result.total, 1)
        self.assertEqual(
            len(result.failed),
            0,
            f"unexpected failures: {[f.reasons for f in result.failed]}",
        )
        self.assertEqual(len(result.success), 1)
        self.assertEqual(result.success[0].invoice_no, self.invoice_no)

        # Sync should have written 0006 into the mappings dict.
        clients = mappings["clients"]
        client_codes = [m.get("erp_code") for m in clients if m.get("erp_type") == "mrerp"]
        self.assertIn(
            "0006",
            client_codes,
            f"sync did not enrich mappings; got {clients!r}",
        )

        # Verify the upload via listing then clean up.
        rec = self.adapter.search_invoice(self.invoice_no)
        self.assertIsNotNone(rec)
        self._cleanup_db_id = rec.db_row_id
        self.assertTrue(self.adapter.delete_invoice(rec.db_row_id))
        self._cleanup_db_id = None


if __name__ == "__main__":
    unittest.main(verbosity=2)

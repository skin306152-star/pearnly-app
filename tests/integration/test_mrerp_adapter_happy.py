#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_adapter_happy.py

End-to-end happy-path test against the real MR.ERP sandbox.

Sequence:
    1. login + select_company
    2. upload one PEARNLY-TEST-* invoice mapped to customer 0006
       (manually pre-created by Zihao 2026-05-18 — see
        docs/integrations/mrerp-known-facts.md §10.2)
    3. assert ImportResult is success
    4. search_invoice — assert row is visible in listing
    5. delete_invoice — assert verification passes
    6. teardown attempts cleanup even on intermediate failure

Skipped automatically if .env.local lacks MRERP_* credentials.

Run directly:
    python tests/integration/test_mrerp_adapter_happy.py
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

from services.erp import mrerp_xlsx_generator  # noqa: E402

from services.erp.mrerp_adapter import MRERPAdapter  # noqa: E402

from tests.integration._mrerp_common import (  # noqa: E402
    SCREENSHOT_ROOT,
    make_test_history,
    make_test_invoice_no,
    make_test_mappings,
    require_credentials,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


KNOWN_GOOD_CUSTOMER_CODE = "0006"  # Skin DB, Skin Trading Co., Ltd.


class HappyPathTest(unittest.TestCase):

    def setUp(self):
        self.creds = require_credentials()
        self.invoice_no = make_test_invoice_no()
        # Monkey-patch the date-based YYMMDD-NNN derivation so our
        # PEARNLY-TEST-XXXXXX label is what lands in the report xlsx. The
        # adapter's classifier reads the same function, so success/failed
        # buckets line up.
        self._original_derive = mrerp_xlsx_generator.derive_mrerp_invoice_no
        inv = self.invoice_no
        mrerp_xlsx_generator.derive_mrerp_invoice_no = lambda h: inv

        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
        self.shot_dir = SCREENSHOT_ROOT / f"happy-{int(time.time())}"

        self.adapter = MRERPAdapter(
            login_url=self.creds[0],
            username=self.creds[1],
            password=self.creds[2],
            comidyear=self.creds[3],
            seldb=self.creds[4],
            headless=True,
            screenshot_dir=self.shot_dir,
        )
        self.adapter.__enter__()
        self._cleanup_db_id = None

    def tearDown(self):
        try:
            mrerp_xlsx_generator.derive_mrerp_invoice_no = self._original_derive
        except Exception:
            pass
        # Best-effort cleanup of any test rows we created.
        try:
            if self._cleanup_db_id is not None:
                try:
                    self.adapter.delete_invoice(self._cleanup_db_id)
                except Exception as e:
                    logging.warning(
                        "teardown delete_invoice(%s) failed: %s",
                        self._cleanup_db_id,
                        e,
                    )
            else:
                # Search by invoice_no in case mid-flight failure left a row.
                try:
                    found = self.adapter.search_invoice(self.invoice_no)
                    if found is not None:
                        self.adapter.delete_invoice(found.db_row_id)
                except Exception as e:
                    logging.warning("teardown rescue search/delete failed: %s", e)
        finally:
            try:
                self.adapter.__exit__(None, None, None)
            except Exception:
                pass

    def test_happy_path(self):
        history = make_test_history(self.invoice_no)
        mappings = make_test_mappings(KNOWN_GOOD_CUSTOMER_CODE)

        result = self.adapter.upload_invoice_batch([history], mappings)

        self.assertEqual(result.total, 1, f"expected 1 input row; result={result.to_dict()}")
        self.assertEqual(
            len(result.failed),
            0,
            f"unexpected business failures: " f"{[f.reasons for f in result.failed]}",
        )
        self.assertEqual(len(result.success), 1)
        sr = result.success[0]
        self.assertEqual(sr.invoice_no, self.invoice_no)
        self.assertEqual(sr.mrerp_bill_no, f"SI{self.invoice_no}")
        self.assertTrue(result.all_success)
        self.assertGreater(result.elapsed_ms, 0)
        self.assertGreater(result.xlsx_size_bytes, 1000)

        record = self.adapter.search_invoice(self.invoice_no)
        self.assertIsNotNone(record, "row should appear in listing")
        self.assertTrue(record.db_row_id.isdigit())
        self.assertEqual(record.invoice_no, self.invoice_no)
        self._cleanup_db_id = record.db_row_id

        deleted = self.adapter.delete_invoice(record.db_row_id)
        self.assertTrue(deleted, "delete_invoice should verify removal")

        after = self.adapter.search_invoice(self.invoice_no)
        self.assertIsNone(after, "row should be gone after delete")
        self._cleanup_db_id = None


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_adapter_business_error.py

Verifies that the adapter classifies an unknown customer code as a
BUSINESS failure (return ImportResult with failed[]) rather than as a
technical or auth failure.

The chosen erp_code "99-NOT-EXIST-PEARNLY-001" is deliberately absent
from any MR.ERP master DB (Skin or Korn). The expected report contents:
    หมายเหตุ = "ไม่พบข้อมูลรหัสลูกค้า\nไม่พบข้อมูลรหัสลูกค้า (บิล)"

Skipped automatically if .env.local lacks MR.ERP credentials.

Run directly:
    python tests/integration/test_mrerp_adapter_business_error.py
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
    make_test_mappings,
    require_credentials,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


# 16 chars, fits under MR.ERP's 20-char customer_code ceiling, definitely
# not present in either the Skin (TEST2019) or Korn master DBs. Triggers
# `ไม่พบข้อมูลรหัสลูกค้า`, not the length-validation message that 21+
# characters produces.
UNKNOWN_CUSTOMER_CODE = "9999NONEXISTPNLY"


class BusinessErrorTest(unittest.TestCase):

    def setUp(self):
        self.creds = require_credentials()
        self.invoice_no = make_test_invoice_no()
        self._original_derive = mrerp_xlsx_generator.derive_mrerp_invoice_no
        inv = self.invoice_no
        mrerp_xlsx_generator.derive_mrerp_invoice_no = lambda h: inv

        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
        self.shot_dir = SCREENSHOT_ROOT / f"business-error-{int(time.time())}"

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

    def tearDown(self):
        try:
            mrerp_xlsx_generator.derive_mrerp_invoice_no = self._original_derive
        except Exception:
            pass
        try:
            self.adapter.__exit__(None, None, None)
        except Exception:
            pass

    def test_unknown_customer_returns_failed_row(self):
        history = make_test_history(self.invoice_no)
        mappings = make_test_mappings(UNKNOWN_CUSTOMER_CODE)

        result = self.adapter.upload_invoice_batch([history], mappings)

        self.assertEqual(result.total, 1)
        self.assertEqual(
            len(result.success),
            0,
            f"expected zero successes; got {result.success!r}",
        )
        self.assertEqual(len(result.failed), 1)
        fr = result.failed[0]
        self.assertEqual(fr.invoice_no, self.invoice_no)
        # MR.ERP returns "customer not found" + "customer (bill) not found"
        # as two newline-separated reasons in the same หมายเหตุ cell.
        reason_blob = "\n".join(fr.reasons)
        self.assertIn("ไม่พบข้อมูลรหัสลูกค้า", reason_blob)
        self.assertIsNotNone(
            fr.evidence_screenshot,
            "failed row should carry an evidence screenshot path",
        )
        self.assertEqual(
            fr.original.get("invoice_number"),
            self.invoice_no,
            "original invoice dict should round-trip",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

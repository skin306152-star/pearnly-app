#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_adapter_technical.py

Verifies that the adapter classifies a non-reachable host as a TECHNICAL
failure (MRERPTechnicalError after the configured retry budget) rather
than as auth or business.

Does NOT hit the real MR.ERP server — only sends Playwright at an
unrouteable IP that returns a connection error immediately. Therefore this
test does NOT require MRERP credentials and is safe to run in CI.

Run directly:
    python tests/integration/test_mrerp_adapter_technical.py
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

from services.erp.exceptions import (   # noqa: E402
    MRERPAuthError,
    MRERPBusinessError,
    MRERPTechnicalError,
)
from services.erp.mrerp_adapter import MRERPAdapter   # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


# RFC 5737 TEST-NET-1 reserved for documentation; never globally routed.
UNREACHABLE_HOST = "http://192.0.2.1:1"


class TechnicalErrorTest(unittest.TestCase):

    def test_login_against_unreachable_host_raises_technical_error(self):
        adapter = MRERPAdapter(
            login_url=UNREACHABLE_HOST,
            username="placeholder",
            password="placeholder",
            headless=True,
            retry_attempts=2,
            retry_delays_seconds=(0.1,),
        )
        # Shorten the per-request timeout so the test finishes quickly.
        adapter.DEFAULT_PAGE_TIMEOUT_MS = 3_000

        with adapter:
            t0 = time.time()
            with self.assertRaises(MRERPTechnicalError) as ctx:
                adapter.login()
            elapsed = time.time() - t0

        # Sanity check: we ran two attempts, separated by ~0.1s, each
        # with a ~3s timeout — well under 30s in total.
        self.assertLess(
            elapsed, 30.0,
            f"technical retries took {elapsed:.1f}s; "
            f"too slow for unit-test CI",
        )
        self.assertNotIsInstance(ctx.exception, MRERPAuthError)
        self.assertNotIsInstance(ctx.exception, MRERPBusinessError)


if __name__ == "__main__":
    unittest.main(verbosity=2)

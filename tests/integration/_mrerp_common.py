#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/_mrerp_common.py

Shared fixtures + helpers for MRERPAdapter integration tests.

These tests hit the real https://www.mrerp4sme.com sandbox; if credentials
or the server are unavailable the suite skips itself rather than fail.
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path
from typing import Any, Dict, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env.local")
except ImportError:
    pass


# Where integration-test screenshots land. Kept under docs/integrations/ so
# Zihao can browse them like the probe artifacts.
SCREENSHOT_ROOT = PROJECT_ROOT / "docs" / "integrations" / "screenshots" / "_tests"


def require_credentials() -> Tuple[str, str, str, str, str]:
    """Return (login_url, username, password, comidyear, seldb) or call
    unittest.SkipTest if any piece is missing.

    Opt-in gate: these tests hit the live MR.ERP site (create/delete customers,
    take screenshots), so plain ``unittest discover`` must NOT run them — even
    when credentials happen to be present in .env.local. Set
    PEARNLY_RUN_LIVE_MRERP=1 to actually run the live suite (TEST-RO-001)."""
    if os.environ.get("PEARNLY_RUN_LIVE_MRERP", "").strip() not in ("1", "true", "yes"):
        raise unittest.SkipTest(
            "live MR.ERP suite disabled by default; set PEARNLY_RUN_LIVE_MRERP=1 to run"
        )
    login_url = os.environ.get("MRERP_LOGIN_URL", "").strip()
    username = os.environ.get("MRERP_USERNAME", "").strip()
    password = os.environ.get("MRERP_PASSWORD", "").strip()
    comidyear = os.environ.get("MRERP_COMIDYEAR", "6").strip()
    seldb = os.environ.get("MRERP_SELDB", "1").strip()
    if not (login_url and username and password):
        raise unittest.SkipTest(
            "MR.ERP credentials missing in .env.local "
            "(MRERP_LOGIN_URL / MRERP_USERNAME / MRERP_PASSWORD)"
        )
    return login_url, username, password, comidyear, seldb


def make_test_invoice_no() -> str:
    """Per-test unique invoice number. PEARNLY-TEST- prefix lets a human
    spot test data in MR.ERP immediately and matches the cleanup pattern
    the probe established.

    Suffix is 4 hex chars (= 65 536 combos): keeps invoice_no at 17 chars
    (under MR.ERP's documented 18-char ceiling) and bill_no at 19 chars
    (under the 20-char ceiling — both limits were discovered when the
    initial 6-hex suffix hit `เลขที่ต้องไม่เกิน 18 ตัวอักษร` /
    `เลขที่บิลต้องไม่เกิน 20 ตัวอักษร` business errors).
    """
    return f"PEARNLY-TEST-{uuid.uuid4().hex[:4].upper()}"


def make_test_history(invoice_no: str) -> Dict[str, Any]:
    """One synthesised history dict in the shape mrerp_xlsx_generator expects."""
    return {
        "client_id": 99,
        "invoice_number": invoice_no,
        "invoice_date": "2026-05-18",
        "subtotal": "100.00",
        "vat": "7.00",
        "total_amount": "107.00",
        "items": [
            {
                "name": f"PEARNLY TEST ITEM ({invoice_no})",
                "qty": 1,
                "unit_price": 100.00,
                "amount": 100.00,
            }
        ],
    }


def make_test_mappings(erp_code: str) -> Dict[str, Any]:
    """Mapping table that ties our synthetic client_id=99 to the supplied
    MR.ERP customer code. Pass '0006' for the happy path, a deliberately
    non-existent code for the business-error path."""
    return {
        "clients": [
            {
                "erp_type": "mrerp",
                "client_id": 99,
                "erp_code": erp_code,
            }
        ],
        "accounts": [],
        "taxes": [],
        "products": [],
    }

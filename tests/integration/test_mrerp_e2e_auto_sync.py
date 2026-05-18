#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_e2e_auto_sync.py

Patch 2 (Zihao 2026-05-18 拍板) · End-to-end push integration with the
full master-data sync stack on:

    enable_master_data_sync   = True
    master_data_auto_create   = True
    seed_customer_code        = "0006"   (Skin Trading, pre-existing)
    seed_product_code         = "P001"   (Pepsi 500ml, pre-existing)

The history dict carries:
    - buyer_name : uuid-suffixed → NEVER matches L0-L3, forces L4 copy
    - items[]    : uuid-suffixed → NEVER matches L0-L3, forces L4 copy
    - everything else valid (date, amounts, tax, etc.)

Expected outcome:
    1. preflight master-data sync triggers customer auto-create
       → P{YYMM}XXXX customer appears in MR.ERP + mappings['clients']
         is enriched in place
    2. preflight master-data sync triggers product auto-create
       → P{YYMM}XXXX product appears in MR.ERP + mappings['products']
         is enriched in place
    3. validate_history_for_sales_credit no longer trips
       ERR_NO_CUSTOMER_MAPPING (the enrichment fixed it)
    4. xlsx generation + upload happen
    5. importpc.php returns "1" → ImportResult.all_success == True
    6. cleanup: delete the invoice (success expected) + attempt to
       delete the auto-created customer + product (best-effort, may
       orphan on test01 per the known alldel limitation)

Skipped automatically when .env.local lacks MR.ERP credentials.

This test is the formal proof that the C-1..C-7 + Decision 1+2 chain
hangs together end-to-end. If it ever regresses, the wiring broke.
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

import mrerp_xlsx_generator   # noqa: E402

from services.erp.mrerp_adapter import MRERPAdapter   # noqa: E402
from services.erp.mrerp_customer_sync import MRERPCustomerSyncService   # noqa: E402
from services.erp.mrerp_product_sync import MRERPProductSyncService   # noqa: E402

from tests.integration._mrerp_common import (   # noqa: E402
    SCREENSHOT_ROOT,
    make_test_invoice_no,
    require_credentials,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


SEED_CUSTOMER_CODE = "0006"
SEED_PRODUCT_CODE = "P001"


def _unique_buyer_name() -> str:
    return f"Pearnly E2E Buyer {uuid.uuid4().hex[:8].upper()} Co., Ltd."


def _unique_item_name() -> str:
    return f"Pearnly E2E Item {uuid.uuid4().hex[:8].upper()} v1"


class EndToEndAutoSyncTest(unittest.TestCase):
    """One big integration test — the full chain in one shot. We
    intentionally don't split into many small tests because each
    setUp would re-login + re-create rows, multiplying test01's
    orphan accumulation."""

    def setUp(self):
        self.creds = require_credentials()
        self.invoice_no = make_test_invoice_no()
        self._original_derive = mrerp_xlsx_generator.derive_mrerp_invoice_no
        inv = self.invoice_no
        mrerp_xlsx_generator.derive_mrerp_invoice_no = lambda h: inv

        SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
        self.shot_dir = SCREENSHOT_ROOT / f"e2e-auto-sync-{int(time.time())}"

        self.adapter = MRERPAdapter(
            login_url=self.creds[0],
            username=self.creds[1],
            password=self.creds[2],
            comidyear=self.creds[3],
            seldb=self.creds[4],
            headless=True,
            screenshot_dir=self.shot_dir,
            enable_master_data_sync=True,
            master_data_auto_create=True,
            seed_customer_code=SEED_CUSTOMER_CODE,
            seed_product_code=SEED_PRODUCT_CODE,
        )
        self.adapter.__enter__()
        self._cleanup_invoice_db_id = None
        self._cleanup_customer_codes: list = []
        self._cleanup_product_codes: list = []

    def tearDown(self):
        try:
            mrerp_xlsx_generator.derive_mrerp_invoice_no = self._original_derive
        except Exception:
            pass

        # Cleanup order: invoice (most important — easy to verify) →
        # auto-created product → auto-created customer. Each step is
        # best-effort; failures get logged but don't fail the test.
        try:
            if self._cleanup_invoice_db_id is not None:
                ok = self.adapter.delete_invoice(self._cleanup_invoice_db_id)
                logging.info("teardown delete invoice %s -> %s",
                             self._cleanup_invoice_db_id, ok)
            else:
                # Mid-flight failure may have left an invoice row;
                # try a search-and-delete rescue.
                try:
                    rec = self.adapter.search_invoice(self.invoice_no)
                    if rec is not None:
                        self.adapter.delete_invoice(rec.db_row_id)
                except Exception as e:
                    logging.warning("rescue delete invoice failed: %s", e)
        except Exception as e:
            logging.warning("teardown delete_invoice raised: %s", e)

        # Auto-created product/customer cleanup. delete_product /
        # delete_customer return False under test01 (the known
        # alldel.php permission limitation — see customer-copy-flow.md).
        # We log the codes either way so periodic manual cleanup picks
        # them up.
        try:
            psvc = MRERPProductSyncService(self.adapter)
            for code in self._cleanup_product_codes:
                ok = psvc.delete_product(code)
                logging.info("teardown delete product %s -> %s", code, ok)
                if not ok:
                    logging.warning(
                        "ORPHANED PRODUCT (please clean manually): %s",
                        code,
                    )
        except Exception as e:
            logging.warning("product cleanup raised: %s", e)

        try:
            csvc = MRERPCustomerSyncService(self.adapter)
            for code in self._cleanup_customer_codes:
                ok = csvc.delete_customer(code)
                logging.info("teardown delete customer %s -> %s", code, ok)
                if not ok:
                    logging.warning(
                        "ORPHANED CUSTOMER (please clean manually): %s",
                        code,
                    )
        except Exception as e:
            logging.warning("customer cleanup raised: %s", e)

        try:
            self.adapter.__exit__(None, None, None)
        except Exception:
            pass

    def test_full_auto_sync_push_lands_in_listing(self):
        buyer_name = _unique_buyer_name()
        item_name = _unique_item_name()
        history = {
            "client_id": 99001,
            "tenant_id": "e2e-tenant",
            "buyer_name": buyer_name,
            "buyer_tax": "0123456789012",
            "buyer_addr": "10/1 Pearnly Test Lane, Bangkok",
            "invoice_number": self.invoice_no,
            "invoice_date": "2026-05-18",
            "subtotal": "100.00",
            "vat": "7.00",
            "total_amount": "107.00",
            "items": [{
                "name": item_name,
                "qty": 1,
                "unit_price": 100.00,
                "amount": 100.00,
            }],
        }
        # No pre-stitched mappings. Sync must populate both clients
        # and products in-place during preflight.
        mappings = {
            "clients": [],
            "accounts": [],
            "taxes": [],
            "products": [],
        }

        logging.info(
            "E2E starting · invoice=%s · buyer=%s · item=%s",
            self.invoice_no, buyer_name, item_name,
        )
        result = self.adapter.upload_invoice_batch([history], mappings)

        # 1. ImportResult shape
        self.assertEqual(
            result.total, 1,
            f"unexpected total; result={result.to_dict()}",
        )
        self.assertEqual(
            len(result.failed), 0,
            f"unexpected failures: "
            f"{[(f.invoice_no, f.reasons) for f in result.failed]}",
        )
        self.assertEqual(len(result.success), 1)
        self.assertTrue(result.all_success)

        # 2. Customer mapping was enriched in-place by the sync
        #    preflight, and the new customer code follows the
        #    P{YYMM}XXXX namespace.
        client_entries = [
            m for m in mappings["clients"]
            if m.get("erp_type") == "mrerp"
            and int(m.get("client_id", 0)) == history["client_id"]
        ]
        self.assertEqual(
            len(client_entries), 1,
            f"customer mapping not enriched; clients={mappings['clients']}",
        )
        new_customer_code = client_entries[0]["erp_code"]
        self.assertTrue(
            new_customer_code.startswith("P"),
            f"customer code didn't follow auto-create namespace: "
            f"{new_customer_code!r}",
        )
        self.assertLessEqual(len(new_customer_code), 20)
        self._cleanup_customer_codes.append(new_customer_code)
        logging.info("auto-created customer: %s", new_customer_code)

        # 3. Product mapping was enriched in-place. The first (and
        #    only) item's normalized name should now map to a new
        #    code.
        from services.erp._matching import normalize_item_name
        product_entries = [
            m for m in mappings["products"]
            if m.get("erp_type") == "mrerp"
            and (m.get("item_name_norm") or "")
            == normalize_item_name(item_name)
        ]
        self.assertEqual(
            len(product_entries), 1,
            f"product mapping not enriched; products={mappings['products']}",
        )
        new_product_code = product_entries[0]["erp_code"]
        self.assertTrue(
            new_product_code.startswith("P"),
            f"product code didn't follow auto-create namespace: "
            f"{new_product_code!r}",
        )
        self.assertLessEqual(len(new_product_code), 20)
        self._cleanup_product_codes.append(new_product_code)
        logging.info("auto-created product: %s", new_product_code)

        # 4. SuccessRow echoes the input invoice + carries the
        #    SI-prefixed bill_no MR.ERP generated.
        sr = result.success[0]
        self.assertEqual(sr.invoice_no, self.invoice_no)
        self.assertEqual(sr.mrerp_bill_no, f"SI{self.invoice_no}")
        self.assertEqual(sr.original.get("invoice_number"), self.invoice_no)

        # 5. The invoice is actually queryable via listing — proves
        #    importpc=1 wasn't a phantom success.
        rec = self.adapter.search_invoice(self.invoice_no)
        self.assertIsNotNone(rec,
                             "invoice should appear in artran listing")
        self.assertEqual(rec.invoice_no, self.invoice_no)
        self._cleanup_invoice_db_id = rec.db_row_id

        logging.info(
            "E2E success · invoice db_row_id=%s · customer=%s · product=%s",
            rec.db_row_id, new_customer_code, new_product_code,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_customer_sync_unit.py

Offline unit tests for services/erp/mrerp_customer_sync.py — covers the
HTML parser + the L0/L1/L2/L3 lookup layers without touching the live
MR.ERP server.

The integration test that DOES hit MR.ERP lives in
tests/integration/test_mrerp_customer_sync.py.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_customer_sync import (   # noqa: E402
    BuyerInfo,
    CustomerSyncResult,
    MRERPCustomerSyncService,
    parse_armas_listing,
)


# Real HTML captured from MR.ERP TEST2019 DB on 2026-05-18 (scrubbed of
# session tokens; the only customer-bearing payload). Two real rows +
# the page footer that the parser must ignore.
SAMPLE_HTML = """<!DOCTYPE html><html><head><title>Mr.erp</title></head>
<body><div id="container"><div id="body"><div id="detail-box">
<div id="showdata">
  <p>
    <span>รหัสลูกค้า</span>
    <span>ชื่อประเภทลูกค้า</span>
    <span>คำนำหน้า</span>
    <span>ชื่อลูกค้า</span>
    <span>URA</span>
  </p>
  <p>
    <span>0006</span>
    <span>ลูกหนี้การค้า</span>
    <span>บริษัท</span>
    <span>Skin Trading Co., Ltd.</span>
    <span><a class="waitreview"></a>
      <span class="showura">
        <span><span>รายการ</span><span>รหัส</span><span>วันที่</span></span>
      </span>
    </span>
  </p>
  <p>
    <span>1-ฟ้าใหม่</span>
    <span>ลูกหนี้การค้า</span>
    <span></span>
    <span>ชื่อ test</span>
    <span><a class="waitreview"></a></span>
  </p>
</div>
</div></div>
<div id="footer">
  <p>
    <span>Username : </span>test01
    <span>Status : </span>User
    <span>Company : </span>1010-01-000006 บริษัท ทดสอบการใช้ จำกัด
    <span>Database Name : </span>TEST2019
  </p>
</div>
</div></body></html>
"""


class ParseListingTests(unittest.TestCase):

    def test_parses_two_real_rows(self):
        rows = parse_armas_listing(SAMPLE_HTML)
        self.assertEqual(len(rows), 2)

    def test_footer_is_ignored(self):
        rows = parse_armas_listing(SAMPLE_HTML)
        codes = [r.code for r in rows]
        self.assertNotIn("Username :", codes)
        self.assertNotIn("Database Name :", codes)

    def test_header_is_ignored(self):
        rows = parse_armas_listing(SAMPLE_HTML)
        codes = [r.code for r in rows]
        self.assertNotIn("รหัสลูกค้า", codes)

    def test_skin_trading_row_fields(self):
        rows = parse_armas_listing(SAMPLE_HTML)
        skin = next(r for r in rows if r.code == "0006")
        self.assertEqual(skin.type_name, "ลูกหนี้การค้า")
        self.assertEqual(skin.prefix, "บริษัท")
        self.assertEqual(skin.name, "Skin Trading Co., Ltd.")
        # Legal suffix stripped.
        self.assertEqual(skin.name_norm, "skin trading")

    def test_thai_row(self):
        rows = parse_armas_listing(SAMPLE_HTML)
        th = next(r for r in rows if r.code == "1-ฟ้าใหม่")
        self.assertEqual(th.name, "ชื่อ test")

    def test_empty_html(self):
        self.assertEqual(parse_armas_listing(""), [])


class LookupLayerTests(unittest.TestCase):
    """Exercise the layer cascade with a mock adapter that returns the
    SAMPLE_HTML fixture from page.content()."""

    def _make_service(self):
        mock_adapter = MagicMock()
        mock_adapter.login_url = "https://mock.example.com"
        mock_adapter.select_company.return_value = None

        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_page.content.return_value = SAMPLE_HTML
        mock_adapter._page = mock_page

        svc = MRERPCustomerSyncService(mock_adapter, customer_threshold=0.82)
        return svc, mock_adapter, mock_page

    def test_l1_db_mapping_hit_without_browser(self):
        svc, _adapter, page = self._make_service()
        buyer = BuyerInfo(name="Anything", client_id=99, tenant_id="t1")
        mappings = {"clients": [{
            "erp_type": "mrerp", "client_id": 99, "erp_code": "0006",
        }]}
        out = svc.lookup(buyer, mappings)
        self.assertIsNotNone(out)
        self.assertEqual(out.customer_code, "0006")
        self.assertEqual(out.source, "db_mapping")
        # L1 should NOT have touched the page.
        page.goto.assert_not_called()

    def test_l2_exact_name_hit(self):
        svc, _adapter, page = self._make_service()
        buyer = BuyerInfo(
            name="Skin Trading Co., Ltd.",
            client_id=200, tenant_id="t1",
        )
        out = svc.lookup(buyer, {"clients": []})
        self.assertIsNotNone(out)
        self.assertEqual(out.customer_code, "0006")
        self.assertEqual(out.source, "erp_name_match")
        self.assertEqual(out.confidence, 1.0)
        page.goto.assert_called_once()

    def test_l3_fuzzy_hit(self):
        svc, _adapter, _page = self._make_service()
        # Drop the legal suffix and lower-case — exact match would
        # already be 1.0 thanks to normalization, so this exercises
        # genuine fuzzy: introduce a typo.
        buyer = BuyerInfo(
            name="Skn Tradng Co., Ltd.", client_id=300, tenant_id="t1",
        )
        out = svc.lookup(buyer, {"clients": []})
        self.assertIsNotNone(out)
        self.assertEqual(out.customer_code, "0006")
        # The normalized form ("skn tradng" vs "skin trading") has a
        # ratio of 1 - 2/12 = 0.833 which is >= the 0.82 threshold.
        self.assertEqual(out.source, "erp_fuzzy_match")
        self.assertGreaterEqual(out.confidence, 0.82)

    def test_no_match_below_threshold(self):
        svc, _adapter, _page = self._make_service()
        buyer = BuyerInfo(
            name="Completely Different Manufacturing PLC",
            client_id=400, tenant_id="t1",
        )
        out = svc.lookup(buyer, {"clients": []})
        self.assertIsNone(out)

    def test_l0_cache_returns_without_browser_on_second_call(self):
        svc, _adapter, page = self._make_service()
        buyer = BuyerInfo(
            name="Skin Trading Co., Ltd.",
            client_id=500, tenant_id="t1",
        )
        svc.lookup(buyer, {"clients": []})
        page.goto.reset_mock()
        # Second call should hit L0 cache.
        out2 = svc.lookup(buyer, {"clients": []})
        self.assertEqual(out2.source, "cache_hit")
        page.goto.assert_not_called()

    def test_invalidate_clears_cache(self):
        svc, _adapter, page = self._make_service()
        buyer = BuyerInfo(
            name="Skin Trading Co., Ltd.",
            client_id=600, tenant_id="t1",
        )
        svc.lookup(buyer, {"clients": []})
        svc.invalidate()
        page.goto.reset_mock()
        svc.lookup(buyer, {"clients": []})
        # After invalidate, the second call must refetch the listing.
        page.goto.assert_called_once()

    def test_empty_buyer_returns_none(self):
        svc, _adapter, _page = self._make_service()
        self.assertIsNone(svc.lookup(BuyerInfo(name=""), {"clients": []}))


if __name__ == "__main__":
    unittest.main(verbosity=2)

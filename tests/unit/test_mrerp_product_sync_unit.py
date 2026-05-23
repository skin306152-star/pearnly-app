#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_product_sync_unit.py

Offline coverage for services/erp/mrerp_product_sync.py — parser +
lookup layer cascade with a mocked adapter (no MR.ERP traffic).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_product_sync import (  # noqa: E402
    ItemInfo,
    ProductSyncResult,
    MRERPProductSyncService,
    parse_stkmas_listing,
)

SAMPLE_HTML = """<!DOCTYPE html><html><body><div id="container"><div id="body">
<div id="detail-box">
<div id="showdata">
  <p>
    <span>รหัสสินค้า</span>
    <span>ชื่อสินค้า</span>
    <span>รหัสหมวดสินค้า</span>
    <span>ชื่อหมวดสินค้า</span>
    <span>URA</span>
  </p>
  <p>
    <span>P001</span>
    <span>Pepsi 500ml</span>
    <span>03-FIG</span>
    <span>สินค้าสำเร็จรูป</span>
    <span><a class="waitreview"></a>
      <span class="showura">
        <span><span>รายการ</span><span>รหัส</span><span>วันที่</span></span>
      </span>
    </span>
  </p>
  <p>
    <span>EXP-5340-01</span>
    <span>ค่าสอบบัญชี</span>
    <span>04-SER</span>
    <span>สินค้าบริการ/ค่าใช้จ่าย</span>
    <span><a class="waitreview"></a></span>
  </p>
</div>
</div></div>
<div id="footer">
  <p>
    <span>Username : </span>test01
    <span>Status : </span>User
    <span>Company : </span>1010
    <span>Database Name : </span>TEST2019
  </p>
</div>
</body></html>
"""


class ParseStkmasListingTests(unittest.TestCase):

    def test_parses_two_real_rows(self):
        rows = parse_stkmas_listing(SAMPLE_HTML)
        self.assertEqual(len(rows), 2)

    def test_footer_is_ignored(self):
        rows = parse_stkmas_listing(SAMPLE_HTML)
        codes = [r.code for r in rows]
        self.assertNotIn("Username :", codes)

    def test_header_is_ignored(self):
        rows = parse_stkmas_listing(SAMPLE_HTML)
        codes = [r.code for r in rows]
        self.assertNotIn("รหัสสินค้า", codes)

    def test_pepsi_row(self):
        rows = parse_stkmas_listing(SAMPLE_HTML)
        pep = next(r for r in rows if r.code == "P001")
        self.assertEqual(pep.name, "Pepsi 500ml")
        self.assertEqual(pep.category_code, "03-FIG")
        self.assertEqual(pep.category_name, "สินค้าสำเร็จรูป")
        # Normalized form drops case + punctuation.
        self.assertEqual(pep.name_norm, "pepsi 500ml")

    def test_empty_html(self):
        self.assertEqual(parse_stkmas_listing(""), [])

    def test_real_fixture_parses_all_rows(self):
        path = PROJECT_ROOT / "scripts" / "probe" / "_debug" / "product_listing_1779116422.html"
        if not path.exists():
            self.skipTest("real fixture missing (gitignored)")
        rows = parse_stkmas_listing(path.read_text(encoding="utf-8"))
        # The captured listing had 30 products — exact count matters.
        self.assertGreaterEqual(len(rows), 20)
        # All rows have non-empty code + name + name_norm.
        for r in rows:
            self.assertTrue(r.code, f"empty code: {r}")
            self.assertTrue(r.name, f"empty name: {r}")
            self.assertTrue(r.name_norm, f"empty name_norm: {r}")


class LookupLayerTests(unittest.TestCase):
    """Exercise the layer cascade with a mock adapter returning
    SAMPLE_HTML for listing requests."""

    def _make_service(self):
        adapter = MagicMock()
        adapter.login_url = "https://mock.example.com"
        adapter.select_company.return_value = None
        page = MagicMock()
        page.goto.return_value = None
        page.content.return_value = SAMPLE_HTML
        adapter._page = page
        svc = MRERPProductSyncService(adapter, product_threshold=0.90)
        return svc, adapter, page

    def test_l1_db_mapping_hit_without_browser(self):
        svc, _adapter, page = self._make_service()
        item = ItemInfo(name="Anything Goes", tenant_id="t1")
        mappings = {
            "products": [
                {
                    "erp_type": "mrerp",
                    "item_name": "Anything Goes",
                    "item_name_norm": "anything goes",
                    "erp_code": "P001",
                }
            ]
        }
        out = svc.lookup(item, mappings)
        self.assertIsNotNone(out)
        self.assertEqual(out.product_code, "P001")
        self.assertEqual(out.source, "db_mapping")
        page.goto.assert_not_called()  # L1 doesn't hit network

    def test_l2_exact_name_hit(self):
        svc, _adapter, _page = self._make_service()
        item = ItemInfo(name="Pepsi 500ml", tenant_id="t1")
        out = svc.lookup(item, {"products": []})
        self.assertIsNotNone(out)
        self.assertEqual(out.product_code, "P001")
        self.assertEqual(out.source, "erp_name_match")
        self.assertEqual(out.confidence, 1.0)

    def test_l3_fuzzy_with_typo(self):
        svc, _adapter, _page = self._make_service()
        # 1 char typo from "Pepsi 500ml" (9 chars normalized) — ratio
        # ~0.91 which is just above the 0.90 threshold.
        item = ItemInfo(name="Peosi 500ml", tenant_id="t1")
        out = svc.lookup(item, {"products": []})
        self.assertIsNotNone(out)
        self.assertEqual(out.product_code, "P001")
        self.assertEqual(out.source, "erp_fuzzy_match")
        self.assertGreaterEqual(out.confidence, 0.90)

    def test_no_match_returns_none(self):
        svc, _adapter, _page = self._make_service()
        item = ItemInfo(
            name="Totally Different Manufacturing Widget XR-9000",
            tenant_id="t1",
        )
        self.assertIsNone(svc.lookup(item, {"products": []}))

    def test_l0_cache_returns_without_browser_on_second_call(self):
        svc, _adapter, page = self._make_service()
        item = ItemInfo(name="Pepsi 500ml", tenant_id="t1")
        svc.lookup(item, {"products": []})
        page.goto.reset_mock()
        out2 = svc.lookup(item, {"products": []})
        self.assertEqual(out2.source, "cache_hit")
        page.goto.assert_not_called()

    def test_empty_item_returns_none(self):
        svc, _adapter, _page = self._make_service()
        self.assertIsNone(svc.lookup(ItemInfo(name=""), {"products": []}))

    def test_lookup_or_create_without_seed_raises(self):
        from services.erp.exceptions import MRERPBusinessError

        svc, _adapter, _page = self._make_service()
        item = ItemInfo(name="brand-new uuid product 9c8b7a", tenant_id="t1")
        with self.assertRaises(MRERPBusinessError) as ctx:
            svc.lookup_or_create(item, {"products": []})
        self.assertIn("ERR_NO_SEED_PRODUCT", str(ctx.exception))


class UpsertMappingTests(unittest.TestCase):
    """The mapping-write logic is part of lookup_or_create; isolate it
    here so we don't need the auto-create flow to exercise it."""

    def test_inserts_new_mapping(self):
        adapter = MagicMock()
        adapter._page = MagicMock()
        svc = MRERPProductSyncService(adapter)
        mappings = {"products": []}
        svc._upsert_mapping(
            mappings,
            ItemInfo(name="Pepsi 500ml", tenant_id="t1"),
            "P001",
        )
        self.assertEqual(len(mappings["products"]), 1)
        self.assertEqual(mappings["products"][0]["erp_code"], "P001")
        self.assertEqual(
            mappings["products"][0]["item_name_norm"],
            "pepsi 500ml",
        )

    def test_updates_existing_mapping(self):
        adapter = MagicMock()
        adapter._page = MagicMock()
        svc = MRERPProductSyncService(adapter)
        mappings = {
            "products": [
                {
                    "erp_type": "mrerp",
                    "item_name": "Pepsi 500ml",
                    "item_name_norm": "pepsi 500ml",
                    "erp_code": "OLD",
                }
            ]
        }
        svc._upsert_mapping(
            mappings,
            ItemInfo(name="Pepsi 500ml", tenant_id="t1"),
            "P001",
        )
        self.assertEqual(len(mappings["products"]), 1)
        self.assertEqual(mappings["products"][0]["erp_code"], "P001")


if __name__ == "__main__":
    unittest.main(verbosity=2)

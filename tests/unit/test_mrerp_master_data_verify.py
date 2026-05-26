#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_master_data_verify.py

Guard tests for the P1 fail-safe name-verification (Zihao 2026-05-26 拍板).

Root cause (read-only prod DB diag 2026-05-26):
  - 16/17 erp_product_mappings 全映射到占位码 '123' → 商品行静默记到占位商品。
  - 客户自动建码撞码 → 个人买方被静默推到 บริษัท อิ๊กลู สตูดิโอ。
  共因 = 凭 code/mapping 复用就推 · 不复核名字。

Fix = 推送前用 MR.ERP listing 反查"将要推送的 code"的真名 · 跟买方/商品复核:
  - 不匹配         → MRERPBusinessError(ERR_*_NAME_MISMATCH)   · 用户数据错 · 不 retry
  - 无法确认/超时  → MRERPTechnicalError(ERR_*_VERIFY_UNAVAILABLE) · 技术错 · 可 retry · 不显示成功

These tests are fully offline: `_search_listing` is mocked, so no live MR.ERP.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import db  # noqa: E402,F401  (import first so db's re-export fully inits push_store · 避免 push_store 作入口的循环 import)

from services.erp.exceptions import (  # noqa: E402
    MRERPBusinessError,
    MRERPTechnicalError,
)
from services.erp.mrerp_customer_sync import (  # noqa: E402
    ListingCustomer,
    MRERPCustomerSyncService,
)
from services.erp.mrerp_product_sync import (  # noqa: E402
    ListingProduct,
    MRERPProductSyncService,
)


def _cust_svc():
    adapter = MagicMock()
    adapter.login_url = "https://mock.example.com"
    adapter._page = MagicMock()
    return MRERPCustomerSyncService(adapter)


def _prod_svc():
    adapter = MagicMock()
    adapter.login_url = "https://mock.example.com"
    adapter._page = MagicMock()
    return MRERPProductSyncService(adapter)


# ============================================================
# Customer verify_resolved_code
# ============================================================
class CustomerVerifyTests(unittest.TestCase):
    def test_name_match_returns_erp_name(self):
        svc = _cust_svc()
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(code="P26050007", type_name="", prefix="", name="ACME Co., Ltd."),
            ]
        )
        out = svc.verify_resolved_code("P26050007", "ACME Co., Ltd.")
        self.assertEqual(out, "ACME Co., Ltd.")

    def test_name_mismatch_raises_business(self):
        svc = _cust_svc()
        # 实测场景:解析出的码指向 อิ๊กลู สตูดิโอ · 买方却是别人。
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(
                    code="P26050029", type_name="", prefix="", name="บริษัท อิ๊กลู สตูดิโอ จำกัด"
                ),
            ]
        )
        with self.assertRaises(MRERPBusinessError) as ctx:
            svc.verify_resolved_code("P26050029", "นายสมชาย ใจดี (บุคคลธรรมดา)")
        self.assertEqual(ctx.exception.failed_rows[0]["reason_code"], "ERR_CUSTOMER_NAME_MISMATCH")
        self.assertIn("ERR_CUSTOMER_NAME_MISMATCH", str(ctx.exception))

    def test_search_technical_failure_raises_unavailable(self):
        svc = _cust_svc()
        svc._search_listing = MagicMock(side_effect=MRERPTechnicalError("listing timeout"))
        with self.assertRaises(MRERPTechnicalError) as ctx:
            svc.verify_resolved_code("P26050007", "ACME Co., Ltd.")
        self.assertIn("ERR_CUSTOMER_VERIFY_UNAVAILABLE", str(ctx.exception))

    def test_code_not_in_listing_raises_unavailable(self):
        svc = _cust_svc()
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(code="OTHER", type_name="", prefix="", name="Someone Else"),
            ]
        )
        with self.assertRaises(MRERPTechnicalError) as ctx:
            svc.verify_resolved_code("P26050007", "ACME Co., Ltd.")
        self.assertIn("ERR_CUSTOMER_VERIFY_UNAVAILABLE", str(ctx.exception))

    def test_empty_inputs_raise_unavailable(self):
        svc = _cust_svc()
        svc._search_listing = MagicMock(return_value=[])
        with self.assertRaises(MRERPTechnicalError):
            svc.verify_resolved_code("", "ACME")
        with self.assertRaises(MRERPTechnicalError):
            svc.verify_resolved_code("P1", "")
        svc._search_listing.assert_not_called()

    # ----- P2 税号优先 -----
    def test_tax_match_passes_despite_name_diff(self):
        # 税号一致 = 权威匹配 · 即便 listing 名字跟买方对不上也放行。
        svc = _cust_svc()
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(code="C1", type_name="", prefix="", name="完全不同的名字")
            ]
        )
        svc._fetch_customer_detail = MagicMock(
            return_value={"name": "完全不同的名字", "tax_id": "0105556789012"}
        )
        out = svc.verify_resolved_code("C1", "ACME Co., Ltd.", "0-1055-56789-01-2")
        self.assertEqual(out, "完全不同的名字")

    def test_tax_mismatch_raises_even_if_name_matches(self):
        # 同名不同税号 = 不同主体 · 必须拦(税号冲突压过名字匹配)。
        svc = _cust_svc()
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(code="C1", type_name="", prefix="", name="ACME Co., Ltd.")
            ]
        )
        svc._fetch_customer_detail = MagicMock(
            return_value={"name": "ACME Co., Ltd.", "tax_id": "9999999999999"}
        )
        with self.assertRaises(MRERPBusinessError) as ctx:
            svc.verify_resolved_code("C1", "ACME Co., Ltd.", "0105556789012")
        self.assertEqual(ctx.exception.failed_rows[0]["reason_code"], "ERR_CUSTOMER_NAME_MISMATCH")
        self.assertEqual(ctx.exception.failed_rows[0].get("conflict"), "tax_id")

    def test_tax_unreadable_degrades_to_name_match(self):
        # 详情页读不到 ERP 税号 → 不硬拦 · 降级名称复核(名字一致则放行)。
        svc = _cust_svc()
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(code="C1", type_name="", prefix="", name="ACME Co., Ltd.")
            ]
        )
        svc._fetch_customer_detail = MagicMock(
            return_value={"name": "ACME Co., Ltd.", "tax_id": ""}
        )
        out = svc.verify_resolved_code("C1", "ACME Co., Ltd.", "0105556789012")
        self.assertEqual(out, "ACME Co., Ltd.")

    def test_tax_detail_fetch_raises_degrades_to_name(self):
        # 读详情抛异常(selector 假设错/超时)→ 降级名称复核 · 绝不因此硬拦合法推送。
        svc = _cust_svc()
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(code="C1", type_name="", prefix="", name="ACME Co., Ltd.")
            ]
        )
        svc._fetch_customer_detail = MagicMock(side_effect=MRERPTechnicalError("detail nav fail"))
        out = svc.verify_resolved_code("C1", "ACME Co., Ltd.", "0105556789012")
        self.assertEqual(out, "ACME Co., Ltd.")

    def test_no_buyer_tax_skips_detail_fetch(self):
        # 买方没税号 → 不付出读详情的代价 · 纯名称复核。
        svc = _cust_svc()
        svc._search_listing = MagicMock(
            return_value=[
                ListingCustomer(code="C1", type_name="", prefix="", name="ACME Co., Ltd.")
            ]
        )
        svc._fetch_customer_detail = MagicMock()
        out = svc.verify_resolved_code("C1", "ACME Co., Ltd.")
        self.assertEqual(out, "ACME Co., Ltd.")
        svc._fetch_customer_detail.assert_not_called()


# ============================================================
# Product verify_resolved_code
# ============================================================
class ProductVerifyTests(unittest.TestCase):
    def test_name_match_returns_erp_name(self):
        svc = _prod_svc()
        svc._search_listing = MagicMock(
            return_value=[ListingProduct(code="P26050010", name="Matcha cream cheese cake")]
        )
        out = svc.verify_resolved_code("P26050010", "Matcha cream cheese cake")
        self.assertEqual(out, "Matcha cream cheese cake")

    def test_placeholder_123_mismatch_raises_business(self):
        svc = _prod_svc()
        # 实测场景:商品全 fallback / stale 映射到占位码 123 = สมุดฉีก。
        svc._search_listing = MagicMock(return_value=[ListingProduct(code="123", name="สมุดฉีก")])
        with self.assertRaises(MRERPBusinessError) as ctx:
            svc.verify_resolved_code("123", "CAKE : Red velvet cake ราคาส่ง ขนาด 3 ปอนด์")
        self.assertEqual(ctx.exception.failed_rows[0]["reason_code"], "ERR_PRODUCT_NAME_MISMATCH")

    def test_search_technical_failure_raises_unavailable(self):
        svc = _prod_svc()
        svc._search_listing = MagicMock(side_effect=MRERPTechnicalError("stkmas timeout"))
        with self.assertRaises(MRERPTechnicalError) as ctx:
            svc.verify_resolved_code("P26050010", "Matcha cake")
        self.assertIn("ERR_PRODUCT_VERIFY_UNAVAILABLE", str(ctx.exception))

    def test_code_not_in_listing_raises_unavailable(self):
        svc = _prod_svc()
        svc._search_listing = MagicMock(
            return_value=[ListingProduct(code="OTHER", name="Something")]
        )
        with self.assertRaises(MRERPTechnicalError) as ctx:
            svc.verify_resolved_code("P26050010", "Matcha cake")
        self.assertIn("ERR_PRODUCT_VERIFY_UNAVAILABLE", str(ctx.exception))


# ============================================================
# Adapter gate: _verify_resolved_master_data
# ============================================================
class AdapterVerifyGateTests(unittest.TestCase):
    def _adapter(self):
        from services.erp.mrerp_adapter import MRERPAdapter

        ad = MRERPAdapter(login_url="https://mock.example.com", username="u", password="p")
        ad._customer_sync = MagicMock()
        ad._product_sync = MagicMock()

        def cust_verify(code, buyer_name, buyer_tax_id=None):
            if code == "C-BAD":
                raise MRERPBusinessError(
                    "mismatch",
                    failed_rows=[{"reason_code": "ERR_CUSTOMER_NAME_MISMATCH"}],
                )
            if code == "C-UNAVAIL":
                raise MRERPTechnicalError("ERR_CUSTOMER_VERIFY_UNAVAILABLE")
            return "ok name"

        def prod_verify(code, item_name):
            if code in ("123", "P-BAD"):
                raise MRERPBusinessError(
                    "mismatch",
                    failed_rows=[{"reason_code": "ERR_PRODUCT_NAME_MISMATCH"}],
                )
            return "ok name"

        ad._customer_sync.verify_resolved_code.side_effect = cust_verify
        ad._customer_sync.customer_threshold = 0.82
        ad._product_sync.verify_resolved_code.side_effect = prod_verify
        ad._product_sync.product_threshold = 0.90
        return ad

    def _history(self, *, client_id, buyer_name, item_names):
        return {
            "client_id": client_id,
            "tenant_id": "t1",
            "buyer_name": buyer_name,
            "invoice_no": f"INV-{client_id}",
            "invoice_number": f"INV-{client_id}",
            "invoice_date": "2026-03-01",
            "items": [{"name": n} for n in item_names],
        }

    def _mappings(self):
        return {
            "clients": [
                {"erp_type": "mrerp", "client_id": 50, "erp_code": "C-OK"},
                {"erp_type": "mrerp", "client_id": 51, "erp_code": "C-BAD"},
                {"erp_type": "mrerp", "client_id": 52, "erp_code": "C-OK"},
                {"erp_type": "mrerp", "client_id": 53, "erp_code": "C-UNAVAIL"},
            ],
            "products": [
                {"erp_type": "mrerp", "item_name": "Good Widget", "erp_code": "P-OK"},
            ],
        }

    def test_clean_invoice_passes(self):
        ad = self._adapter()
        h = self._history(client_id=50, buyer_name="Buyer A", item_names=["Good Widget"])
        valid, failed = ad._verify_resolved_master_data([h], self._mappings())
        self.assertEqual(len(valid), 1)
        self.assertEqual(failed, [])

    def test_customer_mismatch_becomes_failed_row(self):
        ad = self._adapter()
        h = self._history(client_id=51, buyer_name="Buyer B", item_names=["Good Widget"])
        valid, failed = ad._verify_resolved_master_data([h], self._mappings())
        self.assertEqual(valid, [])
        self.assertEqual(len(failed), 1)
        self.assertIn("ERR_CUSTOMER_NAME_MISMATCH", failed[0].reasons)
        # 客户已定失败 · 不应再去查商品。
        ad._product_sync.verify_resolved_code.assert_not_called()

    def test_product_fallback_123_becomes_failed_row(self):
        ad = self._adapter()
        # 客户 OK(client 52→C-OK)· 商品 "Unmapped" 无映射 → fallback '123' → mismatch。
        h = self._history(client_id=52, buyer_name="Buyer C", item_names=["Unmapped Cake"])
        valid, failed = ad._verify_resolved_master_data([h], self._mappings())
        self.assertEqual(valid, [])
        self.assertEqual(len(failed), 1)
        self.assertIn("ERR_PRODUCT_NAME_MISMATCH", failed[0].reasons)

    def test_verify_unavailable_blocks_not_success(self):
        ad = self._adapter()
        h = self._history(client_id=53, buyer_name="Buyer D", item_names=["Good Widget"])
        valid, failed = ad._verify_resolved_master_data([h], self._mappings())
        self.assertEqual(valid, [])
        self.assertEqual(len(failed), 1)
        self.assertIn("ERR_CUSTOMER_VERIFY_UNAVAILABLE", failed[0].reasons)

    def test_mixed_batch_splits_valid_and_failed(self):
        ad = self._adapter()
        good = self._history(client_id=50, buyer_name="Buyer A", item_names=["Good Widget"])
        bad = self._history(client_id=51, buyer_name="Buyer B", item_names=["Good Widget"])
        valid, failed = ad._verify_resolved_master_data([good, bad], self._mappings())
        self.assertEqual([h["client_id"] for h in valid], [50])
        self.assertEqual(len(failed), 1)
        self.assertIn("ERR_CUSTOMER_NAME_MISMATCH", failed[0].reasons)


# ============================================================
# Retry classification + 4-lang friendly coverage
# ============================================================
class ClassificationAndI18nTests(unittest.TestCase):
    def test_name_mismatch_is_user_data_error(self):
        from services.erp.push_store import is_user_data_error

        self.assertTrue(is_user_data_error("... ERR_CUSTOMER_NAME_MISMATCH ..."))
        self.assertTrue(is_user_data_error("... ERR_PRODUCT_NAME_MISMATCH ..."))

    def test_verify_unavailable_is_not_user_data_error(self):
        from services.erp.push_store import is_user_data_error

        # 技术错 · 必须可 retry(但永远不显示成功)。
        self.assertFalse(is_user_data_error("... ERR_CUSTOMER_VERIFY_UNAVAILABLE ..."))
        self.assertFalse(is_user_data_error("... ERR_PRODUCT_VERIFY_UNAVAILABLE ..."))

    def test_friendly_catalog_has_4_langs(self):
        from services.erp.mrerp_business_friendly import SUPPORTED_LANGS, get_friendly

        for code in (
            "ERR_CUSTOMER_NAME_MISMATCH",
            "ERR_CUSTOMER_VERIFY_UNAVAILABLE",
            "ERR_PRODUCT_NAME_MISMATCH",
            "ERR_PRODUCT_VERIFY_UNAVAILABLE",
        ):
            for lang in SUPPORTED_LANGS:
                msg = get_friendly(code, lang)
                self.assertTrue(msg and msg != code, f"{code}/{lang} missing friendly text")


# ============================================================
# P3 自动创建闭环反查:建完调 verify · 冲突抛 / 不可用降级
# ============================================================
class AutoCreatePostVerifyTests(unittest.TestCase):
    def _cust_create_svc(self):
        from services.erp.mrerp_customer_sync import ListingCustomer as LC

        adapter = MagicMock()
        adapter.login_url = "https://mock.example.com"
        page = MagicMock()
        page.url = "https://mock.example.com/armas/allform.php"
        adapter._page = page
        adapter._session = MagicMock()
        adapter._session.dialogs = []
        svc = MRERPCustomerSyncService(adapter)
        svc._generate_customer_code = MagicMock(return_value="C-NEW")
        svc._copy_from_seed = MagicMock()
        svc._override_after_copy = MagicMock()
        svc.invalidate = MagicMock()
        svc._search_listing = MagicMock(
            return_value=[LC(code="C-NEW", type_name="", prefix="", name="ACME")]
        )
        return svc

    def test_autocreate_propagates_name_or_tax_conflict(self):
        from services.erp.mrerp_customer_sync import BuyerInfo

        svc = self._cust_create_svc()
        svc.verify_resolved_code = MagicMock(
            side_effect=MRERPBusinessError(
                "conflict", failed_rows=[{"reason_code": "ERR_CUSTOMER_NAME_MISMATCH"}]
            )
        )
        with self.assertRaises(MRERPBusinessError):
            svc._layer4_auto_create(BuyerInfo(name="ACME", tax_id="0105556789012"), "0006")

    def test_autocreate_swallows_verify_unavailable(self):
        from services.erp.mrerp_customer_sync import BuyerInfo

        svc = self._cust_create_svc()
        svc.verify_resolved_code = MagicMock(
            side_effect=MRERPTechnicalError("ERR_CUSTOMER_VERIFY_UNAVAILABLE")
        )
        res = svc._layer4_auto_create(BuyerInfo(name="ACME"), "0006")
        self.assertEqual(res.customer_code, "C-NEW")
        self.assertTrue(res.is_new)

    def test_autocreate_success_runs_verify(self):
        from services.erp.mrerp_customer_sync import BuyerInfo

        svc = self._cust_create_svc()
        svc.verify_resolved_code = MagicMock(return_value="ACME")
        res = svc._layer4_auto_create(BuyerInfo(name="ACME", tax_id="0105556789012"), "0006")
        self.assertEqual(res.customer_code, "C-NEW")
        svc.verify_resolved_code.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)

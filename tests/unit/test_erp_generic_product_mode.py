#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_erp_generic_product_mode.py

P1「开箱即用」守门测试(Zihao 2026-05-26 拍板) ·
商品「匹配优先 + 通用兜底 · 不自动建商品」。

锁住 4 个契约:
  1. generator:命中行用真码;不中行用通用码(配了 generic_product_code 才有);
     未配通用码 = 精确模式 = 不中返 None(老行为)。
  2. adapter 模式开关:config.generic_product_code 配了 → adapter.generic_product_code
     有值;未配 → None(精确模式)。
  3. verify gate 提速:一批 N 个商品行,命中的按真码逐个名复核,所有"不中"行
     共用通用码且**整批只验存在一次**(把 130 秒逐行反查降到秒级)。
  4. 精确模式(未配通用码)行为不变:不中行仍 fallback '123' 走名复核(必响亮失败)。

全程离线:_search_listing 被 mock,不连真 MR.ERP。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import db  # noqa: E402,F401  (先 import 让 push_store 完整初始化 · 防循环 import)

import mrerp_xlsx_generator as _gen  # noqa: E402
from services.erp.exceptions import MRERPTechnicalError  # noqa: E402
from services.erp.mrerp_product_sync import (  # noqa: E402
    ListingProduct,
    MRERPProductSyncService,
)


def _prod_svc():
    adapter = MagicMock()
    adapter.login_url = "https://mock.example.com"
    adapter._page = MagicMock()
    return MRERPProductSyncService(adapter)


# ============================================================
# 契约 1 · generator 通用码兜底
# ============================================================
class GeneratorGenericFallbackTests(unittest.TestCase):
    def _history(self):
        return {
            "invoice_no": "INV-1",
            "invoice_date": "2026-05-26",
            "items": [
                {"name": "Pepsi 500ml", "qty": 1, "unit_price": 10, "amount": 10},
                {
                    "name": "ครัวซองค์เนยสดโฮมเมด สูตรพิเศษ",
                    "qty": 2,
                    "unit_price": 50,
                    "amount": 100,
                },
            ],
        }

    def _mappings_with_one_match(self, generic=None):
        m = {
            "products": [
                # 只有 Pepsi 有真实映射 · 烘焙长描述没有
                {"erp_code": "P001", "item_name": "Pepsi 500ml", "item_name_norm": ""},
            ],
            "clients": [],
            "accounts": [],
            "taxes": [],
        }
        if generic is not None:
            m["_generic_product_code"] = generic
        return m

    def test_matched_uses_real_code_unmatched_uses_generic(self):
        rows = _gen.build_sales_credit_detail_rows(
            self._history(), self._mappings_with_one_match(generic="GEN-INCOME")
        )
        by_name = {r["item_name"]: r for r in rows}
        self.assertEqual(by_name["Pepsi 500ml"]["product_code"], "P001", "命中行应用真码")
        bakery = [v for k, v in by_name.items() if k.startswith("ครัวซอง")][0]
        self.assertEqual(bakery["product_code"], "GEN-INCOME", "不中行应用通用码")
        # 行描述原样保留(精准其所当精准的关键:明细不丢)
        self.assertTrue(bakery["item_name"].startswith("ครัวซอง"))

    def test_precise_mode_unmatched_stays_none(self):
        # 未配通用码 = 精确模式 = 老行为(不中返 None · 下游 '123')
        rows = _gen.build_sales_credit_detail_rows(
            self._history(), self._mappings_with_one_match(generic=None)
        )
        by_name = {r["item_name"]: r for r in rows}
        self.assertEqual(by_name["Pepsi 500ml"]["product_code"], "P001")
        bakery = [v for k, v in by_name.items() if k.startswith("ครัวซอง")][0]
        self.assertIsNone(bakery["product_code"], "精确模式不中行应保持 None(不变)")


# ============================================================
# 契约 2 · adapter 模式开关(经 build_mrerp_adapter)
# ============================================================
class AdapterGenericModeWiringTests(unittest.TestCase):
    def _base_cfg(self, **extra):
        cfg = {
            "system_url": "https://www.mrerp4sme.com",
            "username": "u",
            "password": "p",
            "comidyear": "6",
            "seldb": "1",
        }
        cfg.update(extra)
        return cfg

    def test_generic_code_set_enters_generic_mode(self):
        import erp_push

        adapter, err = erp_push.build_mrerp_adapter(
            self._base_cfg(generic_product_code="GEN-INCOME")
        )
        self.assertIsNone(err, f"构建失败:{err!r}")
        self.assertEqual(adapter.generic_product_code, "GEN-INCOME")

    def test_no_generic_code_is_precise_mode(self):
        import erp_push

        adapter, err = erp_push.build_mrerp_adapter(self._base_cfg())
        self.assertIsNone(err, f"构建失败:{err!r}")
        self.assertIsNone(adapter.generic_product_code, "未配通用码应为精确模式(None)")


# ============================================================
# 契约 3 · verify_code_exists 名字无关的存在性检查
# ============================================================
class VerifyCodeExistsTests(unittest.TestCase):
    def test_found_returns_name_no_name_match(self):
        svc = _prod_svc()
        svc._search_listing = MagicMock(
            return_value=[ListingProduct(code="GEN-INCOME", name="รายได้จากการขาย")]
        )
        # 行描述跟通用品名完全不像 · 但只要码在就通过(不做相似度)
        out = svc.verify_code_exists("GEN-INCOME")
        self.assertEqual(out, "รายได้จากการขาย")
        svc._search_listing.assert_called_once()

    def test_not_found_raises_technical(self):
        svc = _prod_svc()
        svc._search_listing = MagicMock(return_value=[ListingProduct(code="OTHER", name="x")])
        with self.assertRaises(MRERPTechnicalError) as ctx:
            svc.verify_code_exists("GEN-INCOME")
        self.assertIn("ERR_PRODUCT_VERIFY_UNAVAILABLE", str(ctx.exception))

    def test_empty_code_raises_technical(self):
        svc = _prod_svc()
        with self.assertRaises(MRERPTechnicalError):
            svc.verify_code_exists("")


# ============================================================
# 契约 3b · verify gate 提速:不中行共用通用码 · 整批只验存在一次
# ============================================================
class VerifyGateGenericCollapseTests(unittest.TestCase):
    def _adapter(self, generic_product_code):
        from services.erp.mrerp_adapter import MRERPAdapter

        a = MRERPAdapter(
            login_url="https://mock.example.com",
            username="u",
            password="p",
            generic_product_code=generic_product_code,
        )
        # 预置 mock sync 服务 · 避免懒创建去碰浏览器
        a._product_sync = MagicMock()
        a._customer_sync = MagicMock()
        return a

    def _history_3_items(self):
        return {
            "invoice_no": "INV-9",
            "invoice_date": "2026-05-26",
            "client_id": 0,  # 无客户映射 → 跳过客户复核 · 隔离商品路径
            "tenant_id": "t-1",
            "items": [
                {"name": "Pepsi 500ml", "qty": 1, "unit_price": 10, "amount": 10},
                {"name": "ครัวซองค์เนยสด A", "qty": 1, "unit_price": 20, "amount": 20},
                {"name": "เค้กช็อกโกแลต B", "qty": 1, "unit_price": 30, "amount": 30},
                {"name": "พายแอปเปิล C", "qty": 1, "unit_price": 40, "amount": 40},
            ],
        }

    def _mappings(self, generic):
        # 只有 Pepsi 命中真码 · 其余 3 个不中
        return {
            "products": [{"erp_code": "P001", "item_name": "Pepsi 500ml", "item_name_norm": ""}],
            "clients": [],
            "accounts": [],
            "taxes": [],
            "_generic_product_code": generic,
        }

    def test_generic_mode_verifies_generic_once_and_real_code_per_match(self):
        a = self._adapter(generic_product_code="GEN-INCOME")
        a._product_sync.verify_code_exists = MagicMock(return_value="รายได้จากการขาย")
        a._product_sync.verify_resolved_code = MagicMock(return_value="Pepsi 500ml")

        still_valid, failed = a._verify_resolved_master_data(
            [self._history_3_items()], self._mappings("GEN-INCOME")
        )
        self.assertEqual(len(failed), 0, f"不该有失败:{failed!r}")
        self.assertEqual(len(still_valid), 1)
        # 命中行(Pepsi)按真码名复核 1 次
        self.assertEqual(
            a._product_sync.verify_resolved_code.call_count,
            1,
            "命中真码应名复核 1 次(Pepsi)",
        )
        self.assertEqual(a._product_sync.verify_resolved_code.call_args[0][0], "P001", "用的是真码")
        # 3 个不中行共用通用码 · 整批只验存在 1 次(memo)· 这是 130s→秒级的核心
        self.assertEqual(
            a._product_sync.verify_code_exists.call_count,
            1,
            "3 个不中行应只验通用码存在 1 次(整批 memo)",
        )

    def test_precise_mode_unmatched_falls_back_to_123_name_verify(self):
        # 未配通用码 · 不中行仍走 '123' 名复核(老行为 · 必响亮失败)
        a = self._adapter(generic_product_code=None)
        a._product_sync.verify_code_exists = MagicMock(return_value="x")
        a._product_sync.verify_resolved_code = MagicMock(return_value="Pepsi 500ml")

        a._verify_resolved_master_data([self._history_3_items()], self._mappings(None))
        # 通用码存在检查从不被调(精确模式)
        a._product_sync.verify_code_exists.assert_not_called()
        # 第一个不中行(Pepsi 命中先过)→ 后续不中行用 '123' 名复核
        called_codes = [c.args[0] for c in a._product_sync.verify_resolved_code.call_args_list]
        self.assertIn("123", called_codes, "精确模式不中行应 fallback '123' 名复核")


if __name__ == "__main__":
    unittest.main(verbosity=2)

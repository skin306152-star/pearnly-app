#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门 · 商品复核容忍 MR.ERP 名称截断(2026-05-26 · 沙箱真账号实测复现)。

真 bug:泰式烘焙发票的商品行是长描述(名+规格+换行,100+ 字),MR.ERP 商品名
字段有长度上限 → 自动建档时被截断(只存前 ~40 字)。复核拿"完整发票名 vs 截断名"
算相似度恒 < 阈值(实测 0.30)→ ERR_PRODUCT_NAME_MISMATCH → 自动建出的长名商品
永远推不成。修:ERP 归一名是发票归一名的前缀且足够长 → 判同一商品放行。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_product_sync import (  # noqa: E402
    ListingProduct,
    MRERPProductSyncService,
    parse_stkmas_listing,  # noqa: F401  (keep import surface stable)
)
from services.erp.exceptions import MRERPBusinessError  # noqa: E402


class ProductVerifyTruncationTests(unittest.TestCase):
    def _svc(self):
        adapter = MagicMock()
        adapter.login_url = "https://mock.example.com"
        adapter._page = MagicMock()
        return MRERPProductSyncService(adapter, product_threshold=0.90)

    def test_truncated_erp_name_passes(self):
        """ERP 截断名是发票长名的前缀 → 复核放行(返回 ERP 真名)。"""
        svc = self._svc()
        full = (
            "CHEESE : Blueberry cheese pie ( Premium ) ราคา ส่ง ขนาด 3 ปอนด์\n"
            "เเยก ซอส / แยก ผล บลูเบ อรี่ / ตัด 10"
        )
        erp_trunc = "CHEESE : Blueberry cheese pie ( Prem"  # MR.ERP 截断版
        svc._search_listing = MagicMock(
            return_value=[ListingProduct(code="P26050100", name=erp_trunc)]
        )
        out = svc.verify_resolved_code("P26050100", full)
        self.assertEqual(out, erp_trunc)

    def test_genuinely_different_product_still_mismatches(self):
        """不同商品(非前缀)→ 仍然 ERR_PRODUCT_NAME_MISMATCH(防误放行)。"""
        svc = self._svc()
        svc._search_listing = MagicMock(
            return_value=[ListingProduct(code="P001", name="Pepsi 500ml")]
        )
        with self.assertRaises(MRERPBusinessError) as ctx:
            svc.verify_resolved_code("P001", "CHEESE : Blueberry cheese pie")
        self.assertIn("ERR_PRODUCT_NAME_MISMATCH", str(ctx.exception))

    def test_short_prefix_does_not_false_match(self):
        """ERP 名太短(< 8 归一字符)不走前缀放行 → 避免短码误命中。"""
        svc = self._svc()
        # erp "AB" 归一后很短 · 发票名以 "ab..." 开头但其实是别的商品
        svc._search_listing = MagicMock(return_value=[ListingProduct(code="X1", name="AB")])
        with self.assertRaises(MRERPBusinessError):
            svc.verify_resolved_code("X1", "ABsolute totally different widget")


if __name__ == "__main__":
    unittest.main(verbosity=2)

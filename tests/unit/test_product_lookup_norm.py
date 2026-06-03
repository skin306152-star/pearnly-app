#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门 · 自动建档商品映射能被 generator 解析(2026-05-26 normalizer 一致性修)。

抓的真 bug(沙箱真账号实测复现):自动建档 `_upsert_mapping` 存 item_name_norm 用
`normalize_item_name`(保留空格),而 `_resolve_product_code` 查表用
`_norm_product_name`(去空格)· 两套归一不一致 → 查不到 → 回退占位码 '123' →
fail-safe 复核 ERR_PRODUCT_NAME_MISMATCH · **自动建出来的商品永远推不成功**。
修:`_build_product_lookup` 同时按 item_name 现算的 _norm_product_name 双 key 入表 ·
保证 resolve 必命中。本测试锁定该一致性。
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_xlsx_generator import (  # noqa: E402
    _build_product_lookup,
    _resolve_product_code,
)
from services.erp._matching import normalize_item_name  # noqa: E402


class ProductLookupNormConsistencyTests(unittest.TestCase):
    def test_resolves_mapping_stored_with_normalize_item_name(self):
        """映射 item_name_norm 用 normalize_item_name 存(自动建档老写法)·
        resolve 仍必须命中到对应 erp_code(而非 None → 占位 123)。"""
        item = "Pearnly E2E Item A48379CA v1"
        mappings = {
            "products": [
                {
                    "erp_type": "mrerp",
                    "item_name": item,
                    # 老写法:带空格的 norm(与 generator 的去空格 norm 不一致)
                    "item_name_norm": normalize_item_name(item),
                    "erp_code": "P26050098",
                }
            ]
        }
        lookup = _build_product_lookup(mappings)
        self.assertEqual(_resolve_product_code(item, lookup), "P26050098")

    def test_resolves_when_only_item_name_present(self):
        """映射只有 item_name(无 item_name_norm)· 也必须解析到 erp_code。"""
        item = "CAKE : Matcha cream cheese cake ราคา ส่ง"
        mappings = {"products": [{"erp_type": "mrerp", "item_name": item, "erp_code": "P26050099"}]}
        lookup = _build_product_lookup(mappings)
        self.assertEqual(_resolve_product_code(item, lookup), "P26050099")

    def test_unknown_item_returns_none(self):
        """没映射的商品名 → None(让上层走占位/自动建)· 不误命中。"""
        mappings = {
            "products": [{"erp_type": "mrerp", "item_name": "Known Item", "erp_code": "P001"}]
        }
        lookup = _build_product_lookup(mappings)
        self.assertIsNone(_resolve_product_code("Totally Different Thing", lookup))


if __name__ == "__main__":
    unittest.main(verbosity=2)

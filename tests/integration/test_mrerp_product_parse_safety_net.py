#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_product_parse_safety_net.py · REFACTOR-WC

MR.ERP 商品清单解析 + 通用商品建议安全网 · 纯加测试不改业务 · 给 A 拆 mrerp_product_sync 当保险。

锁定 services/erp/mrerp_product_sync 的纯函数层 —— STKMAS allview.php 列表 HTML →
ListingProduct · 通用销售商品智能默认(开箱即用向导)· 结果序列化。

背景:A 的 mrerp_customer_sync mixin 拆分两度翻车(prod 502)· 已暂停高敏拆分转覆盖。
product_sync 是 customer_sync 的孪生(同 parse/_strip_tags/_extract_top_level_spans 模式)·
A 大概率接着拆它。本文件在拆之前先把纯层焊死(0 凭据 · 0 浏览器 · 0 DB · CI 真跑不 skip)·
现有 test_mrerp_product_sync 要真 sandbox + Playwright → CI 默认 skip,补不上这层。

suggest_generic_product_code 源码自带「纯函数 · 守门可测」注释 —— 它挑「销售收入」类商品
做向导默认,挑错 → 新公司默认商品码错 → 销售记错 GL 科目。本文件锁它的多语种命中 + 优先级。

覆盖维度(对应 loop「给 A 新拆模块补集成测试」):
  1. parse_stkmas_listing — 行解析 + 表头/残行/缺码跳过 + showdata 限域 + name_norm 落地
  2. suggest_generic_product_code — 多语种(泰/英/中)命中 · 名字优先于分类 · 缺码跳过 · 无命中 None
  3. ProductSyncResult.to_dict — 稳定键集(含 warnings)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_HEADER_CODE_LABEL = "รหัสสินค้า"  # 精确商品表头标签


def _load():
    try:
        import services.erp.mrerp_product_sync as mod
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"services.erp.mrerp_product_sync 不可 import:{e}")
    return mod


def _row(code, name, cat_code, cat_name):
    return (
        f"<p><span>{code}</span><span>{name}</span>"
        f"<span>{cat_code}</span><span>{cat_name}</span></p>"
    )


def _showdata(*rows):
    return '<div id="showdata">' + "".join(rows) + "</div>"


class ParseStkmasListingTest(unittest.TestCase):
    """parse_stkmas_listing · 商品列表 HTML → ListingProduct"""

    def setUp(self) -> None:
        self.m = _load()

    def test_valid_rows_parsed_with_fields(self) -> None:
        html = _showdata(
            _row("P001", "Widget A", "C1", "Hardware"),
            _row("P002", "Service B", "C2", "Services"),
        )
        rows = self.m.parse_stkmas_listing(html)
        self.assertEqual([r.code for r in rows], ["P001", "P002"])
        self.assertEqual(rows[0].name, "Widget A")
        self.assertEqual(rows[0].category_code, "C1")
        self.assertEqual(rows[0].category_name, "Hardware")

    def test_header_row_skipped(self) -> None:
        html = _showdata(
            _row(_HEADER_CODE_LABEL, "n", "c", "cn"),
            _row("P001", "Widget A", "C1", "Hardware"),
        )
        rows = self.m.parse_stkmas_listing(html)
        self.assertEqual([r.code for r in rows], ["P001"])

    def test_too_few_spans_skipped(self) -> None:
        html = _showdata(
            "<p><span>P9</span><span>two</span></p>",
            _row("P001", "Widget A", "C1", "Hardware"),
        )
        rows = self.m.parse_stkmas_listing(html)
        self.assertEqual([r.code for r in rows], ["P001"])

    def test_missing_code_or_name_skipped(self) -> None:
        html = _showdata(
            _row("", "NoCode", "C1", "Hardware"),
            _row("P007", "", "C1", "Hardware"),
            _row("P001", "Widget A", "C1", "Hardware"),
        )
        rows = self.m.parse_stkmas_listing(html)
        self.assertEqual([r.code for r in rows], ["P001"])

    def test_scoped_to_showdata_div(self) -> None:
        html = _showdata(_row("P001", "InScope", "C1", "Hardware")) + (
            '<div id="foot">' + _row("P999", "OutScope", "C9", "X") + "</div>"
        )
        rows = self.m.parse_stkmas_listing(html)
        self.assertEqual([r.code for r in rows], ["P001"])

    def test_name_norm_populated(self) -> None:
        rows = self.m.parse_stkmas_listing(_showdata(_row("P001", "Widget A", "C1", "Hardware")))
        self.assertTrue(rows[0].name_norm, "name_norm 应由 normalize_item_name 落地 · 供匹配用")

    def test_empty_html_returns_empty_list(self) -> None:
        self.assertEqual(self.m.parse_stkmas_listing(""), [])


class SuggestGenericProductCodeTest(unittest.TestCase):
    """suggest_generic_product_code · 多语种「销售收入」类命中 · 名字优先分类 · 无命中 None"""

    def setUp(self) -> None:
        self.suggest = _load().suggest_generic_product_code

    def test_english_name_match(self) -> None:
        out = self.suggest(
            [{"code": "P1", "name": "Office Supplies"}, {"code": "P2", "name": "Sales Revenue"}]
        )
        self.assertEqual(out, "P2")

    def test_case_insensitive(self) -> None:
        self.assertEqual(self.suggest([{"code": "P3", "name": "SERVICE income"}]), "P3")

    def test_thai_name_match(self) -> None:
        # รายได้ = 收入(沙箱真账号典型种子)
        self.assertEqual(self.suggest([{"code": "P4", "name": "รายได้จากการขาย"}]), "P4")

    def test_chinese_name_match(self) -> None:
        self.assertEqual(self.suggest([{"code": "P5", "name": "销售收入"}]), "P5")

    def test_category_name_fallback(self) -> None:
        # 商品名没命中 · 分类名命中 → 第二优先返回
        self.assertEqual(
            self.suggest([{"code": "P6", "name": "Widget", "category_name": "Revenue"}]),
            "P6",
        )

    def test_name_priority_over_category(self) -> None:
        # 名字命中优先于分类命中(全表先扫名字)
        out = self.suggest(
            [
                {"code": "PC", "name": "Box", "category_name": "Sales"},
                {"code": "PN", "name": "Service Fee", "category_name": "Misc"},
            ]
        )
        self.assertEqual(out, "PN")

    def test_no_match_returns_none(self) -> None:
        self.assertIsNone(
            self.suggest([{"code": "PX", "name": "Widget", "category_name": "Hardware"}])
        )

    def test_empty_list_returns_none(self) -> None:
        self.assertIsNone(self.suggest([]))

    def test_product_without_code_skipped(self) -> None:
        # 命中但无 code 不能选(返不出有效码)→ 继续找 · 找不到返 None
        self.assertIsNone(
            self.suggest([{"name": "Sales Revenue"}, {"code": "PY", "name": "random"}])
        )


class ProductSyncResultDictTest(unittest.TestCase):
    """ProductSyncResult.to_dict · 稳定键集(含 warnings · 契约防漏字段)"""

    def setUp(self) -> None:
        self.m = _load()

    def test_to_dict_key_set_stable(self) -> None:
        r = self.m.ProductSyncResult(product_code="P1", source="db_mapping", confidence=1.0)
        self.assertEqual(
            set(r.to_dict().keys()),
            {
                "product_code",
                "source",
                "confidence",
                "matched_name",
                "is_new",
                "erp_code_persisted",
                "warnings",
            },
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

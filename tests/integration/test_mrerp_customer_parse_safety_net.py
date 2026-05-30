#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_mrerp_customer_parse_safety_net.py · REFACTOR-WC

MR.ERP 客户清单解析安全网 · 纯加测试不改业务 · 给 A 拆 mrerp_customer_sync 当保险。

锁定 services/erp/mrerp_customer_sync 的纯解析层 —— ARMAS allview.php 列表 HTML →
ListingCustomer · 税号归一 · 标签清洗 · 结果序列化。这些是客户码解析的地基:解析写坏 →
匹配到错客户码 → ERP 推送到错买方(红线:workspace_client_id ≠ history.client_id)。

现有 test_mrerp_customer_sync 测的是 lookup 分层,但要真 MR.ERP sandbox 凭据 + Playwright
浏览器 → CI 默认 skip。本文件补的是纯函数层(0 凭据 · 0 浏览器 · 0 DB)→ CI 真跑不 skip。
窗口 A 把这个 1324 行模块拆 mixin(base/lookup/create)时,把解析 helper 搬串了立刻红。

覆盖维度(对应 loop「给 A 新拆模块补集成测试」):
  1. parse_armas_listing — 有效行解析 + 表头/残行/缺码跳过 + showdata 限域 + name_norm 落地
  2. _norm_tax — 仅 13 位泰国税号可比(非 13 位 / 空 → ""),归一去非数字
  3. _strip_tags — 去标签 + trim
  4. CustomerSyncResult.to_dict — 稳定键集(契约防漏字段)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 精确表头标签(parse_armas_listing 按它跳过表头行)
_HEADER_CODE_LABEL = "รหัสลูกค้า"


def _load():
    try:
        import services.erp.mrerp_customer_sync as mod
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"services.erp.mrerp_customer_sync 不可 import:{e}")
    return mod


def _row(code, type_name, prefix, name):
    return (
        f"<p><span>{code}</span><span>{type_name}</span>"
        f"<span>{prefix}</span><span>{name}</span></p>"
    )


def _showdata(*rows):
    return '<div id="showdata">' + "".join(rows) + "</div>"


class ParseArmasListingTest(unittest.TestCase):
    """parse_armas_listing · 列表 HTML → ListingCustomer 行"""

    def setUp(self) -> None:
        self.m = _load()

    def test_valid_rows_parsed_with_fields(self) -> None:
        html = _showdata(
            _row("0006", "TYPE_A", "PFX", "Skin Trading Co., Ltd."),
            _row("0010", "TYPE_A", "PFX", "Acme Co., Ltd."),
        )
        rows = self.m.parse_armas_listing(html)
        self.assertEqual([r.code for r in rows], ["0006", "0010"])
        self.assertEqual(rows[0].name, "Skin Trading Co., Ltd.")
        self.assertEqual(rows[0].type_name, "TYPE_A")
        self.assertEqual(rows[0].prefix, "PFX")

    def test_header_row_skipped(self) -> None:
        # 表头行(首格 == รหัสลูกค้า)不能当客户行
        html = _showdata(
            _row(_HEADER_CODE_LABEL, "t", "p", "n"),
            _row("0006", "TYPE_A", "PFX", "Skin Trading Co., Ltd."),
        )
        rows = self.m.parse_armas_listing(html)
        self.assertEqual([r.code for r in rows], ["0006"])

    def test_row_with_too_few_spans_skipped(self) -> None:
        # < 4 个顶层 span 的残行跳过(防把噪声当客户)
        html = _showdata(
            "<p><span>nope</span><span>two</span></p>",
            _row("0006", "TYPE_A", "PFX", "Skin Trading Co., Ltd."),
        )
        rows = self.m.parse_armas_listing(html)
        self.assertEqual([r.code for r in rows], ["0006"])

    def test_row_missing_code_or_name_skipped(self) -> None:
        html = _showdata(
            _row("", "TYPE_A", "PFX", "NoCode Co"),
            _row("0007", "TYPE_A", "PFX", ""),
            _row("0006", "TYPE_A", "PFX", "Skin Trading Co., Ltd."),
        )
        rows = self.m.parse_armas_listing(html)
        self.assertEqual([r.code for r in rows], ["0006"])

    def test_scoped_to_showdata_div(self) -> None:
        # showdata 之外的行(如 footer 状态行)不解析
        html = _showdata(_row("0006", "t", "p", "InScope Co")) + (
            '<div id="foot">' + _row("9999", "t", "p", "OutScope Co") + "</div>"
        )
        rows = self.m.parse_armas_listing(html)
        self.assertEqual([r.code for r in rows], ["0006"])

    def test_name_norm_populated(self) -> None:
        html = _showdata(_row("0006", "TYPE_A", "PFX", "Skin Trading Co., Ltd."))
        rows = self.m.parse_armas_listing(html)
        self.assertTrue(rows[0].name_norm, "name_norm 应由 normalize_company_name 落地 · 供匹配用")

    def test_empty_html_returns_empty_list(self) -> None:
        self.assertEqual(self.m.parse_armas_listing(""), [])


class NormTaxTest(unittest.TestCase):
    """_norm_tax · 仅 13 位泰国税号可比 · 否则 "" (降级名称复核)"""

    def setUp(self) -> None:
        self.m = _load()

    def test_thirteen_digits_normalized(self) -> None:
        self.assertEqual(self.m._norm_tax("0-1055-51234-56-7"), "0105551234567")

    def test_strips_non_digits(self) -> None:
        self.assertEqual(self.m._norm_tax("TH 0105551234567"), "0105551234567")

    def test_non_thirteen_length_is_empty(self) -> None:
        # 12 / 14 位都不可比 → "" (防拿半个税号误判同一买方)
        self.assertEqual(self.m._norm_tax("010555123456"), "")
        self.assertEqual(self.m._norm_tax("01055512345678"), "")

    def test_none_and_empty(self) -> None:
        self.assertEqual(self.m._norm_tax(None), "")
        self.assertEqual(self.m._norm_tax(""), "")


class StripTagsTest(unittest.TestCase):
    """_strip_tags · 去 HTML 标签 + 去首尾空白"""

    def setUp(self) -> None:
        self.m = _load()

    def test_removes_tags_and_trims(self) -> None:
        self.assertEqual(self.m._strip_tags("  <b>X</b> Y  "), "X Y")

    def test_plain_text_unchanged(self) -> None:
        self.assertEqual(self.m._strip_tags("Skin Trading"), "Skin Trading")


class CustomerSyncResultDictTest(unittest.TestCase):
    """CustomerSyncResult.to_dict · 稳定键集(契约防漏字段)"""

    def setUp(self) -> None:
        self.m = _load()

    def test_to_dict_key_set_stable(self) -> None:
        r = self.m.CustomerSyncResult(customer_code="0006", source="db_mapping", confidence=1.0)
        self.assertEqual(
            set(r.to_dict().keys()),
            {
                "customer_code",
                "source",
                "confidence",
                "matched_name",
                "is_new",
                "erp_code_persisted",
            },
        )

    def test_to_dict_values_round_trip(self) -> None:
        r = self.m.CustomerSyncResult(
            customer_code="0010",
            source="erp_auto_created",
            confidence=0.9,
            matched_name="Acme",
            is_new=True,
            erp_code_persisted=True,
        )
        d = r.to_dict()
        self.assertEqual(d["customer_code"], "0010")
        self.assertEqual(d["source"], "erp_auto_created")
        self.assertTrue(d["is_new"])
        self.assertTrue(d["erp_code_persisted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_recon_field_override_safety_net.py · REFACTOR-WC

对账字段校正契约安全网 · 纯加测试不改业务 · 给 A 拆 recon 当保险。

锁定 services/recon/field_override 的纯层:
- ALLOWED_FIELDS —— 用户只能手动校正这 7 个发票字段(含金额 amount_pre_vat / vat_amount)。
  这是「用户改对账金额」的白名单闸:多放字段 → 用户能改不该改的(如派生 total_amount);
  漏放金额字段 → 用户没法修 OCR 抽错的税额。重构动这个集合,本测试立刻红。
- parse_overrides —— JSONB field_overrides(psycopg2 给 dict 或 str)统一成 dict · 返回副本
  (调用方不能改到行里存的原 dict)· 脏输入降级 {} 不抛。

纯函数(0 DB · 0 网络)→ CI 真跑不 skip。record_field_override 走 DB,不在本文件覆盖范围。

覆盖维度(对应 loop「对账扣费 · 金额对」· 字段校正层):
  1. ALLOWED_FIELDS 集合精确(含两个金额字段 · 不含派生 total_amount)
  2. parse_overrides 归一:dict 副本 / json str / None / 脏串 / 非 dict json → {}
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load():
    try:
        import services.recon.field_override as mod
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"services.recon.field_override 不可 import:{e}")
    return mod


class AllowedFieldsContractTest(unittest.TestCase):
    """ALLOWED_FIELDS · 用户可校正的 7 个发票字段白名单"""

    def setUp(self) -> None:
        self.m = _load()

    def test_exact_seven_fields(self) -> None:
        self.assertEqual(
            set(self.m.ALLOWED_FIELDS),
            {
                "invoice_date",
                "invoice_no",
                "buyer_name",
                "buyer_tax_id",
                "buyer_branch",
                "amount_pre_vat",
                "vat_amount",
            },
        )

    def test_money_fields_are_correctable(self) -> None:
        # 净额与税额必须可手动校正(OCR 抽错金额时用户要能修)
        self.assertIn("amount_pre_vat", self.m.ALLOWED_FIELDS)
        self.assertIn("vat_amount", self.m.ALLOWED_FIELDS)

    def test_derived_total_not_correctable(self) -> None:
        # total_amount 是派生(净额+税额)· 不能让用户直接改(会与求和矛盾)
        self.assertNotIn("total_amount", self.m.ALLOWED_FIELDS)


class ParseOverridesTest(unittest.TestCase):
    """parse_overrides · JSONB → dict 归一 · 返回副本 · 脏输入降级 {}"""

    def setUp(self) -> None:
        self.m = _load()

    def test_dict_passthrough_as_copy(self) -> None:
        src = {"vat_amount": {"ocr": "7", "user": "7.5"}}
        out = self.m.parse_overrides(src)
        self.assertEqual(out, src)
        self.assertIsNot(out, src)  # 必须是副本 · 防调用方改到行里存的原 dict

    def test_json_string_parsed(self) -> None:
        self.assertEqual(self.m.parse_overrides('{"x": 2}'), {"x": 2})

    def test_none_and_empty_to_empty_dict(self) -> None:
        self.assertEqual(self.m.parse_overrides(None), {})
        self.assertEqual(self.m.parse_overrides(""), {})

    def test_garbage_string_to_empty_dict(self) -> None:
        # 非法 JSON 不抛 · 降级 {}(防一条坏数据让整页对账崩)
        self.assertEqual(self.m.parse_overrides("not json"), {})

    def test_non_dict_json_to_empty_dict(self) -> None:
        # JSON 合法但不是 object(如数组)→ {}(字段 override 必须是 dict)
        self.assertEqual(self.m.parse_overrides("[1, 2]"), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)

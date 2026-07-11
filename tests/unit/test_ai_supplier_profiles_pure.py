#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_supplier_profiles_pure.py

供应商过账档案面板前端(Z3-b)纯函数守门:ai-supplier-profiles-render.js 走
ai-profile-panels-render.js 先例的 UMD 双导出,这里用真 node 直接 require 源文件断言
输出——不进浏览器,只测无 DOM 依赖的那一半逻辑(validateTaxIdRaw + 值域常量)。
node 缺失时跳过(本地/CI 均装了 node)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_MODULE = AI_DIR / "ai-supplier-profiles-render.js"


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ValidateTaxIdRawTests(unittest.TestCase):
    def test_exact_13_digits_accepted(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(_MODULE))});
            process.stdout.write(JSON.stringify(r.validateTaxIdRaw('0107561000013')));
            """)
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], "0107561000013")

    def test_separators_stripped_before_length_check(self):
        # 与后端 clean_tax_id 同口径:剥分隔符后仍是 13 位才算合法。
        out = _run_node(f"""
            const r = require({json.dumps(str(_MODULE))});
            process.stdout.write(JSON.stringify(r.validateTaxIdRaw('010-756-1000013')));
            """)
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], "0107561000013")

    def test_short_or_long_digit_strings_rejected(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(_MODULE))});
            process.stdout.write(JSON.stringify([
                r.validateTaxIdRaw('12345'), r.validateTaxIdRaw('01075610000135'),
                r.validateTaxIdRaw(''), r.validateTaxIdRaw(null),
            ]));
            """)
        for item in out:
            self.assertFalse(item["ok"])
            self.assertEqual(item["errKey"], "err_sp_tax_id_invalid")

    def test_non_digit_only_input_rejected(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(_MODULE))});
            process.stdout.write(JSON.stringify(r.validateTaxIdRaw('บริษัท เอบีซี')));
            """)
        self.assertFalse(out["ok"])
        self.assertEqual(out["errKey"], "err_sp_tax_id_invalid")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ValueDomainExposedTests(unittest.TestCase):
    def test_payment_and_item_type_values_match_backend_domain(self):
        # 与 services/ocr_history/posting_manual.py 的 _PAYMENT_VALUES/_ITEM_TYPE_VALUES 同源词汇
        # (展示层复制,非校验——真正的值域闸在后端)。
        out = _run_node(f"""
            const r = require({json.dumps(str(_MODULE))});
            process.stdout.write(JSON.stringify([r.PAYMENT_VALUES, r.ITEM_TYPE_VALUES, r.UNSET]));
            """)
        self.assertEqual(out[0], ["cash", "credit"])
        self.assertEqual(out[1], ["goods", "expense"])
        self.assertEqual(out[2], "")


if __name__ == "__main__":
    unittest.main()

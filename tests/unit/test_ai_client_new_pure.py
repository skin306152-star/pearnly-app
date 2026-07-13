# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_client_new_pure.py

MC1-b0(2026-07-13)· 建客户模态的税号直查:零 DOM 依赖的纯逻辑摘出到
static/ai/ai-client-new.js 顶部(taxDigits/mod11Check/shouldTriggerLookup),
node 直接 require 断言(同 test_ai_clients_pure.py 先例)。

覆盖四场景之一「mod-11 预检」——回填/查不到/超时三场景走的是主站现成端点
GET /api/workspace/tax-lookup(routes/workspace_routes.py::workspace_tax_lookup),
已有 tests/unit/test_workspace_routes_contract.py::TaxLookupBehaviorTests 覆盖
found/not_found,本文件补 mod11Check 与前端触发条件(shouldTriggerLookup),
超时场景见 test_workspace_tax_lookup_timeout.py。

mod11Check 口径来自 0105546015062(仓库既有测试夹具,tests/unit/
test_expense_line_l2.py 等已使用同一号码,已知过 mod-11)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_MODULE = json.dumps(str(AI_DIR / "ai-client-new.js"))

_VALID_TAX_ID = "0105546015062"  # 已知过 mod-11(仓库既有测试夹具)
_INVALID_TAX_ID = "0105546015061"  # 末位改一位 → 校验位不符


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class Mod11CheckTests(unittest.TestCase):
    def test_valid_tax_id_passes(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.mod11Check('{_VALID_TAX_ID}')));
            """)
        self.assertTrue(out)

    def test_checksum_mismatch_fails(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.mod11Check('{_INVALID_TAX_ID}')));
            """)
        self.assertFalse(out)

    def test_wrong_length_fails(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify([
                m.mod11Check('12345'), m.mod11Check(''), m.mod11Check(null),
            ]));
            """)
        self.assertEqual(out, [False, False, False])

    def test_strips_non_digits_before_checking(self):
        # 用户可能带连字符/空格粘贴(泰国常见排版:0-1055-46015-06-2)
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.mod11Check('0-1055-46015-06-2')));
            """)
        self.assertTrue(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ShouldTriggerLookupTests(unittest.TestCase):
    def test_triggers_on_valid_13_digits_not_yet_queried(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.shouldTriggerLookup('{_VALID_TAX_ID}', null)));
            """)
        self.assertTrue(out)

    def test_does_not_trigger_when_mod11_fails(self):
        # mod-11 不过 → 不自动查(只给黄字提示,§3 交互设计)
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.shouldTriggerLookup('{_INVALID_TAX_ID}', null)));
            """)
        self.assertFalse(out)

    def test_does_not_trigger_before_13_digits(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.shouldTriggerLookup('010554601', null)));
            """)
        self.assertFalse(out)

    def test_does_not_repeat_same_tax_id(self):
        # 防抖去重:同一税号已经查过就不再重复请求
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(
                m.shouldTriggerLookup('{_VALID_TAX_ID}', '{_VALID_TAX_ID}')
            ));
            """)
        self.assertFalse(out)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_client_archive_pure.py

EN-clients · 单客户档案页(ai-client-archive-render.js)零 DOM/零 i18n 依赖的那一半逻辑:
工单历史按账期倒序。画像/供应商两 tab 的表单逻辑复用 ai-profile.js(已有
test_ai_profile_pure.py 覆盖,不重测);HTML 拼装依赖 at()/AI.state/AI.format/AI.router,
不在 node 里独立可测,由 tests/e2e/_entryclose_verify.spec.js 真浏览器覆盖。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_RENDER = json.dumps(str(AI_DIR / "ai-client-archive-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SortOrdersByPeriodDescTests(unittest.TestCase):
    def test_sorts_descending_without_mutating_input(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const input = [{{period: '2569-01'}}, {{period: '2569-05'}}, {{period: '2569-03'}}];
            const sorted = r.sortOrdersByPeriodDesc(input);
            process.stdout.write(JSON.stringify([sorted, input]));
            """)
        sorted_out, original = out
        self.assertEqual([o["period"] for o in sorted_out], ["2569-05", "2569-03", "2569-01"])
        # 原数组顺序不被就地排序打乱(调用方 listOrders() 拿到的响应可能被别处复用)。
        self.assertEqual([o["period"] for o in original], ["2569-01", "2569-05", "2569-03"])

    def test_empty_and_missing_input(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([r.sortOrdersByPeriodDesc([]), r.sortOrdersByPeriodDesc(null)]));
            """)
        self.assertEqual(out, [[], []])


# 完整度(0% 画像 CTA 判据)已改由后端 GET tax-profile 出参权威给出,前端不再实现——
# 口径守门在 tests/unit/test_tax_profile_routes_contract.py 的 _profile_completeness 用例。


if __name__ == "__main__":
    unittest.main()

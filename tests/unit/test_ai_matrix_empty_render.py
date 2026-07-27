#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_matrix_empty_render.py

矩阵表格三条渲染分支的守门(2026-07-27):当期一项义务都没物化时,此前会画出一张
只剩「客户」一列的残缺表——比空态还难读。这里钉住:

  没有客户        → 既有的「还没有客户」空态(原样保留)
  有客户没有义务列 → 「这一期还没有义务记录」空态 + 两条能点的出路,且不出 <table>
  有客户有义务列   → 照旧出表格,不被空态误伤

ai-matrix-render.js 是浏览器 IIFE(挂 window.AI.matrixRender),node 侧喂 window/at
垫片后 require 真源文件跑——断言的选择器与 key 全来自真实产物,不是测试自己造的对象。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

# at() 垫片直接回原 key:空态文案有没有真进 HTML,靠 key 是否出现来断言(无词典依赖)。
PRELUDE = f"""
    global.window = global;
    global.at = (k) => k;
    require({json.dumps(str(AI_DIR / "ai-state.js"))});
    require({json.dumps(str(AI_DIR / "ai-router.js"))});
    require({json.dumps(str(AI_DIR / "ai-matrix-render.js"))});
    """

CLIENT = {"id": 1, "name": "บริษัท เอ", "missing_order": True, "profile_completeness": 0}


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class MatrixTableHtmlTests(unittest.TestCase):
    def _table(self, matrix):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(
                global.AI.matrixRender.tableHtml({json.dumps(matrix)}, 'zh')
            ));
            """)

    def test_no_obligation_columns_renders_empty_state_not_a_crippled_table(self):
        html = self._table({"period": "2569-07", "clients": [CLIENT], "obligation_codes": []})
        self.assertNotIn("<table", html)
        self.assertIn("emp_mx_noobl_t", html)
        self.assertIn("emp_mx_noobl_s", html)

    def test_empty_state_gives_two_clickable_ways_out(self):
        # 说清为什么空还不够:义务从画像来 → 客户档案;想直接干活 → 看板开单。
        html = self._table({"period": "2569-07", "clients": [CLIENT], "obligation_codes": []})
        self.assertIn('href="#/clients"', html)
        self.assertIn('href="#/board"', html)
        self.assertIn("emp_mx_noobl_btn", html)
        self.assertIn("emp_mx_noobl_alt", html)

    def test_missing_obligation_codes_field_is_treated_as_none(self):
        # 老缓存/降级响应可能整个字段都没有,与空数组同义,不该炸成残表。
        html = self._table({"period": "2569-07", "clients": [CLIENT]})
        self.assertIn("emp_mx_noobl_t", html)

    def test_clients_present_with_obligations_still_renders_the_table(self):
        html = self._table(
            {
                "period": "2569-07",
                "clients": [CLIENT],
                "obligation_codes": ["pp30"],
                "obligation_labels": {"pp30": {"zh": "增值税", "th": "ภ.พ.30"}},
                "cells": [{"client_id": 1, "obligation_code": "pp30", "badge": "pending_order"}],
            }
        )
        self.assertIn('class="mx-table"', html)
        self.assertNotIn("emp_mx_noobl_t", html)

    def test_no_clients_keeps_the_existing_empty_state(self):
        html = self._table({"period": "2569-07", "clients": [], "obligation_codes": []})
        self.assertIn("matrix_empty_t", html)
        self.assertNotIn("emp_mx_noobl_t", html)


if __name__ == "__main__":
    unittest.main()

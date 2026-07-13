#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_clients_pure.py

EN-clients · 客户目录(ai-clients-render.js)零 DOM/零 i18n 依赖的那一半逻辑:画像完整度
百分比换算、搜索匹配(名字+税号)、按客户过滤矩阵格子、当期义务计数(UI1 行内分层的
「当期义务 N 项」标签)。HTML 拼装/事件委托依赖 at()/AI.state,不在 node 里独立可测,
由 tests/e2e/_ui1_design_tokens_verify.spec.js 真浏览器覆盖(同 ai-vatcheck-render.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_RENDER = json.dumps(str(AI_DIR / "ai-clients-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CompletenessTests(unittest.TestCase):
    def test_percent_rounds_and_clamps_missing_to_zero(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.completenessPercent(0.995), r.completenessPercent(0), r.completenessPercent(null),
                r.completenessPercent(0.5), r.completenessPercent(1),
            ]));
            """)
        self.assertEqual(out, [100, 0, 0, 50, 100])

    def test_obligations_count_skips_not_evaluated(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const matrix = {{cells: [
                {{client_id: 1, obligation_code: 'pp30', badge: 'in_progress'}},
                {{client_id: 1, obligation_code: 'pnd1', badge: 'not_evaluated'}},
                {{client_id: 1, obligation_code: 'pnd3', badge: 'frozen'}},
                {{client_id: 2, obligation_code: 'pp30', badge: 'frozen'}},
            ]}};
            process.stdout.write(JSON.stringify([
                r.obligationsCount(matrix, 1), r.obligationsCount(matrix, 2),
                r.obligationsCount(matrix, 3), r.obligationsCount({{}}, 1),
            ]));
            """)
        self.assertEqual(out, [2, 1, 0, 0])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SearchMatchTests(unittest.TestCase):
    def test_matches_name_or_tax_id_case_insensitive(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const c = {{name: 'Sister Makeup', tax_id: '1234567890123'}};
            process.stdout.write(JSON.stringify([
                r.matchesSearch(c, 'sister'), r.matchesSearch(c, '789012'),
                r.matchesSearch(c, 'nope'), r.matchesSearch(c, ''), r.matchesSearch(c, '   '),
            ]));
            """)
        self.assertEqual(out, [True, True, False, True, True])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ClientBadgesTests(unittest.TestCase):
    def test_filters_matrix_cells_by_client_id(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const matrix = {{cells: [
                {{client_id: 1, obligation_code: 'pp30', badge: 'in_progress'}},
                {{client_id: 2, obligation_code: 'pp30', badge: 'frozen'}},
            ]}};
            process.stdout.write(JSON.stringify(r.clientBadges(matrix, 1)));
            """)
        self.assertEqual(out, [{"client_id": 1, "obligation_code": "pp30", "badge": "in_progress"}])

    def test_missing_cells_returns_empty(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.clientBadges({{}}, 1)));
            """)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()

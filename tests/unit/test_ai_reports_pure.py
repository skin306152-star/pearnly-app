#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_reports_pure.py

EN-clients · 跨客户报表中心(ai-reports-render.js)零 DOM/零 i18n 依赖的那一半逻辑:
按期间定位工单、筛出真有文件的交付物种类。报表本体(BS/PL/TB/影子底稿)复用既有
AI.financials/AI.shadow 渲染,不在本文件重拼,已由 test_ai_financials_pure.py/
test_ai_shadow_pure.py 覆盖。HTML 拼装依赖 at()/AI.state/AI.format,不在 node 里独立
可测,由 tests/e2e/_entryclose_verify.spec.js 真浏览器覆盖。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_RENDER = json.dumps(str(AI_DIR / "ai-reports-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class PickOrderForPeriodTests(unittest.TestCase):
    def test_picks_first_match_by_period(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            const orders = [{{id: 'a', period: '2569-04'}}, {{id: 'b', period: '2569-05'}}];
            process.stdout.write(JSON.stringify(r.pickOrderForPeriod(orders, '2569-05')));
            """)
        self.assertEqual(out, {"id": "b", "period": "2569-05"})

    def test_no_match_returns_null(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.pickOrderForPeriod([{{id: 'a', period: '2569-04'}}], '2569-05'),
                r.pickOrderForPeriod([], '2569-05'),
                r.pickOrderForPeriod(null, '2569-05'),
            ]));
            """)
        self.assertEqual(out, [None, None, None])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DownloadableDeliverablesTests(unittest.TestCase):
    def test_filters_to_has_file_true_in_kind_order(self):
        out = _run_node(f"""
            // ai-pkg-render.js 是 root 模式(root=globalThis in node)——require 它的
            // 副作用就会把 KIND_ORDER 挂上 global.AI.pkgRender,同 build-home-js.mjs
            // 里两文件的加载顺序(pkg-render 排在 reports-render 之前)。
            require({json.dumps(str(AI_DIR / "ai-pkg-render.js"))});
            const r = require({_RENDER});
            const deliverables = [
                {{kind: 'evidence_index', has_file: true}},
                {{kind: 'pp30_draft', has_file: true}},
                {{kind: 'bank_workpaper', has_file: false}},
            ];
            process.stdout.write(JSON.stringify(r.downloadableDeliverables(deliverables)));
            """)
        # KIND_ORDER = [pp30_draft, ledger_workpaper, bank_workpaper, missing_doc_memo,
        # evidence_index] — 结果必须按这个顺序,不是输入数组的顺序。
        self.assertEqual(out, ["pp30_draft", "evidence_index"])

    def test_empty_deliverables_returns_empty(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.downloadableDeliverables([])));
            """)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()

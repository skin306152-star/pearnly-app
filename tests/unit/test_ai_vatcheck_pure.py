#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_vatcheck_pure.py

N1 · 销项税报告三查(ai-vatcheck-render.js)零 DOM/零 i18n 依赖的那一半逻辑:
补零宽度推断(padWidth)/ 区间压缩(compressRanges/formatNumberRanges)/ 号型族
异常判定(familyHasIssues)/ 三查全绿判定(allClear)/ 单文件类型校验(validateFile)。
HTML 拼装那一半依赖 at()/AI.state/AI.format,不在 node 里独立可测,由
tests/e2e/_n1_vatcheck_mock.spec.js 真浏览器覆盖(同 ai-recon-render.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class PadWidthTests(unittest.TestCase):
    def test_picks_modal_digit_length(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.padWidth({{
                invoice_numbers: ['IV69/00512', 'IV69/00513', 'IV69/00514'],
            }})));
            """)
        self.assertEqual(out, 5)

    def test_zero_when_no_numeric_suffix(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.padWidth({{invoice_numbers: []}})));
            """)
        self.assertEqual(out, 0)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FormatNumberRangesTests(unittest.TestCase):
    def test_compresses_consecutive_runs_and_pads(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(
                r.formatNumberRanges([520, 521, 522, 561, 562], 5)
            ));
            """)
        self.assertEqual(out, "00520-00522, 00561-00562")

    def test_single_values_stay_single(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.formatNumberRanges([31], 2)));
            """)
        self.assertEqual(out, "31")

    def test_zero_width_leaves_numbers_unpadded(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.formatNumberRanges([3, 4, 5], 0)));
            """)
        self.assertEqual(out, "3-5")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FamilyHasIssuesTests(unittest.TestCase):
    def test_clean_family_has_no_issues(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.familyHasIssues({{
                missing: [], out_of_order: [], duplicates: [], format_anomalies: [],
            }})));
            """)
        self.assertFalse(out)

    def test_missing_flags_issue(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.familyHasIssues({{missing: [520]}})));
            """)
        self.assertTrue(out)

    def test_date_coded_missing_days_flags_issue(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.familyHasIssues({{missing_days: [31]}})));
            """)
        self.assertTrue(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AllClearTests(unittest.TestCase):
    def test_all_clear_when_no_issues_and_no_out_of_period(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.allClear({{
                sequence: {{families: [{{missing: [], out_of_order: []}}]}},
                period: {{out_of_period: []}},
            }})));
            """)
        self.assertTrue(out)

    def test_not_clear_when_a_family_has_missing(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.allClear({{
                sequence: {{families: [{{missing: [520]}}]}},
                period: {{out_of_period: []}},
            }})));
            """)
        self.assertFalse(out)

    def test_not_clear_when_out_of_period_present(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.allClear({{
                sequence: {{families: []}},
                period: {{out_of_period: [{{invoice_no: 'X'}}]}},
            }})));
            """)
        self.assertFalse(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ValidateFileTests(unittest.TestCase):
    def test_no_file_returns_error_key(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.validateFile(null)));
            """)
        self.assertEqual(out, {"ok": False, "errKey": "vatcheck_err_no_file"})

    def test_bad_extension_rejected(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify(r.validateFile({{name: 'report.docx'}})));
            """)
        self.assertEqual(out, {"ok": False, "errKey": "vatcheck_err_bad_type"})

    def test_pdf_and_xlsx_accepted(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-vatcheck-render.js"))});
            process.stdout.write(JSON.stringify([
                r.validateFile({{name: 'report.pdf'}}),
                r.validateFile({{name: 'report.xlsx'}}),
            ]));
            """)
        self.assertEqual(out, [{"ok": True}, {"ok": True}])


if __name__ == "__main__":
    unittest.main()

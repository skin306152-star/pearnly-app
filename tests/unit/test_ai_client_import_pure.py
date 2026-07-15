# -*- coding: utf-8 -*-
"""IN-0d · static/ai/ai-client-import-render.js 纯函数 + HTML 拼装测试(node)。

上半段(validateFile/chipClassForStatus/errKeyFor/previewCounts/resultCounts)零依赖,
直接 require 断言;下半段(previewTableHtml/resultCardHtml)依赖 at()/AI.state.esc,
node 里 stub global.at + global.AI(同 test_ai_client_pool_pure.py::
ReviewPoolStateMachineTests 的 global.window=global 先例),断言真出 HTML 字符串
(逐行 chip/reason/counts 都看得见,不是只测数据结构)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_MODULE = json.dumps(str(AI_DIR / "ai-client-import-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ValidateFileTests(unittest.TestCase):
    def test_no_file_rejected(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.validateFile(null)));
            """)
        self.assertEqual(out, {"ok": False, "errKey": "client_import_err_no_file"})

    def test_wrong_extension_rejected(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify(m.validateFile({{ name: 'clients.pdf' }})));
            """)
        self.assertEqual(out, {"ok": False, "errKey": "client_import_err_bad_type"})

    def test_xlsx_accepted(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify([
                m.validateFile({{ name: 'clients.xlsx' }}).ok,
                m.validateFile({{ name: 'clients.csv' }}).ok,
                m.validateFile({{ name: 'clients.xls' }}).ok,
            ]));
            """)
        self.assertEqual(out, [True, True, True])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ChipAndReasonKeyTests(unittest.TestCase):
    def test_chip_class_for_status(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify([
                m.chipClassForStatus('valid'), m.chipClassForStatus('created'),
                m.chipClassForStatus('skip'), m.chipClassForStatus('error'),
                m.chipClassForStatus('bogus'),
            ]));
            """)
        self.assertEqual(out, ["g", "g", "n", "b", "n"])

    def test_err_key_for_maps_dots_to_underscores(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            process.stdout.write(JSON.stringify([
                m.errKeyFor('workspace.tax_id_duplicate'),
                m.errKeyFor(''),
                m.errKeyFor(null),
            ]));
            """)
        self.assertEqual(
            out, ["err_workspace_tax_id_duplicate", "err_generic", "err_generic"]
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CountsTests(unittest.TestCase):
    def test_preview_counts_tallies_three_states(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            const preview = [
                {{ status: 'valid' }}, {{ status: 'valid' }},
                {{ status: 'skip' }}, {{ status: 'error' }},
            ];
            process.stdout.write(JSON.stringify(m.previewCounts(preview)));
            """)
        self.assertEqual(out, {"total": 4, "valid": 2, "skip": 1, "error": 1})

    def test_result_counts_tallies_three_states(self):
        out = _run_node(f"""
            const m = require({_MODULE});
            const results = [
                {{ status: 'created' }}, {{ status: 'created' }}, {{ status: 'created' }},
                {{ status: 'skip' }}, {{ status: 'error' }},
            ];
            process.stdout.write(JSON.stringify(m.resultCounts(results)));
            """)
        self.assertEqual(out, {"total": 5, "created": 3, "skip": 1, "error": 1})


def _at_stub():
    # 非恒等变换(模拟真有翻译):at(key,{n})=key+':'+n(能在断言里看到值被插值),同
    # test_ai_client_pool_pure.py 的 '[' + key + ']' 先例(证明真调用了 at,不是原样漏字符串)。
    return """
        global.window = global;
        global.at = function (key, vars) {
            return key + (vars && vars.n != null ? ':' + vars.n : '');
        };
        global.AI = { state: { esc: function (s) { return String(s == null ? '' : s); } } };
    """


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class PreviewTableHtmlTests(unittest.TestCase):
    def _render(self, preview_json: str) -> str:
        return _run_node(f"""
            {_at_stub()}
            require({_MODULE});
            const preview = {preview_json};
            process.stdout.write(JSON.stringify(global.AI.clientImportRender.previewTableHtml(preview)));
            """)

    def test_shows_row_name_and_tax_id(self):
        html = self._render(
            json.dumps([{"row_index": 0, "name": "ACME Co Ltd", "tax_id": "0105546015062", "status": "valid"}])
        )
        self.assertIn("ACME Co Ltd", html)
        self.assertIn("0105546015062", html)

    def test_valid_row_gets_green_chip(self):
        html = self._render(json.dumps([{"row_index": 0, "name": "ACME", "status": "valid"}]))
        self.assertIn('chip g', html)
        self.assertIn("client_import_status_valid", html)

    def test_skip_row_shows_neutral_chip_and_reason(self):
        html = self._render(
            json.dumps(
                [
                    {
                        "row_index": 1,
                        "name": "Dup Co",
                        "tax_id": "0105546015062",
                        "status": "skip",
                        "reason": "workspace.tax_id_duplicate",
                    }
                ]
            )
        )
        self.assertIn('chip n', html)
        self.assertIn("err_workspace_tax_id_duplicate", html)

    def test_error_row_shows_red_chip_and_reason(self):
        html = self._render(
            json.dumps(
                [{"row_index": 2, "name": "", "status": "error", "reason": "client_import.err_missing_name"}]
            )
        )
        self.assertIn('chip b', html)
        self.assertIn("err_client_import_err_missing_name", html)

    def test_counts_chip_row_shows_valid_skip_error_tallies(self):
        html = self._render(
            json.dumps(
                [
                    {"row_index": 0, "name": "A", "status": "valid"},
                    {"row_index": 1, "name": "B", "status": "valid"},
                    {"row_index": 2, "name": "C", "status": "skip", "reason": "workspace.tax_id_duplicate"},
                    {"row_index": 3, "name": "", "status": "error", "reason": "client_import.err_missing_name"},
                ]
            )
        )
        self.assertIn("client_import_preview_valid_n:2", html)
        self.assertIn("client_import_preview_skip_n:1", html)
        self.assertIn("client_import_preview_error_n:1", html)

    def test_confirm_button_disabled_when_zero_valid_rows(self):
        html = self._render(
            json.dumps(
                [{"row_index": 0, "name": "", "status": "error", "reason": "client_import.err_missing_name"}]
            )
        )
        self.assertIn('data-action="ci-confirm" disabled', html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ResultCardHtmlTests(unittest.TestCase):
    def _render(self, results_json: str) -> str:
        return _run_node(f"""
            {_at_stub()}
            require({_MODULE});
            const results = {results_json};
            process.stdout.write(JSON.stringify(global.AI.clientImportRender.resultCardHtml(results)));
            """)

    def test_shows_created_skip_error_counts(self):
        html = self._render(
            json.dumps(
                [
                    {"row_index": 0, "name": "A", "status": "created", "id": 1},
                    {"row_index": 1, "name": "B", "status": "created", "id": 2},
                    {"row_index": 2, "name": "C", "status": "skip", "reason": "workspace.tax_id_duplicate"},
                    {"row_index": 3, "name": "", "status": "error", "reason": "client_import.err_missing_name"},
                ]
            )
        )
        self.assertIn("client_import_result_created_n:2", html)
        self.assertIn("client_import_result_skip_n:1", html)
        self.assertIn("client_import_result_error_n:1", html)

    def test_created_row_gets_green_chip(self):
        html = self._render(json.dumps([{"row_index": 0, "name": "A", "status": "created", "id": 1}]))
        self.assertIn('chip g', html)
        self.assertIn("client_import_status_created", html)


if __name__ == "__main__":
    unittest.main()

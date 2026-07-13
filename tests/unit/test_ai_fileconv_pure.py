#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_fileconv_pure.py

K1b · 财务文件转换(ai-fileconv-render.js)零 DOM/零 i18n 依赖的那一半逻辑:
单文件类型校验(validateFile)/ doc_type→i18n key(docTypeKey)/ issue.kind→i18n key
(issueKindKey)。HTML 拼装那一半依赖 at()/AI.state/AI.format,不在 node 里独立可测,
由 tests/e2e/_k1b_fileconv_local.spec.js 真浏览器覆盖(同 ai-vatcheck-render.js 先例)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_RENDER = json.dumps(str(AI_DIR / "ai-fileconv-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ValidateFileTests(unittest.TestCase):
    def test_no_file_returns_error_key(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.validateFile(null)));
            """)
        self.assertEqual(out, {"ok": False, "errKey": "fileconv_err_no_file"})

    def test_unsupported_types_rejected(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.validateFile({{name: 'report.xlsx'}}),
                r.validateFile({{name: 'notes.txt'}}),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"ok": False, "errKey": "fileconv_err_bad_type"},
                {"ok": False, "errKey": "fileconv_err_bad_type"},
            ],
        )

    def test_pdf_and_images_accepted_case_insensitive(self):
        # K1c 起图片(jpg/png/webp)走 OCR 路,前端放行。
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.validateFile({{name: 'GL TTB.pdf'}}),
                r.validateFile({{name: 'REPORT.PDF'}}),
                r.validateFile({{name: 'scan.jpg'}}),
                r.validateFile({{name: 'stmt.PNG'}}),
                r.validateFile({{name: 'photo.webp'}}),
            ]));
            """)
        self.assertEqual(out, [{"ok": True}] * 5)

    def test_is_image_file_distinguishes_ocr_path(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.isImageFile({{name: 'scan.jpg'}}),
                r.isImageFile({{name: 'gl.pdf'}}),
                r.isImageFile(null),
            ]));
            """)
        self.assertEqual(out, [True, False, False])

    def test_rejected_statuses(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.isRejected('no_text_layer'),
                r.isRejected('ocr_incomplete'),
                r.isRejected('ocr_unavailable'),
                r.isRejected('ok'),
            ]));
            """)
        self.assertEqual(out, [True, True, True, False])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DocTypeKeyTests(unittest.TestCase):
    def test_known_types_map_to_keys(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.docTypeKey('gl_ledger'),
                r.docTypeKey('bank_statement'),
                r.docTypeKey('vat_report'),
                r.docTypeKey('generic_table'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                "fileconv_doctype_gl_ledger",
                "fileconv_doctype_bank_statement",
                "fileconv_doctype_vat_report",
                "fileconv_doctype_generic_table",
            ],
        )

    def test_unknown_type_falls_back_to_generic(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.docTypeKey('some_future_type')));
            """)
        self.assertEqual(out, "fileconv_doctype_generic_table")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class IssueKindKeyTests(unittest.TestCase):
    def test_known_kinds_map_to_keys(self):
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify([
                r.issueKindKey('gl_balance_chain'),
                r.issueKindKey('running_balance'),
                r.issueKindKey('footer_total'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                "fileconv_issue_gl_balance_chain",
                "fileconv_issue_running_balance",
                "fileconv_issue_footer_total",
            ],
        )

    def test_unknown_kind_passes_through_verbatim(self):
        # 引擎未来加新校验种类时,原样显示 kind 比错挂到别的文案更诚实。
        out = _run_node(f"""
            const r = require({_RENDER});
            process.stdout.write(JSON.stringify(r.issueKindKey('new_check')));
            """)
        self.assertEqual(out, "new_check")


if __name__ == "__main__":
    unittest.main()

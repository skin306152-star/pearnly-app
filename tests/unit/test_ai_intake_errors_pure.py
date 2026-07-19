#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pearnly AI 销项表单失败类型的确定性前端映射。"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class IntakeErrorKeyTests(unittest.TestCase):
    def _resolve(self, expression):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            process.stdout.write(JSON.stringify(r.resolveIntakeErrKey({expression})));
            """)
        return out

    def test_session_expiry(self):
        self.assertEqual(self._resolve("{status: 401}"), "intake_err_session")

    def test_wrong_entrance(self):
        self.assertEqual(
            self._resolve("{status: 403, code: 'authz.entrance_scope'}"),
            "intake_err_entrance",
        )

    def test_other_forbidden(self):
        self.assertEqual(
            self._resolve("{status: 403, code: 'authz.forbidden'}"), "intake_err_forbidden"
        )

    def test_network_failure(self):
        self.assertEqual(self._resolve("{status: null}"), "intake_err_network")

    def test_other_api_failure_uses_validation_copy(self):
        self.assertEqual(self._resolve("{status: 422}"), "intake_form_invalid")


if __name__ == "__main__":
    unittest.main()

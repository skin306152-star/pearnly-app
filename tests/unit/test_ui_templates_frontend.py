#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ui_templates_frontend.py

6 页面模板骨架(src/home/ui-templates.ts)的真 node 守门。

全站新屏/迁移屏对号入座套这 6 个之一,结构必须:.ui 作用域 + 模板原语(.pagehead/.panel),
slot 内容如实注入,向导步骤条 step/total 算对(第 N 步前点亮)。node 缺失时跳过。
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src" / "home" / "ui-templates.ts"

DRIVER = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
globalThis.window = {};
const mod = { exports: {} };
new Function('module', 'exports', 'require', code)(mod, mod.exports, require);
const { uiTpl } = mod.exports;
let fails = 0;
function ok(c, m) { if (!c) { console.error('FAIL ' + m); fails++; } }

const list = uiTpl.list({ title: 'TITLE_X', actions: 'ACT_X', tools: 'TOOL_X', table: 'TBL_X', pager: 'PG_X' });
ok(list.includes('class="ui"'), 'list .ui scope');
ok(list.includes('class="pagehead"'), 'list pagehead');
ok(list.includes('class="panel"'), 'list panel');
['TITLE_X', 'ACT_X', 'TOOL_X', 'TBL_X', 'PG_X'].forEach((s) => ok(list.includes(s), 'list slot ' + s));

const ov = uiTpl.overview({ title: 'T', band: 'BAND', quick: 'Q', recent: 'R' });
['BAND', 'Q', 'R'].forEach((s) => ok(ov.includes(s), 'overview slot ' + s));

const det = uiTpl.detail({ title: 'T', status: 'STAT', main: 'M', side: 'S' });
['STAT', 'M', 'S'].forEach((s) => ok(det.includes(s), 'detail slot ' + s));

const ent = uiTpl.entry({ title: 'T', image: 'IMG', form: 'FORM' });
['IMG', 'FORM'].forEach((s) => ok(ent.includes(s), 'entry slot ' + s));

const set = uiTpl.settings({ title: 'T', sections: 'SEC', footer: 'FOOT' });
['SEC', 'FOOT'].forEach((s) => ok(set.includes(s), 'settings slot ' + s));

const wiz = uiTpl.wizard({ title: 'T', step: 2, total: 4, body: 'BODY', prev: 'PREV', next: 'NEXT' });
ok((wiz.match(/class="dot/g) || []).length === 4, 'wizard 4 dots');
ok((wiz.match(/class="dot on"/g) || []).length === 2, 'wizard 2 active dots (step=2)');
ok((wiz.match(/class="seg/g) || []).length === 3, 'wizard 3 segs');
['BODY', 'PREV', 'NEXT'].forEach((s) => ok(wiz.includes(s), 'wizard slot ' + s));

if (fails) process.exit(1);
console.log('OK');
"""


class UiTemplatesFrontendTests(unittest.TestCase):
    def test_ui_templates_node(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        proc = subprocess.run(
            [node, "-e", DRIVER, str(SRC)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=(proc.stdout + proc.stderr))
        self.assertIn("OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()

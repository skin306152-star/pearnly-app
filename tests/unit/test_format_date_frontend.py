#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_format_date_frontend.py

共享日期格式化(src/home/format-date.ts)的真 node 守门。

formatDate 是全站唯一日期出口(显示/表格/CSV/PDF 全走它),历法默认佛历 พ.ศ.(公历年 +543)。
这里用 esbuild 把 TS 转出后在 node 内跑,断言:佛历默认、各样式、公历切换、空/非法输入。
node 缺失时跳过(本地/CI 均装了 node)。
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src" / "home" / "format-date.ts"

DRIVER = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
globalThis.window = {};
let store = {};
globalThis.localStorage = {
  getItem: (k) => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); },
};
const mod = { exports: {} };
new Function('module', 'exports', 'require', code)(mod, mod.exports, require);
const { formatDate, setCalendar, getCalendar } = mod.exports;
function eq(a, b, m) { if (a !== b) { console.error('FAIL ' + m + ' got=' + a + ' want=' + b); process.exit(1); } }
eq(getCalendar(), 'buddhist', 'default calendar buddhist');
eq(formatDate('2026-06-06'), '2569-06-06', 'buddhist YYYY-MM-DD');
eq(formatDate('2026-06-06', { style: 'DD/MM/YYYY' }), '06/06/2569', 'buddhist DD/MM/YYYY');
eq(formatDate('2026-06-06', { style: 'YYYY/MM/DD' }), '2569/06/06', 'buddhist YYYY/MM/DD');
setCalendar('gregorian');
eq(formatDate('2026-06-06'), '2026-06-06', 'gregorian YYYY-MM-DD');
eq(formatDate('2026-06-06', { calendar: 'buddhist' }), '2569-06-06', 'per-call override');
eq(formatDate(''), '', 'empty -> empty');
eq(formatDate('not a date'), '', 'invalid -> empty');
eq(formatDate(new Date(2026, 5, 6), { calendar: 'gregorian' }), '2026-06-06', 'Date input');
console.log('OK');
"""


class FormatDateFrontendTests(unittest.TestCase):
    def test_format_date_node_equivalence(self):
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_list_error_state_frontend.py

列表错误态共用件(src/home/list-error-state.ts)的真 node 守门。

四处列表面(对账中心「最近对账」/ 客户管理买方 / 客户管理账套主体 / 银行对账会话)
共用这一份脸。它必须同时给出三样,少一样用户就会把「取数失败」读成「我的数据没了」:
  ① 说这是失败(标题走调用方给的 key)② 说数据还在(共用 list-error-desc)
  ③ 给一条出路(重试按钮,带调用方事件委托认的 data-* 属性)
另断 XSS:标题/文案里的尖括号必须被转义(t() 的返回值也可能被别处写脏)。
node 缺失时跳过。
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src" / "home" / "list-error-state.ts"

DRIVER = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });

const DICT = {
  'rcx-hist-load-fail': '历史加载失败',
  'clients-error-title': '没能加载客户',
  'list-error-desc': '数据还在,是这次没取回来。',
  'list-retry': '重试',
  'xss-title': '<img src=x onerror=alert(1)>',
};
globalThis.t = (k) => DICT[k] !== undefined ? DICT[k] : k;
globalThis.escapeHtml = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
globalThis.window = {};

const mod = { exports: {} };
new Function('module', 'exports', 'require', code)(mod, mod.exports, require);
const { listErrorHtml } = mod.exports;
function ok(c, m) { if (!c) { console.error('FAIL ' + m); process.exit(1); } }

const html = listErrorHtml('clients-error-title', 'data-buyer-retry');
ok(html.includes('class="pu-error"'), '走共享设计系统 .pu-error');
ok(html.includes('data-state="error"'), '带机器可断的 data-state');
ok(html.includes('没能加载客户'), '标题按 key 出文案');
ok(html.includes('数据还在'), '说清数据没丢');
ok(html.includes('>重试</button>'), '给重试按钮');
ok(html.includes('data-buyer-retry="1"'), '按钮带调用方的委托属性');
ok(html.includes('pu-btn--primary'), '按钮走共享按钮件');

// 标题 key 是按面给的,不是写死一句「加载失败」
const h2 = listErrorHtml('rcx-hist-load-fail', 'data-rcx-hist-retry');
ok(h2.includes('历史加载失败') && h2.includes('data-rcx-hist-retry="1"'), 'key/属性都可换');
ok(!h2.includes('没能加载客户'), '两处标题不串');

// 文案脏了也不许变成注入点
const h3 = listErrorHtml('xss-title', 'data-x-retry');
ok(!h3.includes('<img'), '标题转义');
ok(h3.includes('&lt;img'), '标题转义成实体');

// 缺翻译时诚实回落成 key(不静默出空标题,空标题=没说失败)
const h4 = listErrorHtml('no-such-key', 'data-x-retry');
ok(h4.includes('no-such-key'), '缺 key 回落原 key,不出空标题');

console.log('OK');
"""


class ListErrorStateFrontendTests(unittest.TestCase):
    def test_list_error_html_node_behavior(self):
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

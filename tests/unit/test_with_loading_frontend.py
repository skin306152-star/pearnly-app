#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_with_loading_frontend.py

按钮即时反馈助手(src/home/with-loading.ts)的真 node 守门。

withLoading(btn, fn):点击 → 禁用 + .is-busy → 完成/失败必恢复。断言:
成功后状态复原、fn 抛错后仍复原(finally)、返回值透传、已 busy 的元素重入不被抢先恢复。
node 缺失时跳过。
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src" / "home" / "with-loading.ts"

DRIVER = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });

class HTMLElement {
  constructor() {
    this._cls = new Set();
    this._attr = {};
    this.classList = {
      add: (c) => this._cls.add(c),
      remove: (c) => this._cls.delete(c),
      contains: (c) => this._cls.has(c),
    };
  }
  setAttribute(k, v) { this._attr[k] = v; }
  removeAttribute(k) { delete this._attr[k]; }
}
class HTMLButtonElement extends HTMLElement { constructor() { super(); this.disabled = false; } }
globalThis.HTMLElement = HTMLElement;
globalThis.HTMLButtonElement = HTMLButtonElement;
globalThis.window = {};

const mod = { exports: {} };
new Function('module', 'exports', 'require', code)(mod, mod.exports, require);
const withLoading = globalThis.window.withLoading;
function ok(c, m) { if (!c) { console.error('FAIL ' + m); process.exit(1); } }

(async () => {
  // 成功路径:进行中置位 → 完成复原 + 返回值透传
  const b = new HTMLButtonElement();
  const p = withLoading(b, async () => {
    ok(b.disabled === true, 'busy: disabled');
    ok(b._cls.has('is-busy'), 'busy: is-busy class');
    ok(b._attr['aria-busy'] === 'true', 'busy: aria-busy');
    return 42;
  });
  const r = await p;
  ok(r === 42, 'return passthrough');
  ok(b.disabled === false, 'restored: disabled');
  ok(!b._cls.has('is-busy'), 'restored: class');
  ok(!('aria-busy' in b._attr), 'restored: aria-busy');

  // 失败路径:抛错仍复原(finally),且原样抛出
  const b2 = new HTMLButtonElement();
  let threw = false;
  try { await withLoading(b2, async () => { throw new Error('boom'); }); }
  catch (e) { threw = e.message === 'boom'; }
  ok(threw, 'error rethrown');
  ok(b2.disabled === false && !b2._cls.has('is-busy'), 'restored after error');

  // 保留调用方原 disabled:本就 disabled 的按钮跑完仍 disabled
  const b3 = new HTMLButtonElement();
  b3.disabled = true;
  await withLoading(b3, async () => {});
  ok(b3.disabled === true, 'preserves prior disabled');

  // 重入:已 busy 的元素不被内层抢先复原
  const b4 = new HTMLButtonElement();
  await withLoading(b4, async () => {
    await withLoading(b4, async () => {});
    ok(b4._cls.has('is-busy'), 'reentrant: outer still busy');
  });
  ok(!b4._cls.has('is-busy'), 'reentrant: outer restored');

  // null 安全:无元素也照常跑 fn
  ok((await withLoading(null, async () => 'x')) === 'x', 'null target safe');

  console.log('OK');
})();
"""


class WithLoadingFrontendTests(unittest.TestCase):
    def test_with_loading_node_behavior(self):
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

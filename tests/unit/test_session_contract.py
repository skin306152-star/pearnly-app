#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_session_contract.py

入口级会话隔离(src/home/session.ts)的 node 守门契约。

契约(高敏路径 · 2026-08-27):
  1. cowork/erp 各自独立 token 槽(mrpilot_token_cowork / mrpilot_token_erp),legacy main/pos
     保持 mrpilot_token;槽选择只认 pathname/canonical,绝不认共享 pearnly_entry。
  2. 写/清同步 window.token;set/clear 只动当前槽,绝不影响另一入口槽(cowork/erp 互不清)。
  3. 安全迁移:仅 JWT entry 精确匹配才收养 legacy token(cowork 接 main/cowork · erp 只接 erp);
     POS/main token 不得被 erp/cowork 收养。
  4. workspace(active client id)按入口分槽,避免标签页互改 X-Workspace-Client-Id。

node 缺失时跳过(matches test_ui_templates_frontend.py)。
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src" / "home" / "session.ts"

DRIVER = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
globalThis.window = {};
globalThis.location = { pathname: '', search: '' };
const mod = { exports: {} };
new Function('module', 'exports', 'require', code)(mod, mod.exports, require);
const S = mod.exports;
let fails = 0;
function ok(c, m) { if (!c) { console.error('FAIL ' + m); fails++; } else { console.log('ok ' + m); } }
function mkStore(init) {
  const s = new Map();
  if (init) Object.keys(init).forEach((k) => s.set(k, init[k]));
  return { getItem: (k) => (s.has(k) ? s.get(k) : null), setItem: (k, v) => s.set(k, String(v)), removeItem: (k) => s.delete(k), has: (k) => s.has(k), get: (k) => s.get(k) };
}
function setGlobal(store, pathname, search) {
  globalThis.localStorage = store;
  globalThis.location = { pathname: pathname || '', search: search || '' };
}
function mkTok(entry) {
  const p = JSON.stringify({ entry: entry || 'main', exp: 0 });
  const b = Buffer.from(p).toString('base64').replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
  return 'a.' + b + '.sig';
}

// 1) 槽选择:pathname/canonical 决定,pearnly_entry 不参与 cowork/erp 判定。
setGlobal(mkStore(), '/cowork', '');
ok(S.entry() === 'cowork', 'entry(/cowork)=cowork');
ok(S.tokenKey() === 'mrpilot_token_cowork', 'cowork token key');
ok(S.workspaceKey() === 'pearnly_active_workspace_client_id_cowork', 'cowork ws key');
setGlobal(mkStore(), '/erp', '');
ok(S.entry() === 'erp', 'entry(/erp)=erp');
ok(S.tokenKey() === 'mrpilot_token_erp', 'erp token key');
ok(S.workspaceKey() === 'pearnly_active_workspace_client_id_erp', 'erp ws key');
setGlobal(mkStore(), '/home', '');
ok(S.entry() === '', 'entry(/home)="" (legacy main)');
ok(S.tokenKey() === 'mrpilot_token', 'legacy token key stays mrpilot_token');
ok(S.workspaceKey() === 'pearnly_active_workspace_client_id', 'legacy ws key');
// pearnly_entry must NOT hijack the slot decision.
setGlobal(mkStore({ pearnly_entry: 'erp' }), '/cowork', '');
ok(S.entry() === 'cowork', 'pearnly_entry=erp cannot force /cowork into erp slot');
setGlobal(mkStore({ pearnly_entry: 'cowork' }), '/home', '');
ok(S.entry() === '', 'pearnly_entry=cowork cannot force /home into cowork slot');
// canonical query overrides bare /home.
setGlobal(mkStore(), '/home', '?canonical=cowork');
ok(S.entry() === 'cowork', 'canonical query wins on /home');

// 2) 写/清同步 window.token,只动当前槽,不碰另一入口槽。
setGlobal(mkStore(), '/cowork', '');
S.setToken('cowT');
ok(globalThis.window.token === 'cowT', 'window.token synced on cowork set');
ok(S.tokenKey() === 'mrpilot_token_cowork', 'cowork set writes its own slot');
setGlobal(mkStore({ mrpilot_token_cowork: 'cowT' }), '/cowork', '');
ok(S.getToken() === 'cowT', 'cowork getToken reads its own slot');
setGlobal(mkStore({ mrpilot_token_cowork: 'cowT' }), '/erp', '');
ok(S.getToken() === '', 'erp page must not read cowork slot (no bleed)');
setGlobal(mkStore({ mrpilot_token_cowork: 'cowT', mrpilot_token_erp: 'erpT' }), '/erp', '');
S.clearToken();
ok(!globalThis.localStorage.has('mrpilot_token_erp'), 'erp clear removes erp slot');
ok(globalThis.localStorage.has('mrpilot_token_cowork'), 'erp clear leaves cowork slot alone');
ok(globalThis.window.token === '', 'window.token cleared on erp clear');

// 3) 迁移收养:JWT entry 精确匹配才收养;POS/main 不得被收养。
setGlobal(mkStore({ mrpilot_token: mkTok('main') }), '/cowork', '');
ok(S.migrateLegacyToken() === true, 'cowork adopts main legacy');
ok(globalThis.localStorage.get('mrpilot_token_cowork') === mkTok('main'), 'cowork slot mirrors main');
ok(globalThis.localStorage.has('mrpilot_token'), 'legacy token preserved (not cleared)');
setGlobal(mkStore({ mrpilot_token: mkTok('cowork') }), '/cowork', '');
ok(S.migrateLegacyToken() === true, 'cowork adopts cowork legacy');
setGlobal(mkStore({ mrpilot_token: mkTok('pos') }), '/cowork', '');
ok(S.migrateLegacyToken() === false, 'cowork rejects pos legacy');
ok(!globalThis.localStorage.has('mrpilot_token_cowork'), 'pos token not adopted into cowork');
setGlobal(mkStore({ mrpilot_token: mkTok('cowork') }), '/erp', '');
ok(S.migrateLegacyToken() === false, 'erp rejects cowork legacy');
setGlobal(mkStore({ mrpilot_token: mkTok('erp') }), '/erp', '');
ok(S.migrateLegacyToken() === true, 'erp adopts erp legacy');
setGlobal(mkStore({ mrpilot_token: mkTok('main') }), '/erp', '');
ok(S.migrateLegacyToken() === false, 'erp rejects main legacy');
// 槽已有 token 时不覆盖、不迁移。
setGlobal(mkStore({ mrpilot_token_cowork: 'existing', mrpilot_token: mkTok('main') }), '/cowork', '');
ok(S.migrateLegacyToken() === false, 'cowork with existing slot token does not migrate');

if (fails) process.exit(1);
console.log('OK');
"""


class SessionContractTests(unittest.TestCase):
    def test_session_contract_node(self):
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_dms_erp_card_offline.py

小助手活性判定(src/home/erp-agent-liveness.ts)真 node 守门。

Express 靠会计电脑上的小助手写本地 DBF,小助手掉线时票只排队不落地。这张卡此前只看
endpoint.enabled,小助手关机也照写「已连接 · 自动推送」——会计据此以为票进了 Express。
判定拿不准时必须落「离线」,不能反过来(状态诚实红线:rows=0/blocked 绝不显示成功)。

node 缺失时跳过(本地/CI 均装了 node)。
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src" / "home" / "erp-agent-liveness.ts"
I18N = PROJECT_ROOT / "static" / "i18n-data.js"

DRIVER = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
globalThis.window = { setInterval: () => 0, clearInterval: () => {} };
const mod = { exports: {} };
new Function('module', 'exports', 'require', code)(mod, mod.exports, require);
const { isAgentOffline } = mod.exports;

function eq(got, want, msg) {
  if (got !== want) { console.error('FAIL ' + msg + ' got=' + got + ' want=' + want); process.exit(1); }
}
const ago = (ms) => new Date(Date.now() - ms).toISOString();
const express = (seen) => ({ adapter: 'express', config: seen === undefined ? {} : { agent_last_seen_at: seen } });

// MR.ERP 云端直连,没有小助手这回事 —— 不能因为缺心跳字段就被判离线。
eq(isAgentOffline({ adapter: 'mrerp', config: {} }), false, 'mrerp never offline');
eq(isAgentOffline({ adapter: 'mrerp' }), false, 'mrerp without config');

eq(isAgentOffline(express(ago(60000))), false, 'fresh heartbeat 1min -> online');
eq(isAgentOffline(express(ago(179000))), false, 'just inside 3min window -> online');
eq(isAgentOffline(express(ago(181000))), true, 'just outside 3min window -> offline');
eq(isAgentOffline(express(ago(3600000))), true, 'stale 1h -> offline');

// 小助手右键退出时主动上报下线,服务端把时间戳写成 1970 让网页立刻转灰。
eq(isAgentOffline(express('1970-01-01T00:00:00Z')), true, 'graceful shutdown sentinel -> offline');

// 拿不准一律离线:从未配对、字段缺失、时间戳损坏,都不许显示「已连接」。
eq(isAgentOffline(express()), true, 'never paired -> offline');
eq(isAgentOffline(express(null)), true, 'null heartbeat -> offline');
eq(isAgentOffline(express('')), true, 'empty heartbeat -> offline');
eq(isAgentOffline(express('not-a-timestamp')), true, 'corrupt heartbeat -> offline');
eq(isAgentOffline({ adapter: 'express' }), true, 'express without config -> offline');

// adapter 大小写来自后端原样字段,判定按小写比对。
eq(isAgentOffline({ adapter: 'EXPRESS', config: { agent_last_seen_at: ago(60000) } }), false, 'uppercase adapter online');
eq(isAgentOffline({ adapter: 'Express', config: {} }), true, 'mixed-case adapter offline');

console.log('OK');
"""


@unittest.skipUnless(shutil.which("node"), "node not available")
class TestErpCardAgentOffline(unittest.TestCase):
    def test_offline_judgement_in_real_node(self) -> None:
        r = subprocess.run(
            [shutil.which("node") or "node", "-e", DRIVER, str(SRC)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=90,
        )
        self.assertEqual(r.returncode, 0, msg=(r.stdout + r.stderr))
        self.assertIn("OK", r.stdout)

    def test_offline_label_translated_in_all_four_languages(self) -> None:
        # 键漏一语 → 该语种会计看到裸 key「dx-erp-offline」,比不显示更糟。
        hits = re.findall(r"'dx-erp-offline':", I18N.read_text(encoding="utf-8"))
        self.assertEqual(len(hits), 4, f"dx-erp-offline 应四语齐全,实得 {len(hits)}")


if __name__ == "__main__":
    unittest.main()

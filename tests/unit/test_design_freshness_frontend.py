#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_design_freshness_frontend.py

基准过期检测(tests/visual/design-freshness.js)的反证 + 登记表体检。

视觉照搬闸要跑真浏览器(CI 的 test job 里),这里只验它的判据本身:喂已知有毒样本必须报红,
干净样本必须不报;顺带体检登记表(条目指向的基准文件要在、理由不许空),以及锁住
pur-settings 那面 2026-07-31 修掉的 chip 墙不许回潮。node 缺失时跳过。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DIR = PROJECT_ROOT / "tests" / "visual" / "design"
ALLOW_FILE = DESIGN_DIR / "_freshness-allow.json"

DRIVER = r"""
const { checkFreshness } = require(process.argv[1]);
const allow = { global: { deco: 'ok' }, pages: { 'p.html': { legacy: 'ok' } } };
let fails = 0;
const ok = (c, m) => { if (!c) { console.error('FAIL ' + m); fails++; } };

// ① 毒样本:稿里有 .gone,生产 DOM 与样式表都没有 → 必须报
let r = checkFreshness('p.html', ['panel', 'gone'], ['panel'], ['panel'], allow);
ok(r.orphans.length === 1 && r.orphans[0] === 'gone', '毒样本 .gone 被逮住 · got ' + JSON.stringify(r.orphans));

// ② 干净样本:稿里的 class 生产 DOM 全有 → 不许报
r = checkFreshness('p.html', ['panel', 'btn'], ['panel', 'btn'], [], allow);
ok(r.orphans.length === 0, '干净样本不误报 · got ' + JSON.stringify(r.orphans));

// ③ 这次没渲染出来但生产还留着样式 → 不许报(挡 stub 只渲染一态造的误报)
r = checkFreshness('p.html', ['panel', 'row'], ['panel'], ['panel', 'row'], allow);
ok(r.orphans.length === 0, '有样式无元素不误报 · got ' + JSON.stringify(r.orphans));

// ④ 登记豁免:不进 orphans,但要出现在 skipped 里带理由(不静默跳过)
r = checkFreshness('p.html', ['panel', 'deco', 'legacy'], ['panel'], [], allow);
ok(r.orphans.length === 0, '登记过的不报红 · got ' + JSON.stringify(r.orphans));
ok(r.skipped.length === 2 && r.skipped.every((s) => s.why), '登记条目进 skipped 且带理由');
ok(r.judged === 1, '判过的数目排除登记条目 · got ' + r.judged);

// ⑤ 登记表自己过期:登记了 .legacy,生产现在又有了 → 必须报,逼人删登记
r = checkFreshness('p.html', ['legacy'], ['legacy'], [], allow);
ok(r.dead.length === 1 && r.dead[0] === 'legacy', '失效登记被逮住 · got ' + JSON.stringify(r.dead));

if (fails) process.exit(1);
console.log('OK');
"""


class DesignFreshnessTests(unittest.TestCase):
    def test_freshness_judgement_node(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        module = PROJECT_ROOT / "tests" / "visual" / "design-freshness.js"
        proc = subprocess.run(
            [node, "-e", DRIVER, str(module)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=(proc.stdout + proc.stderr))
        self.assertIn("OK", proc.stdout)

    def test_allow_registry_is_honest(self) -> None:
        data = json.loads(ALLOW_FILE.read_text(encoding="utf-8"))
        buckets = [("global", data["global"])] + [
            (page, entries) for page, entries in data["pages"].items()
        ]
        for page, entries in buckets:
            if page != "global":
                self.assertTrue(
                    (DESIGN_DIR / page).is_file(),
                    f"登记表指向不存在的基准 {page} —— 基准删了登记也要删",
                )
            for cls, why in entries.items():
                self.assertGreaterEqual(
                    len(why.strip()), 8, f"{page}.{cls} 的理由太短,登记必须写清为什么生产没有"
                )

    def test_purchase_settings_chip_wall_stays_dead(self) -> None:
        # 0f5a5fad(2026-07-07)把费用科目搬去「商品 › 费用数据」· 基准里那面 chip 墙留到 7-31 才清。
        html = (DESIGN_DIR / "pur-settings.html").read_text(encoding="utf-8")
        body = html[html.index("<body") :]
        for cls in ("cats", "chip", "addc"):
            self.assertIsNone(
                re.search(r'class="[^"]*(?<![\w-])' + cls + r"(?![\w-])", body),
                f"pur-settings 基准又出现 .{cls} —— 生产这页早没有费用科目 chip 墙了",
            )
        self.assertIn("去费用数据", body, "基准该留生产实际那行「去费用数据 →」跳转")


if __name__ == "__main__":
    unittest.main()

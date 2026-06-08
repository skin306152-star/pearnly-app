#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_pay_accessors.py

POS 收款设置共享访问器(static/pos/pos-data.js · POS.pay)守门。

收银台(pos-cashier.js)与餐厅埋单(pos-restaurant-ops.js)原各写一份 state.payment 默认访问器
+ 硬编码 show/hide,去重后统一走 POS.pay。这里用真 node 加载 pos-data.js,验三件事:
  1. settings/inclVat/svcRate 默认与覆盖语义(未拉到收款设置=默认全开 + 价内 VAT + 服务费回落 10)。
  2. applyMethods 数据驱动显隐:现金(无开关)恒显,关掉的方式置 display:none。
  3. data-pm 键 qr(收银台)/ promptpay(餐厅)都映射到 promptpay_enabled —— 这是不归一键(免改后端
     method 字符串/报表分组)却共用一个 applyMethods 的关键,必须双向覆盖防回归。
node 缺失时跳过(本地/CI 均装了 node)。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_JS = PROJECT_ROOT / "static" / "pos" / "pos-data.js"

# pos-data.js 是浏览器 IIFE(挂 window.POS),node 里补最小 window/document 桩后加载,
# 再用 POS.pay 跑各场景,把结果汇成一个 JSON 对象给 Python 断言。
NODE_HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');

const win = {};
global.window = win;
global.fetch = () => Promise.reject(new Error('no network in test'));

// 当前这一轮 applyMethods 要操作的 DOM,按 selector 取;每个元素 {dataset:{pm}, style:{}}。
let DOM = {};
global.document = { querySelectorAll: (sel) => DOM[sel] || [] };

// 加载 pos-data.js(IIFE 自执行 → window.POS 就绪)
(0, eval)(src);
const POS = win.POS;

function mkEls(pms) {
    return pms.map((pm) => ({ dataset: { pm }, style: {} }));
}

// ── 未拉到收款设置 → settings() 给全默认(全开 + 价内VAT)──
POS.state.payment = null;
const defaults = POS.pay.settings();

// ── 派生访问器 inclVat / svcRate(开票 payload 用)逐场景 ──
const accessor = [
    null, // 默认:价内VAT=true,服务费回落 '10'
    { price_includes_vat: false },
    { price_includes_vat: true },
    { service_charge_rate: '7.5' },
    { service_charge_rate: 0 }, // 0 ≠ null → 取 '0'(不回落)
].map((payment) => {
    POS.state.payment = payment;
    return { inclVat: POS.pay.inclVat(), svcRate: POS.pay.svcRate() };
});

// ── applyMethods:收银台 .pm(cash/qr/card) + 餐厅 button(cash/promptpay/card) ──
function applyCase(payment, sel, pms) {
    POS.state.payment = payment;
    const els = mkEls(pms);
    DOM = { [sel]: els };
    POS.pay.applyMethods(sel);
    return els.map((e) => e.style.display);
}

const apply = {
    // promptpay 关 / card 开 → 收银台:cash 不动(''),qr 隐,card 显
    cashier_pp_off: applyCase(
        { promptpay_enabled: false, card_enabled: true },
        '#pay-mask .pm',
        ['cash', 'qr', 'card']
    ),
    // 餐厅同一设置:promptpay 隐,card 显(证明 promptpay 键也映射到 promptpay_enabled)
    restaurant_pp_off: applyCase(
        { promptpay_enabled: false, card_enabled: true },
        '#rb-pm button',
        ['cash', 'promptpay', 'card']
    ),
    // card 关 / promptpay 开 → 餐厅:card 隐,promptpay 显
    restaurant_card_off: applyCase(
        { promptpay_enabled: true, card_enabled: false },
        '#rb-pm button',
        ['cash', 'promptpay', 'card']
    ),
    // 全开(state.payment=null 用默认)→ 全部显(现金'',其余'')
    cashier_default: applyCase(null, '#pay-mask .pm', ['cash', 'qr', 'card']),
};

process.stdout.write(JSON.stringify({ defaults, accessor, apply }));
"""

# display 期望:'' = 显示(不改),'none' = 隐藏。现金永远 ''(无开关)。
EXPECTED = {
    "defaults": {"promptpay_enabled": True, "card_enabled": True, "price_includes_vat": True},
    "accessor": [
        {"inclVat": True, "svcRate": "10"},  # null → 价内VAT + 服务费回落 10
        {"inclVat": False, "svcRate": "10"},
        {"inclVat": True, "svcRate": "10"},
        {"inclVat": True, "svcRate": "7.5"},
        {"inclVat": True, "svcRate": "0"},
    ],
    # 现金无开关 → applyMethods 不碰它(style.display 保持未设 = None),由 HTML/CSS 决定显示。
    "apply": {
        "cashier_pp_off": [None, "none", ""],
        "restaurant_pp_off": [None, "none", ""],
        "restaurant_card_off": [None, "", "none"],
        "cashier_default": [None, "", ""],
    },
}


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过 POS.pay 访问器测试")
class PosPayAccessorsTest(unittest.TestCase):
    def test_shared_accessor_semantics(self):
        self.assertTrue(DATA_JS.exists(), "pos-data.js 缺失")
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(NODE_HARNESS)
            harness = fh.name
        try:
            proc = subprocess.run(
                ["node", harness, str(DATA_JS)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        finally:
            Path(harness).unlink(missing_ok=True)
        self.assertEqual(proc.returncode, 0, f"node 跑 pos-data 失败: {proc.stderr}")
        got = json.loads(proc.stdout)
        self.assertEqual(got, EXPECTED)


if __name__ == "__main__":
    unittest.main()

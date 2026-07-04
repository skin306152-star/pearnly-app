#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_purchase_calc.py

商户采购进项录入即时合计(src/home/purchase-calc.js · computePurchaseTotals)守门。

屏10 录入时本地即时重算税前→VAT→含税→WHT→实付,逐行取整防 ±1 分漂移(餐厅服务费教训)。
后端 services/purchase/totals.py 尚未上线;本测试用真 node 跑 calc 对照「设计稿黄金值」
(Pearnly_采购_UI预览/10:13,600 → VAT 952 → 含税 14,552 → WHT 300 → 实付 14,252)+ 逐分取整边界。
后端 totals 上线后可在此加等价用例(同 test_pos_local_totals 模式)。node 缺失时跳过。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CALC_JS = PROJECT_ROOT / "src" / "home" / "purchase-calc.js"

NODE_HARNESS = """
import { pathToFileURL } from 'url';
const c = await import(pathToFileURL(process.argv[2]).href);
const cases = JSON.parse(process.argv[3]);
const out = cases.map(x => c.computePurchaseTotals(x.lines, x.opts));
process.stdout.write(JSON.stringify(out));
"""

# (label, lines, opts, expected{subtotal,vat_amount,grand_total,wht_amount,net_payable})
CASES = [
    (
        "设计稿黄金值(商品+服务行·服务带 WHT 3%)",
        [
            {"qty": 240, "unit_price": 15, "discount": 0, "vat_rate": 7, "wht_rate": 0},
            {"qty": 1, "unit_price": 10000, "discount": 0, "vat_rate": 7, "wht_rate": 3},
        ],
        {},
        {
            "subtotal": "13600.00",
            "vat_amount": "952.00",
            "grand_total": "14552.00",
            "wht_amount": "300.00",
            "net_payable": "14252.00",
        },
    ),
    (
        "无 VAT 费用单(打车 200·不抵税·无 WHT)",
        [{"qty": 1, "unit_price": 200, "discount": 0, "vat_rate": 0, "wht_rate": 0}],
        {},
        {
            "subtotal": "200.00",
            "vat_amount": "0.00",
            "grand_total": "200.00",
            "wht_amount": "0.00",
            "net_payable": "200.00",
        },
    ),
    (
        "行折扣 + 整单折扣(税前与含税都减)",
        [{"qty": 10, "unit_price": 100, "discount": 50, "vat_rate": 7, "wht_rate": 0}],
        {"doc_discount": 50},
        {
            # 行净额 1000-50=950 · VAT 950*7%=66.50 · 含税 950-50+66.50=966.50
            "subtotal": "950.00",
            "vat_amount": "66.50",
            "grand_total": "966.50",
            "wht_amount": "0.00",
            "net_payable": "966.50",
        },
    ),
    (
        "两行不同预扣率(服务 3% + 运输 1%·逐行汇总非全局单一率)",
        [
            {"qty": 1, "unit_price": 10000, "discount": 0, "vat_rate": 7, "wht_rate": 3},
            {"qty": 1, "unit_price": 5000, "discount": 0, "vat_rate": 0, "wht_rate": 1},
        ],
        {},
        {
            # 净 15000 · VAT 700 · 含税 15700 · WHT 300+50=350 · 实付 15350
            "subtotal": "15000.00",
            "vat_amount": "700.00",
            "grand_total": "15700.00",
            "wht_amount": "350.00",
            "net_payable": "15350.00",
        },
    ),
    (
        "商品行也可带预扣(税务上存在·140 净额 × 1% = 1.40)",
        [{"qty": 1, "unit_price": 140, "discount": 0, "vat_rate": 7, "wht_rate": 1}],
        {},
        {
            "subtotal": "140.00",
            "vat_amount": "9.80",
            "grand_total": "149.80",
            "wht_amount": "1.40",
            "net_payable": "148.40",
        },
    ),
    (
        "逐行取整(两行各 0.5 分·分别取整非汇总取整)",
        [
            {"qty": 1, "unit_price": 1.07, "discount": 0, "vat_rate": 7, "wht_rate": 0},
            {"qty": 1, "unit_price": 1.07, "discount": 0, "vat_rate": 7, "wht_rate": 0},
        ],
        {},
        {
            # 每行 VAT 1.07*0.07=0.0749 → 0.07 · 两行 0.14;subtotal 2.14;含税 2.28
            "subtotal": "2.14",
            "vat_amount": "0.14",
            "grand_total": "2.28",
            "wht_amount": "0.00",
            "net_payable": "2.28",
        },
    ),
]


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过采购合计等价测试")
class PurchaseCalcGoldenTest(unittest.TestCase):
    def test_matches_design_golden(self):
        self.assertTrue(CALC_JS.exists(), "purchase-calc.js 缺失")
        js_cases = [{"lines": lines, "opts": opts} for (_, lines, opts, _) in CASES]
        with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as fh:
            fh.write(NODE_HARNESS)
            harness = fh.name
        try:
            proc = subprocess.run(
                ["node", harness, str(CALC_JS), json.dumps(js_cases)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        finally:
            Path(harness).unlink(missing_ok=True)
        self.assertEqual(proc.returncode, 0, f"node 跑 purchase-calc 失败: {proc.stderr}")
        out = json.loads(proc.stdout)
        for i, (label, _lines, _opts, expected) in enumerate(CASES):
            got = out[i]
            for key, want in expected.items():
                self.assertEqual(
                    got[key],
                    want,
                    f"用例「{label}」字段 {key} 不符 · 实际={got[key]} 期望={want}",
                )


if __name__ == "__main__":
    unittest.main()

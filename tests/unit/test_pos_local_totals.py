#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_local_totals.py

POS B5 离线本地算价(static/pos/pos-totals.js)与服务端 services/sales/totals.py 等价守门。

离线开单时收银要立刻看到应收/找零并出小票(08 ADR-4),本地算法必须与服务端权威复算逐分一致,
否则同一单线下显示金额 ≠ 联网入库金额。这里用真 node 跑 pos-totals.js 的 localTotals,对照
Python compute_totals 的输出(subtotal / discount_total / header_discount / vat / grand),覆盖
价内价外 × 整单折扣(无/绝对/百分比)× 非应税行。node 缺失时跳过(本地/CI 均装了 node)。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOTALS_JS = PROJECT_ROOT / "static" / "pos" / "pos-totals.js"

from services.sales.totals import compute_totals

VAT_RATE = 7

# (lines, opts) · lines: [{qty, unit_price, discount, vat_applicable}]
CASES = [
    # 价外 · 无折扣
    (
        [{"qty": 2, "unit_price": "15.00", "discount": "0", "vat_applicable": True}],
        False,
        "none",
        0,
    ),
    # 价内 · 无折扣(VAT 反算)
    ([{"qty": 3, "unit_price": "55.00", "discount": "0", "vat_applicable": True}], True, "none", 0),
    # 价外 · 行折扣
    (
        [{"qty": 4, "unit_price": "12.50", "discount": "5.00", "vat_applicable": True}],
        False,
        "none",
        0,
    ),
    # 价内 · 整单绝对折扣
    (
        [
            {"qty": 2, "unit_price": "15.00", "discount": "0", "vat_applicable": True},
            {"qty": 1, "unit_price": "25.00", "discount": "0", "vat_applicable": True},
        ],
        True,
        "amount",
        "10.00",
    ),
    # 价外 · 整单百分比折扣 + 非应税行
    (
        [
            {"qty": 3, "unit_price": "18.00", "discount": "0", "vat_applicable": True},
            {"qty": 2, "unit_price": "9.00", "discount": "0", "vat_applicable": False},
        ],
        False,
        "pct",
        "10",
    ),
    # 价内 · 多行 + 行折扣 + 整单百分比(VAT 摊销 + 反算)
    (
        [
            {"qty": 5, "unit_price": "22.00", "discount": "3.00", "vat_applicable": True},
            {"qty": 1, "unit_price": "120.00", "discount": "0", "vat_applicable": True},
        ],
        True,
        "pct",
        "5",
    ),
]

NODE_HARNESS = """
const t = require(process.argv[2]);
const cases = JSON.parse(process.argv[3]);
const out = cases.map(c => t.localTotals(c.lines, c.opts));
process.stdout.write(JSON.stringify(out));
"""


def _py_totals(lines, incl, hd_type, hd_val):
    hd_amount = hd_val if hd_type == "amount" else 0
    hd_pct = hd_val if hd_type == "pct" else 0
    r = compute_totals(
        lines,
        vat_rate=VAT_RATE,
        price_includes_vat=incl,
        header_discount_amount=hd_amount,
        header_discount_pct=hd_pct,
    )
    return {
        "subtotal": f"{r['subtotal']:.2f}",
        "discount_total": f"{r['discount_total']:.2f}",
        "header_discount_amount": f"{r['header_discount_amount']:.2f}",
        "vat_amount": f"{r['vat_amount']:.2f}",
        "grand_total": f"{r['grand_total']:.2f}",
    }


def _js_opts(incl, hd_type, hd_val):
    return {
        "vat_rate": VAT_RATE,
        "price_includes_vat": incl,
        "header_discount_amount": hd_val if hd_type == "amount" else 0,
        "header_discount_pct": hd_val if hd_type == "pct" else 0,
    }


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过本地算价等价测试")
class PosLocalTotalsEquivalenceTest(unittest.TestCase):
    def test_local_matches_server(self):
        self.assertTrue(TOTALS_JS.exists(), "pos-totals.js 缺失")
        js_cases = [
            {"lines": lines, "opts": _js_opts(incl, hd_type, hd_val)}
            for (lines, incl, hd_type, hd_val) in CASES
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(NODE_HARNESS)
            harness = fh.name
        try:
            proc = subprocess.run(
                ["node", harness, str(TOTALS_JS), json.dumps(js_cases)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        finally:
            Path(harness).unlink(missing_ok=True)
        self.assertEqual(proc.returncode, 0, f"node 跑 pos-totals 失败: {proc.stderr}")
        js_out = json.loads(proc.stdout)
        for i, (lines, incl, hd_type, hd_val) in enumerate(CASES):
            py = _py_totals(lines, incl, hd_type, hd_val)
            js = js_out[i]
            for key in (
                "subtotal",
                "discount_total",
                "header_discount_amount",
                "vat_amount",
                "grand_total",
            ):
                self.assertEqual(
                    js[key],
                    py[key],
                    f"case#{i} 字段 {key} 不等价 · 本地={js[key]} 服务端={py[key]} · "
                    f"(incl={incl} hd={hd_type}:{hd_val})",
                )


if __name__ == "__main__":
    unittest.main()

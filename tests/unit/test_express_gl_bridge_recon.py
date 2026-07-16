# -*- coding: utf-8 -*-
"""Express 对平贯通金标(T4b · matcher + adapter → reconcile_gl 端到端)。

合成"影子科目余额 + 冰厂式 GL fixture + auto 桥"→ reconcile_gl:erp 侧聚合正确、
matched/unmapped/gl_only 分类对、Σ借Σ贷合计对平判定对。桥由 matcher 自动从 GLACC 建,
GL 由 adapter 从 GLJNLIT 转,只喂 reconcile_gl 的 erp 侧,不改任何 F2 契约。
"""

import unittest
from decimal import Decimal

from services.accounting import express_coa_matcher as matcher
from services.accounting import express_gl_adapter as adapter
from services.accounting.shadow_gl_recon import reconcile_gl

_GLACC = [
    {"ACCNUM": "11-01-01-01", "ACCNAM": "เงินสด"},
    {"ACCNUM": "11-01-02-01", "ACCNAM": "เงินฝากธนาคาร"},
    {"ACCNUM": "21-05-04-02", "ACCNAM": "ภาษีขาย"},
    {"ACCNUM": "11-05-04-01", "ACCNAM": "ภาษีซื้อ"},
    {"ACCNUM": "41-01-01-01", "ACCNAM": "รายได้จากการขาย"},
    {"ACCNUM": "51-01-01-01", "ACCNAM": "ต้นทุนขาย"},
]

_GLJNLIT_CSV = (
    "VOUCHER,ACCNUM,TRNTYP,AMOUNT\r\n"
    "JV001,11-01-01-01,0,1000.50\r\n"
    "JV001,41-01-01-01,1,934.58\r\n"
    "JV001,21-05-04-02,1,65.92\r\n"
    "JV002,11-05-04-01,0,70.00\r\n"
    "JV002,51-01-01-01,0,1000.00\r\n"
    "JV002,11-01-02-01,1,1070.00\r\n"
).encode("utf-8-sig")


def _bridge_and_gl():
    bridge = matcher.suggest_bridge(_GLACC).bridge_map()
    gl_rows, _ = adapter.parse_express_gl_csv(_GLJNLIT_CSV, "gl.csv")
    return bridge, gl_rows


class ReconciledGoldenTests(unittest.TestCase):
    def test_full_coverage_reconciles(self):
        bridge, gl_rows = _bridge_and_gl()
        shadow = [
            {"code": "1010", "name": "现金", "debit": "1000.50", "credit": "0"},
            {"code": "4010", "name": "销售收入", "debit": "0", "credit": "934.58"},
            {"code": "2030", "name": "销项税", "debit": "0", "credit": "65.92"},
            {"code": "1140", "name": "进项税", "debit": "70.00", "credit": "0"},
            {"code": "5010", "name": "销售成本", "debit": "1000.00", "credit": "0"},
            {"code": "1020", "name": "银行", "debit": "0", "credit": "1070.00"},
        ]
        res = reconcile_gl(shadow, gl_rows, bridge)
        self.assertEqual(res.status, "reconciled")
        self.assertFalse(res.alert)
        self.assertTrue(res.totals["balanced"])
        self.assertEqual(Decimal(res.totals["gl_debit"]), Decimal("2070.50"))
        self.assertEqual(Decimal(res.totals["gl_credit"]), Decimal("2070.50"))
        self.assertEqual(Decimal(res.totals["debit_diff"]), Decimal("0"))
        self.assertEqual(len(res.matched), 6)
        self.assertEqual(res.mismatch, [])
        self.assertEqual(res.gl_only, [])
        # erp 侧聚合按四段码正确:现金借方经桥对上。
        cash = next(r for r in res.matched if r["local_code"] == "1010")
        self.assertEqual(cash["erp_code"], "11-01-01-01")
        self.assertEqual(Decimal(cash["gl_debit"]), Decimal("1000.50"))

    def test_unmapped_and_gl_only_classified(self):
        bridge, gl_rows = _bridge_and_gl()
        # 影子含无桥科目 5290 → unmapped;去掉银行影子行 → 银行 GL 成 gl_only + 总额失衡。
        shadow = [
            {"code": "1010", "name": "现金", "debit": "1000.50", "credit": "0"},
            {"code": "4010", "name": "销售收入", "debit": "0", "credit": "934.58"},
            {"code": "2030", "name": "销项税", "debit": "0", "credit": "65.92"},
            {"code": "1140", "name": "进项税", "debit": "70.00", "credit": "0"},
            {"code": "5010", "name": "销售成本", "debit": "1000.00", "credit": "0"},
            {"code": "5290", "name": "杂项", "debit": "50.00", "credit": "0"},
        ]
        res = reconcile_gl(shadow, gl_rows, bridge)
        self.assertIn("5290", [u["local_code"] for u in res.unmapped])
        self.assertIn("11-01-02-01", [g["erp_code"] for g in res.gl_only])
        self.assertFalse(res.totals["balanced"])
        self.assertEqual(res.status, "mismatch")


if __name__ == "__main__":
    unittest.main()

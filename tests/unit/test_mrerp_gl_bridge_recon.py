# -*- coding: utf-8 -*-
"""MR.ERP 对平贯通金标(T4b-SM · matcher + adapter → reconcile_gl 端到端)。

合成"影子科目余额 + SM 式分类账 xlsx + auto 桥"→ reconcile_gl:erp 侧按扁平码聚合正确、
matched/unmapped/gl_only 分类对、Σ借Σ贷合计对平判定对。桥由 matcher 从 GL 标题行自动建,
GL 由 adapter 从分类账 xlsx 转,只喂 reconcile_gl 的 erp 侧,不改任何 F2 契约。
"""

import io
import unittest
from datetime import datetime
from decimal import Decimal

import openpyxl

from services.accounting import mrerp_coa_matcher as matcher
from services.accounting import mrerp_gl_adapter as adapter
from services.accounting.shadow_gl_recon import reconcile_gl

_HEADER = ["วันที่", "สมุด", "ใบสำคัญ", "คำอธิบาย", "เดบิต", "เครดิต", "ยอดคงเหลือ"]

# 名对 preset · Σ借=Σ贷=2070.50
_ACCOUNTS = [
    ("1111-01", "เงินสด", [("2569-05-28", "รับ", "FR001", "ขายสด", "1000.50", "0")]),
    ("4110-01", "รายได้จากการขาย", [(datetime(2569, 5, 28), "ขาย", "SE001", "ขาย", "0", "934.58")]),
    ("2160-11", "ภาษีขาย", [("2569-05-28", "ขาย", "SE001", "ภาษีขาย", "0", "65.92")]),
    ("1161-10", "ภาษีซื้อ", [("2569-05-28", "ซื้อ", "PV001", "ภาษีซื้อ", "70.00", "0")]),
    ("5010-01", "ต้นทุนขาย", [("2569-05-28", "ซื้อ", "PV001", "ต้นทุน", "1000.00", "0")]),
    ("1112-01", "เงินฝากธนาคาร", [("2569-05-28", "จ่าย", "PV002", "ธนาคาร", "0", "1070.00")]),
]


def _build_ledger(accounts) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["บริษัท ทดสอบ จำกัด", "", "", "", "", "", ""])
    ws.append(["รายงานสมุดแยกประเภท", "", "", "", "", "", ""])
    ws.append(["วันที่  01/01/2569  ถึง", "", "", "", "", "วันที่  16/07/2569", ""])
    ws.append(["รหัสบัญชี", "", "", "", "", "", ""])
    ws.append(list(_HEADER))
    for code, name, details in accounts:
        ws.append([f"{code}  {name}", "", "", "", "", "", "0"])
        td = tc = Decimal("0")
        for dt, book, vch, desc, dr, cr in details:
            ws.append([dt, book, vch, desc, dr, cr, "0"])
            td += Decimal(str(dr))
            tc += Decimal(str(cr))
        ws.append(["รวม", "", "", "", str(td), str(tc), ""])
        ws.append(["", "", "", "", "", "", ""])
    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    return buf.getvalue()


def _bridge_and_gl():
    data = _build_ledger(_ACCOUNTS)
    bridge = matcher.suggest_bridge(adapter.iter_account_titles(data)).bridge_map()
    gl_rows, _ = adapter.parse_mrerp_gl_xlsx(data, "gl.xlsx")
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
        # erp 侧按扁平码聚合:现金借方经桥对上。
        cash = next(r for r in res.matched if r["local_code"] == "1010")
        self.assertEqual(cash["erp_code"], "1111-01")
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
        self.assertIn("1112-01", [g["erp_code"] for g in res.gl_only])
        self.assertFalse(res.totals["balanced"])
        self.assertEqual(res.status, "mismatch")


if __name__ == "__main__":
    unittest.main()

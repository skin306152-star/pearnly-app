# -*- coding: utf-8 -*-
"""银行对账导出「总账余额列」守门:GL 行运行余额(期初+累计借−贷)透传到导出 · 4 语跟随。
不参与匹配引擎(只新增展示字段)· 见 [[GlRow.balance / BankReconRow.gl_balance]]。"""

import unittest
from datetime import date

import openpyxl

from services.recon.bank_recon_types import GlRow, StatementRow
from services.recon.bank_recon_reconcile import reconcile
from services.recon.bank_recon_excel import _build_match_results_sheet
from services.recon.bank_recon_excel_i18n import _t


class ReconGlBalanceTests(unittest.TestCase):
    def _rows(self):
        gl = [
            GlRow(
                date(2025, 6, 2),
                "V1",
                "1112",
                "รับ บริษัท แจแปน 111",
                227418.00,
                0.0,
                balance=378232.56,
            ),
            GlRow(date(2025, 6, 5), "V2", "1112", "โอนให้", 0.0, 380000.00, balance=-1632.44),
        ]
        st = [
            StatementRow(
                date=date(2025, 6, 2),
                description="in",
                withdrawal=0.0,
                deposit=227418.00,
                balance=378232.56,
            )
        ]
        return reconcile(st, gl)

    def test_gl_balance_passthrough_to_recon_row(self):
        rows, _ = self._rows()
        matched = [r for r in rows if r.match_status == "matched"]
        self.assertTrue(matched)
        self.assertEqual(matched[0].gl_balance, 378232.56)
        # GL 孤项也带余额
        gl_only = [r for r in rows if r.match_status in ("gl_debit_only", "gl_credit_only")]
        self.assertTrue(any(r.gl_balance == -1632.44 for r in gl_only))

    def test_export_has_gl_balance_column_4lang(self):
        rows, _ = self._rows()
        for lang in ("zh", "en", "th", "ja"):
            wb = openpyxl.Workbook()
            _build_match_results_sheet(wb, rows, lang)
            ws = wb.worksheets[-1]
            hdr = [c.value for c in ws[1]]
            label = _t("col_gl_balance", lang)
            self.assertIn(label, hdr, f"{lang} 列头缺 GL 余额")
            ci = hdr.index(label)
            # 已配对行该列有值
            vals = [ws.cell(r, ci + 1).value for r in range(2, ws.max_row + 1)]
            self.assertIn(378232.56, vals, f"{lang} GL 余额列无值")

    def test_gl_detail_sheet_has_balance_column_4lang(self):
        # 「总账明细」sheet(รายละเอียดบัญชีแยกประเภท)也要有余额列 · 4 语跟随
        from services.recon.bank_recon_excel import export_bank_recon_excel
        from services.recon.bank_recon_types import BankReconSummary
        import io as _io

        rows, _ = self._rows()
        for lang in ("zh", "en", "th", "ja"):
            blob = export_bank_recon_excel(rows, BankReconSummary(), lang)
            wb = openpyxl.load_workbook(_io.BytesIO(blob))
            ws = wb[_t("sh_gl_detail", lang)]
            hdr = [c.value for c in ws[1]]
            self.assertIn(_t("col_balance", lang), hdr, f"{lang} 总账明细缺余额列")
            ci = hdr.index(_t("col_balance", lang))
            vals = [ws.cell(r, ci + 1).value for r in range(2, ws.max_row + 1)]
            self.assertIn(378232.56, vals, f"{lang} 总账明细余额无值")

    def test_running_balance_computed_from_opening(self):
        # parse 层逐行运行余额 = 期初 + 累计(借−贷)· 用 parse_gl_excel 验
        import io
        from services.recon.bank_gl_excel import parse_gl_excel

        wb = openpyxl.Workbook()
        wsx = wb.active
        wsx.title = "Pearnly-GL"
        wsx.append(
            ["วันที่", "เลขที่ใบสำคัญ", "รายละเอียด", "เดบิต=ฝากเงิน", "เครดิต=ถอนเงิน", "คงเหลือ"]
        )
        wsx.append(["ยอดยกมา", None, None, None, None, 100.0])
        wsx.append(["02/05/2026", "V1", "in", 200.0, None, 300.0])
        wsx.append(["02/05/2026", "V2", "out", None, 50.0, 250.0])
        buf = io.BytesIO()
        wb.save(buf)
        res = parse_gl_excel(buf.getvalue(), "gl.xlsx")
        self.assertTrue(res.get("ok"))
        bals = [r.balance for r in res["rows"]]
        self.assertEqual(bals, [300.0, 250.0])  # 100+200=300 · 300-50=250


if __name__ == "__main__":
    unittest.main()

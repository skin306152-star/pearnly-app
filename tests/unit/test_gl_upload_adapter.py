# -*- coding: utf-8 -*-
"""GL 上传件适配器单测(services/accounting/gl_upload_adapter.py · T4a)。

覆盖:借贷双列 LedgerRow 直搬 GlRow(Decimal→float 边界用金标数值 608,917.35 钉精度,
往返 shadow_gl_recon 的 str()→Decimal 清算无损);单金额列按余额变动定向(涨=借/跌=贷),
定不了向(无期初锚/余额持平)如实丢 issue 不臆造;parse_gl_bytes 的 PDF 主路(合成文本页
走真 extract_ledger)与整件失败态(无文字层/零行/不支持扩展名)全部 fail loud。
"""

import unittest
from decimal import Decimal

from services.accounting import gl_upload_adapter as adapter
from services.fileconv.ledger import extract_ledger

# 金标口径的三栏 GL 合成页(数值取 K1a 真料期末 608,917.35 等,内容脱敏)。
_GL_PAGE = """รายงานสมุดแยกประเภท
1113-01 เงินฝากธนาคาร 0.00
01/05/2569 JV JV001 รับเงิน 608917.35 0.00 608917.35
02/05/2569 JV JV002 จ่ายเงิน 0.00 1070.25 607847.10"""

# 单金额 + 跑余额两栏(承前 100):+50.10 → 150.10;−20.10 → 130.00;最后一行余额持平。
_AMOUNT_PAGE = """Bank Ledger
Date Description Debit Credit
01/01/2026 Balance Forward 100.00
02/01/2026 SV001 in 50.10 150.10
03/01/2026 SV002 out 20.10 130.00
04/01/2026 SV003 flat 5.00 130.00"""


def _dec_sum(rows, field):
    return sum((Decimal(str(getattr(r, field))) for r in rows), Decimal("0"))


class ThreeColumnAdaptTests(unittest.TestCase):
    def test_direct_rows_and_golden_precision(self):
        ledger_rows, opening = extract_ledger([_GL_PAGE])
        rows, issues = adapter.from_ledger_rows(ledger_rows, opening, source_file="gl.pdf")
        self.assertEqual(issues, [])
        self.assertEqual(len(rows), 2)
        r = rows[0]
        self.assertEqual(r.account_code, "1113-01")
        self.assertEqual(r.source_file, "gl.pdf")
        self.assertEqual(r.date.isoformat(), "2026-05-01")
        # 金标数值过 float 边界后经 str() 回 Decimal 无损(shadow_gl_recon._dec 的清算口径)。
        self.assertEqual(Decimal(str(r.debit)), Decimal("608917.35"))
        self.assertEqual(Decimal(str(rows[1].credit)), Decimal("1070.25"))
        self.assertEqual(_dec_sum(rows, "debit"), Decimal("608917.35"))
        self.assertEqual(_dec_sum(rows, "credit"), Decimal("1070.25"))


class AmountColumnDirectionTests(unittest.TestCase):
    def test_direction_from_balance_movement(self):
        ledger_rows, opening = extract_ledger([_AMOUNT_PAGE])
        rows, issues = adapter.from_ledger_rows(ledger_rows, opening)
        # 前两行按余额涨跌定向;第三行余额持平定不了向 → 如实丢 issue。
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0].debit, rows[0].credit), (50.10, 0.0))
        self.assertEqual((rows[1].debit, rows[1].credit), (0.0, 20.10))
        self.assertEqual(len(issues), 1)
        self.assertIn("余额持平", issues[0])

    def test_no_opening_anchor_drops_first_row_honestly(self):
        page = "\n".join(line for line in _AMOUNT_PAGE.split("\n") if "Balance Forward" not in line)
        ledger_rows, opening = extract_ledger([page])
        rows, issues = adapter.from_ledger_rows(ledger_rows, opening)
        # 首行无期初可锚 → 丢弃并留 issue;其余行仍以首行余额为锚续链,不断链。
        self.assertTrue(any("无期初可锚" in i for i in issues))
        self.assertEqual((rows[0].debit, rows[0].credit), (0.0, 20.10))


class ParseGlBytesTests(unittest.TestCase):
    def _patch_pages(self, pages):
        prev = adapter.extract_pages
        adapter.extract_pages = lambda data: pages
        self.addCleanup(setattr, adapter, "extract_pages", prev)

    def test_pdf_main_path(self):
        self._patch_pages([_GL_PAGE])
        out = adapter.parse_gl_bytes(b"%PDF-stub", "gl_may.pdf")
        self.assertEqual(len(out["rows"]), 2)
        self.assertEqual(out["row_issues"], [])
        self.assertEqual(out["rows"][0].source_file, "gl_may.pdf")

    def test_no_text_layer_fails_loud(self):
        self._patch_pages(None)
        with self.assertRaises(adapter.GlUploadParseError):
            adapter.parse_gl_bytes(b"\x00scan", "scan_gl.pdf")

    def test_zero_rows_fails_loud(self):
        # 有文字层但抽不出一行台账 = 读不出,必须炸,不许当「没上传」。
        self._patch_pages(["x" * 80])
        with self.assertRaises(adapter.GlUploadParseError):
            adapter.parse_gl_bytes(b"%PDF-stub", "gl_empty.pdf")

    def test_unsupported_ext_fails_loud(self):
        with self.assertRaises(adapter.GlUploadParseError):
            adapter.parse_gl_bytes(b"...", "gl.docx")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""台账#10 · GL 余额链确定性修复(gl_balance_chain.repair_gl_document)。

对抗实测:v1 竖排堆叠版式 12/12 期初恒空 + 借贷方向错 → 勾稽分 0.400。
锁四条:方向按余额涨跌摆正、期初数学反推(印刷合计消歧首行方向)、
断链只标不改、缺口跨行不误改。
"""

import unittest

from services.ocr.gl_balance_chain import repair_gl_document
from services.ocr.schemas_documents import GeneralLedgerDocument, GLEntry


def _e(debit="", credit="", balance="", **kw):
    return GLEntry(debit=debit, credit=credit, balance=balance, **kw)


def _doc(entries, opening="", closing="", total_debit="", total_credit=""):
    return GeneralLedgerDocument(
        opening_balance=opening,
        closing_balance=closing,
        total_debit=total_debit,
        total_credit=total_credit,
        entries=entries,
    )


class DirectionRepairTests(unittest.TestCase):
    def test_flipped_side_corrected_by_balance_delta(self):
        # 余额 1000→1500(涨 500)却记在贷方 → 摆正到借方 · 行标透明 · 不出警告
        doc = _doc([_e(credit="500", balance="1500")], opening="1000")
        warnings = repair_gl_document(doc)
        e = doc.entries[0]
        self.assertEqual(e.debit, "500.00")
        self.assertEqual(e.credit, "")
        self.assertEqual(e.direction, "deposit")
        self.assertTrue(e.raw_row_data.get("direction_autocorrected"))
        self.assertEqual(warnings, [])

    def test_consistent_rows_untouched(self):
        doc = _doc(
            [_e(debit="500", balance="1500"), _e(credit="200", balance="1300")],
            opening="1000",
        )
        warnings = repair_gl_document(doc)
        self.assertEqual(doc.entries[0].debit, "500")
        self.assertEqual(doc.entries[1].credit, "200")
        self.assertEqual(warnings, [])

    def test_broken_chain_flagged_not_modified(self):
        # 金额与涨跌都对不上 → 不改数 · 出断链警告(顶起人工)
        doc = _doc([_e(debit="500", balance="1800")], opening="1000")
        warnings = repair_gl_document(doc)
        self.assertEqual(doc.entries[0].debit, "500")
        self.assertEqual(len(warnings), 1)
        self.assertIn("余额链断裂", warnings[0])

    def test_gap_row_does_not_miscorrect(self):
        # 中间行缺余额 → 跨缺口涨跌 700 ≠ 单笔 200 → 不纠不报(缺口后重新锚定)
        doc = _doc(
            [_e(debit="500", balance=""), _e(debit="200", balance="1700")],
            opening="1000",
        )
        warnings = repair_gl_document(doc)
        self.assertEqual(doc.entries[1].debit, "200")
        self.assertEqual(warnings, [])


class OpeningDerivationTests(unittest.TestCase):
    def test_opening_derived_from_first_row(self):
        # 台账#10 主症状:期初没印 → 首行余额 51200 − 借 1200 = 50000
        doc = _doc(
            [_e(debit="1200", balance="51200"), _e(credit="1025", balance="50175")],
            closing="50175",
        )
        repair_gl_document(doc)
        self.assertEqual(doc.opening_balance, "50000.00")

    def test_printed_totals_flip_wrong_first_row(self):
        # 首行方向被读反(贷 1200)· 首行无上行余额可验 → 页脚印刷合计是唯一
        # 确定性佐证:翻转首行后借/贷两项全平 → 翻转 + 期初正确
        doc = _doc(
            [_e(credit="1200", balance="51200"), _e(credit="1025", balance="50175")],
            total_debit="1200",
            total_credit="1025",
        )
        warnings = repair_gl_document(doc)
        self.assertEqual(doc.entries[0].debit, "1200.00")
        self.assertTrue(doc.entries[0].raw_row_data.get("direction_autocorrected"))
        self.assertEqual(doc.opening_balance, "50000.00")
        self.assertEqual(warnings, [])

    def test_unreconcilable_totals_warn_not_modify(self):
        # 翻首行也平不了印刷合计 = 可能漏行 → 只警告不改数
        doc = _doc([_e(debit="1200", balance="51200")], total_debit="9999", total_credit="0")
        warnings = repair_gl_document(doc)
        self.assertEqual(doc.entries[0].debit, "1200")
        self.assertEqual(len(warnings), 1)
        self.assertIn("借贷合计与明细对不上", warnings[0])

    def test_printed_opening_never_overwritten(self):
        doc = _doc([_e(debit="1200", balance="51200")], opening="50000")
        repair_gl_document(doc)
        self.assertEqual(doc.opening_balance, "50000")

    def test_closing_backfilled_from_last_balance(self):
        doc = _doc([_e(debit="1200", balance="51200")], opening="50000")
        repair_gl_document(doc)
        self.assertEqual(doc.closing_balance, "51200")

    def test_empty_doc_noop(self):
        self.assertEqual(repair_gl_document(_doc([])), [])


class StackedLayoutEndToEndTests(unittest.TestCase):
    def test_gl_bank_cash_signature(self):
        # 语料 gl_bank_cash_01 的数字骨架:交替借贷 12 行 · 期初不印 · 借贷一列
        # 模拟模型把全部金额读进借方(方向信息在版式上不存在)
        amounts = [1200, 1025, 1380, 1175, 1560, 1325, 1740, 1475, 1920, 1625, 2100, 1775]
        balances = [
            51200,
            50175,
            51555,
            50380,
            51940,
            50615,
            52355,
            50880,
            52800,
            51175,
            53275,
            51500,
        ]
        doc = _doc(
            [_e(debit=str(a), balance=str(b)) for a, b in zip(amounts, balances)],
            closing="51500",
            total_debit="9900",
            total_credit="8400",
        )
        warnings = repair_gl_document(doc)
        self.assertEqual(warnings, [])
        self.assertEqual(doc.opening_balance, "50000.00")
        total_debit = sum(float(e.debit) for e in doc.entries if e.debit)
        total_credit = sum(float(e.credit) for e in doc.entries if e.credit)
        self.assertEqual(total_debit, 9900.0)  # GT total_debit
        self.assertEqual(total_credit, 8400.0)  # GT total_credit


if __name__ == "__main__":
    unittest.main(verbosity=2)

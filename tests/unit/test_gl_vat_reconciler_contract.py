# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · GL↔VAT 对账引擎 gl_vat_reconciler.py 行为契约

gl_vat_reconciler.py(总账 vs 销项税报表对账 · 仍被 recon 链路使用)此前 0 专属测试。
只测纯/确定性核心(不碰 parse_gl_pdf/excel 这类需真文件字节的解析):
  - 工具:_to_float / _is_revenue_acct / _is_debit_line / normalize_doc_no
  - reconcile_gl_vat:匹配 / 容差 / 贷项票(负额)/ GL-only / VAT-only / 汇总
  - json 往返:detail/summary to_json↔from_json(任务状态持久化契约)
纯函数 · 无 DB/网络/凭证(Wave 0 安全网 · 零冲突)。
"""

import unittest

import gl_vat_reconciler as glv
from gl_vat_reconciler import GlRow, ReconRow, GlVatSummary


class HelperTests(unittest.TestCase):
    def test_to_float_variants(self):
        self.assertEqual(glv._to_float("1,000.00"), 1000.0)
        self.assertEqual(glv._to_float("(1,000.00)"), -1000.0)  # 括号 = 负数
        self.assertEqual(glv._to_float("-"), 0.0)
        self.assertEqual(glv._to_float(None), 0.0)
        self.assertEqual(glv._to_float("abc"), 0.0)
        self.assertEqual(glv._to_float(1234.5), 1234.5)

    def test_is_revenue_acct(self):
        self.assertTrue(glv._is_revenue_acct("4110-01"))  # 默认 4 开头
        self.assertFalse(glv._is_revenue_acct("5110"))
        self.assertFalse(glv._is_revenue_acct(""))
        self.assertTrue(glv._is_revenue_acct("8xxx", prefix="8"))

    def test_is_debit_line(self):
        self.assertTrue(glv._is_debit_line("ใบลดหนี้ คืนสินค้า"))  # 含退货/折让关键词
        self.assertFalse(glv._is_debit_line("ขายสินค้า ปกติ"))

    def test_normalize_doc_no_delegates(self):
        self.assertEqual(glv.normalize_doc_no("INV-001"), "inv001")


def _gl(doc_no, *, credit=0.0, debit=0.0, acct="4110-01", date="2026-03-15", desc="Sale"):
    return GlRow(
        doc_no=doc_no,
        norm_doc_no=glv.normalize_doc_no(doc_no),
        date=date,
        account_code=acct,
        description=desc,
        debit=debit,
        credit=credit,
    )


def _vat(ref, amt, *, name="ACME", date="2026-03-15"):
    return {
        "report_ref_no": ref,
        "report_date": date,
        "report_buyer_name": name,
        "report_amount_pre_vat": amt,
    }


class ReconcileMatchTests(unittest.TestCase):
    def test_exact_match_diff_zero(self):
        gl = [_gl("INV-001", credit=1000.0)]
        vat = [_vat("inv001", 1000.0)]
        detail, summary = glv.reconcile_gl_vat(gl, vat)
        self.assertEqual(len(detail), 1)
        self.assertEqual(detail[0].gl_amount, 1000.0)
        self.assertEqual(detail[0].diff, 0.0)
        self.assertEqual(detail[0].account_codes, "4110-01")
        self.assertEqual(summary.gl_total, 1000.0)
        self.assertEqual(summary.vat_total, 1000.0)
        self.assertEqual(summary.gl_only_credit, 0.0)
        self.assertEqual(summary.vat_only_positive, 0.0)

    def test_within_tolerance_diff_collapses_to_zero(self):
        gl = [_gl("A", credit=999.99)]
        vat = [_vat("A", 1000.00)]  # raw diff 0.01 <= 容差 → 0
        detail, _ = glv.reconcile_gl_vat(gl, vat)
        self.assertEqual(detail[0].diff, 0.0)

    def test_beyond_tolerance_keeps_diff(self):
        gl = [_gl("A", credit=999.98)]
        vat = [_vat("A", 1000.00)]  # diff 0.02 > 容差
        detail, _ = glv.reconcile_gl_vat(gl, vat)
        self.assertEqual(detail[0].diff, 0.02)

    def test_multi_gl_rows_sum_credit_and_join_accounts(self):
        gl = [_gl("A", credit=600.0, acct="4110-01"), _gl("A", credit=400.0, acct="4120-02")]
        vat = [_vat("A", 1000.0)]
        detail, _ = glv.reconcile_gl_vat(gl, vat)
        self.assertEqual(detail[0].gl_amount, 1000.0)
        self.assertEqual(detail[0].account_codes, "4110-01,4120-02")  # 去重排序拼接


class ReconcileCreditNoteTests(unittest.TestCase):
    def test_negative_vat_uses_debit_side(self):
        # 贷项票(负额)→ GL 侧取 -sum(debit)
        gl = [_gl("CN1", debit=100.0)]
        vat = [_vat("CN1", -100.0)]
        detail, _ = glv.reconcile_gl_vat(gl, vat)
        self.assertEqual(detail[0].gl_amount, -100.0)
        self.assertEqual(detail[0].diff, 0.0)


class ReconcileOrphanTests(unittest.TestCase):
    def test_vat_only_no_gl(self):
        vat = [_vat("ZZZ", 500.0)]
        detail, summary = glv.reconcile_gl_vat([], vat)
        self.assertIsNone(detail[0].gl_amount)
        self.assertIsNone(detail[0].diff)
        self.assertEqual(summary.vat_only_positive, 500.0)
        self.assertEqual(len(summary.vat_only_positive_items), 1)

    def test_vat_only_negative(self):
        vat = [_vat("ZZZ", -200.0)]
        _, summary = glv.reconcile_gl_vat([], vat)
        self.assertEqual(summary.vat_only_negative, -200.0)
        self.assertEqual(len(summary.vat_only_negative_items), 1)

    def test_gl_only_credit_and_debit(self):
        gl = [_gl("GLC", credit=300.0), _gl("GLD", debit=120.0)]
        _, summary = glv.reconcile_gl_vat(gl, [])
        self.assertEqual(summary.gl_only_credit, 300.0)
        self.assertEqual(summary.gl_only_debit, 120.0)
        self.assertEqual(len(summary.gl_only_credit_items), 1)
        self.assertEqual(summary.gl_only_credit_items[0]["doc_no"], "GLC")


class JsonRoundTripTests(unittest.TestCase):
    def test_detail_round_trip(self):
        rows = [
            ReconRow(
                doc_no="A",
                date="2026-03-15",
                customer_name="ACME",
                vat_amount=1000.0,
                gl_amount=1000.0,
                diff=0.0,
                account_codes="4110-01",
            )
        ]
        back = glv.detail_from_json(glv.detail_to_json(rows))
        self.assertEqual(back, rows)

    def test_summary_round_trip(self):
        s = GlVatSummary(
            gl_total=1000.0,
            gl_only_credit=0.0,
            gl_only_debit=0.0,
            vat_only_positive=0.0,
            vat_only_negative=0.0,
            vat_total=1000.0,
        )
        back = glv.summary_from_json(glv.summary_to_json(s))
        self.assertEqual(back, s)

    def test_summary_from_json_none_defaults(self):
        s = glv.summary_from_json(None)
        self.assertEqual(s.gl_total, 0)
        self.assertEqual(s.vat_total, 0)
        self.assertEqual(s.gl_only_credit_items, [])  # __post_init__ 兜底

    def test_detail_from_json_empty(self):
        self.assertEqual(glv.detail_from_json(None), [])


if __name__ == "__main__":
    unittest.main()

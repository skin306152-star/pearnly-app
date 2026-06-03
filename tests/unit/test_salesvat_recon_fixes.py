# -*- coding: utf-8 -*-
"""
销项税对账 UI 实测回归(2026-05-25)· 锁定 P0-1 / P1-2 / P1-4。

- P0-1 分公司:空分公司 ≡ 00000(总部)· 正常发票(报告侧 00000)不再被误判"分公司差异"·
  但真实支店码(00001)vs 00000 仍正常报差。
- P1-2 混月份:多份报告 meta={} 时从行 report_date 推主导期间 · 跨文件不同月 → 拦截。
- P1-4 OCR 失败计数:salesvat handler raw_data 输出 invoice_ocr_failed_count 等解析层真值。
"""

import unittest
from unittest import mock

from services.vat import vat_excel_export as VEX


class BranchNormalizationTests(unittest.TestCase):
    """P0-1 · _diff_dims 分公司维度。其余维度都喂相同值以隔离 branch。"""

    def _base(self, inv_branch, rep_branch):
        inv = {
            "invoice_no": "A1",
            "invoice_date": "2026-01-05",
            "buyer_tax_id": "1234567890123",
            "buyer_name": "Alpha Co",
            "buyer_branch": inv_branch,
        }
        rep = {
            "report_invoice_no": "A1",
            "report_date": "2026-01-05",
            "report_buyer_tax_id": "1234567890123",
            "report_buyer_name": "Alpha Co",
            "report_buyer_branch": rep_branch,
        }
        return VEX._diff_dims(inv, rep)

    # 注:_diff_dims 预初始化所有维度键为 "" · 有差异才填值 · 故断言「值是否为空」而非键是否存在
    def test_empty_invoice_branch_vs_report_hq_no_diff(self):
        # 核心回归:发票无分公司(空)· 报告标准化成 00000 → 不应报分公司差异
        out = self._base("", "00000")
        self.assertEqual(out.get("branch", ""), "", f"空分公司被误判差异: {out}")

    def test_both_empty_no_diff(self):
        out = self._base("", "")
        self.assertEqual(out.get("branch", ""), "")

    def test_real_subbranch_vs_hq_still_diff(self):
        # 真实支店码 00001 vs 总部 00000 → 必须报差(不被归一掩盖)
        out = self._base("00001", "00000")
        self.assertNotEqual(out.get("branch", ""), "")

    def test_hq_synonym_vs_empty_no_diff(self):
        out = self._base("สำนักงานใหญ่", "")
        self.assertEqual(out.get("branch", ""), "")


class DominantPeriodTests(unittest.TestCase):
    """P1-2 · _dominant_report_period:meta 优先 · 否则行日期众数。"""

    def test_meta_period_wins(self):
        p = {"meta": {"period_year": 2026, "period_month": 5}, "rows": []}
        self.assertEqual(VEX._dominant_report_period(p), (2026, 5))

    def test_derive_from_rows_when_meta_empty(self):
        p = {
            "meta": {},
            "rows": [
                {"report_date": "2026-06-01"},
                {"report_date": "2026-06-15"},
                {"report_date": "2026-05-30"},  # 噪声 · 少数
            ],
        }
        self.assertEqual(VEX._dominant_report_period(p), (2026, 6))

    def test_no_dates_returns_none(self):
        self.assertIsNone(VEX._dominant_report_period({"meta": {}, "rows": [{"report_date": ""}]}))


class MergeMixedPeriodTests(unittest.TestCase):
    """P1-2 · merge_vat_reports 跨文件混月份拦截(parse_vat_report 走 mock · 不碰 Gemini)。"""

    def _patch_parse(self, side_effect):
        # merge_vat_reports 拆到 vat_report_merge · parse_vat_report 在该模块命名空间解析
        p = mock.patch("services.vat.vat_report_merge.parse_vat_report", side_effect=side_effect)
        p.start()
        self.addCleanup(p.stop)

    def test_mixed_period_blocked(self):
        def fake(b, fn, api_key=None):
            month = 5 if "may" in fn else 6
            return {
                "ok": True,
                "rows": [{"report_date": f"2026-{month:02d}-10", "report_invoice_no": "X"}],
                "row_count": 1,
                "meta": {},
            }

        self._patch_parse(fake)
        res = VEX.merge_vat_reports(
            [{"filename": "may.pdf", "bytes": b"x"}, {"filename": "jun.pdf", "bytes": b"y"}]
        )
        self.assertFalse(res.get("ok"))
        self.assertIn("期间不一致", res.get("error", ""))

    def test_same_period_ok(self):
        def fake(b, fn, api_key=None):
            return {
                "ok": True,
                "rows": [
                    {"report_date": "2026-05-10", "report_invoice_no": "X"},
                    {"report_date": "2026-05-11", "report_invoice_no": "Y"},
                ],
                "row_count": 2,
                "meta": {},
            }

        self._patch_parse(fake)
        res = VEX.merge_vat_reports(
            [{"filename": "a.pdf", "bytes": b"x"}, {"filename": "b.pdf", "bytes": b"y"}]
        )
        self.assertTrue(res.get("ok"), res.get("error"))
        # meta 缺失也应回填期间(从行推导)
        self.assertEqual((res.get("period_year"), res.get("period_month")), (2026, 5))


class SalesvatOcrCountTests(unittest.TestCase):
    """P1-4 · run_salesvat raw_data 含 OCR 计数字段(2 张发票 · 1 张 OCR 失败)。"""

    def test_raw_data_has_ocr_counts(self):
        from services.recon_jobs import handlers

        captured = {}

        def _capture_create(**kw):
            captured.update(kw)
            return "task-uuid"

        with (
            mock.patch.object(
                VEX,
                "merge_vat_reports",
                return_value={
                    "ok": True,
                    "rows": [{"report_invoice_no": "A"}],
                    "row_count": 1,
                    "seller_name": "S",
                    "seller_tax_id": "1",
                    "period_year": 2026,
                    "period_month": 5,
                },
            ),
            mock.patch.object(
                VEX,
                "extract_invoices_parallel",
                return_value=[
                    {"ok": True, "filename": "i1.pdf"},
                    {"ok": False, "filename": "i2.pdf"},
                ],
            ),
            mock.patch.object(
                VEX,
                "build_excel",
                return_value=(
                    b"XLSX",
                    {"n_total": 1, "n_ok": 1, "n_diff": 0, "diff_amount_total": 0.0},
                ),
            ),
            mock.patch("routes.vat_excel_routes._save_excel_file", return_value="/tmp/x.xlsx"),
            mock.patch("core.db.create_vat_recon_task", side_effect=_capture_create),
            mock.patch("core.db.get_cursor"),
            mock.patch("core.db.get_latest_balance", return_value={"calibration_factor": 1.1}),
            mock.patch("core.db.log_ocr_cost"),
        ):
            import tempfile
            import os

            d = tempfile.mkdtemp()
            refs = []
            for role, name in [("invoice", "i1.pdf"), ("invoice", "i2.pdf"), ("report", "r.pdf")]:
                pth = os.path.join(d, name)
                with open(pth, "wb") as f:
                    f.write(b"x")
                refs.append({"path": pth, "filename": name, "role": role})
            params = {"user_id": "u1", "tenant_id": None, "lang": "th", "is_exempt": True}
            table, rid = handlers.run_salesvat(params, refs, None)

        self.assertEqual(table, "vat_recon_tasks")
        raw = captured.get("raw_data_json") or {}
        self.assertEqual(raw.get("invoice_file_count"), 2)
        self.assertEqual(raw.get("invoice_ocr_ok_count"), 1)
        self.assertEqual(raw.get("invoice_ocr_failed_count"), 1)
        self.assertIn("i2.pdf", raw.get("invoice_failed_files") or [])


if __name__ == "__main__":
    unittest.main()

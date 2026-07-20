# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
from unittest import mock

from core import db
from services.email_ingest import email_ingest
from services.ocr import entrypoints


class OcrEntrypointContractTests(unittest.TestCase):
    def test_all_entrypoints_share_supported_file_set(self):
        required = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".tiff",
            ".tif",
            ".bmp",
            ".gif",
            ".xlsx",
            ".xls",
            ".xlsm",
            ".csv",
            ".tsv",
            ".docx",
            ".doc",
            ".txt",
        }
        self.assertTrue(required.issubset(entrypoints.SUPPORTED_OCR_EXTENSIONS))
        self.assertEqual(email_ingest._SUPPORTED_EXTS, entrypoints.SUPPORTED_OCR_EXTENSIONS)

    def test_billing_quote_images_use_pdf_page_pricing(self):
        user = {"id": "u1", "tenant_id": "t1"}
        with mock.patch("core.db.get_billing_status_combined") as status:
            status.return_value = {
                "allowed": True,
                "is_exempt": False,
                "balance_thb": 100,
                "pages_used_this_month": 0,
            }
            quote = entrypoints.billing_quote(user, b"image-bytes", "invoice.png")
        self.assertTrue(quote["allowed"])
        self.assertEqual(quote["kind"], "pdf")
        self.assertEqual(quote["units"], 1)
        self.assertEqual(quote["page_count"], 1)

    def test_billing_quote_tables_use_excel_character_pricing(self):
        user = {"id": "u1", "tenant_id": "t1"}
        with (
            mock.patch("core.db.get_billing_status_combined") as status,
            mock.patch("core.db._excel_char_count_estimate", return_value=1234) as chars,
        ):
            status.return_value = {
                "allowed": True,
                "is_exempt": False,
                "balance_thb": 100,
                "pages_used_this_month": 0,
            }
            quote = entrypoints.billing_quote(user, b"a,b\n1,2\n", "invoice.csv")
        self.assertTrue(quote["allowed"])
        self.assertEqual(quote["kind"], "excel")
        self.assertEqual(quote["units"], 1234)
        chars.assert_called_once()

    def test_charge_successful_ocr_skips_cache_or_exempt_only_by_quote(self):
        user = {"id": "u1", "tenant_id": "t1"}
        with mock.patch("core.db.charge_ocr_async") as charge:
            entrypoints.charge_successful_ocr(
                user,
                {"is_exempt": False, "kind": "pdf", "units": 2},
                "hid-1",
                "OCR test",
            )
        charge.assert_called_once_with("u1", "t1", "pdf", 2, "hid-1", "OCR test")

        with mock.patch("core.db.charge_ocr_async") as charge:
            entrypoints.charge_successful_ocr(
                user,
                {"is_exempt": True, "kind": "pdf", "units": 2},
                "hid-1",
                "OCR test",
            )
        charge.assert_not_called()

    def test_duplicate_semantics_document_cache_as_only_no_charge_path(self):
        self.assertTrue(hasattr(db, "find_ocr_by_hash"))
        self.assertTrue(hasattr(entrypoints, "get_cached_history"))


class RunPipelineTaskPolicyTests(unittest.TestCase):
    """D3:run_pipeline_for_file 的 task 参数定「引擎档生效域」(→ OcrRequest.policy_task),不换
    handler(task 恒 invoice)。facade 只搬运;引擎档按 policy_task 生效由 controller 落实(见
    controller 契约测试),task 合法性也由 controller 一处校验。"""

    def _capture_request(self, **kwargs):
        """跑一次 run_pipeline_for_file,返回它构造并传给 controller.run 的 OcrRequest。"""
        with mock.patch("services.ocr.controller.run") as run:
            run.return_value = mock.Mock(data="pipeline-result")
            out = entrypoints.run_pipeline_for_file(b"x", "a.png", api_key="k", **kwargs)
        self.assertEqual(out, "pipeline-result")
        req = run.call_args[0][0]
        # handler 始终 invoice:OcrRequest.task 恒 invoice(产物形状不变)。
        self.assertEqual(req.task, "invoice")
        return req

    def test_default_task_resolves_engine_under_invoice(self):
        req = self._capture_request()
        self.assertEqual(req.policy_task, "invoice")  # 默认 task=invoice → policy_task=invoice

    def test_bank_statement_task_becomes_policy_task(self):
        req = self._capture_request(task="bank_statement", document_type="bank_statement")
        self.assertEqual(req.policy_task, "bank_statement")

    def test_plan_context_flows_into_request(self):
        req = self._capture_request(task="invoice", plan_code="L", is_exempt=True)
        self.assertEqual((req.plan_code, req.is_exempt), ("L", True))

    def test_unknown_task_rejected(self):
        # 非法 task 经 policy_task 由 controller 校验(handler task 恒 invoice 合法)→ ValueError。
        with self.assertRaises(ValueError):
            entrypoints.run_pipeline_for_file(b"x", "a.png", api_key="k", task="nope")

    def test_web_upload_checks_cache_before_balance_gate(self):
        # 识别核心 2026-06-30 抽到 services/ocr/recognize/core.py(缺口④ · 同步/异步单一事实源);
        # 缓存先于余额闸的顺序契约随之跟到新文件,网页同步与异步 worker 同享此顺序。
        core_py = Path(__file__).resolve().parents[2] / "services" / "ocr" / "recognize" / "core.py"
        src = core_py.read_text(encoding="utf-8")
        cache_pos = src.index("cached = _ocr_get_cached(user, file_hash")
        billing_pos = src.index('db.get_billing_status_combined(str(user.get("id")), _tid(user))')
        self.assertLess(
            cache_pos,
            billing_pos,
            "缓存命中是唯一不扣费路径,必须先于余额闸;否则 0 余额用户无法复用旧结果。",
        )


if __name__ == "__main__":
    unittest.main()

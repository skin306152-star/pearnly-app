# -*- coding: utf-8 -*-
"""对账车道的成本归因接线(2026-08-13 修账:recon 行 tenant/user=NULL、pages=0)。

锁定两根线:
  ① worker 把任务 owner(params.user_id/tenant_id)设进网关归因 contextvar,
     handler(及 _parallel 子线程)里的 AI 调用落账带 owner,且不改写内部 task 标签;
  ② 对账三车道的 facade 把文档物理页数填进 usage_context,ai_usage 的每页成本有分母。
"""

import unittest
from types import SimpleNamespace
from unittest import mock

from services.ai_gateway import attribution
from services.cost import usage_context as uc
from services.recon_jobs import worker


class WorkerOwnerAttributionTests(unittest.TestCase):
    def tearDown(self):
        self.assertIsNone(attribution.current(), "归因上下文泄漏到了下一个用例")

    def test_handler_runs_with_owner_attribution(self):
        seen = {}

        def handler(params, input_ref, progress_cb):
            seen["attr"] = attribution.current()
            return ("t", 1)

        job = {"id": "job-9", "input_ref": [], "params": {}}
        params = {"user_id": "u1", "tenant_id": "t1"}
        result = worker._run_handler_attributed(handler, params, job, None)
        self.assertEqual(result, ("t", 1))
        self.assertEqual(seen["attr"]["tenant_id"], "t1")
        self.assertEqual(seen["attr"]["user_id"], "u1")
        self.assertEqual(seen["attr"]["trace_id"], "job-9")
        # task=None:ocr.image_json 这类工程标签必须保留,不许被压成业务名
        self.assertIsNone(seen["attr"]["task"])

    def test_attribution_reset_after_handler_raises(self):
        def handler(params, input_ref, progress_cb):
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            worker._run_handler_attributed(
                handler, {"user_id": "u1", "tenant_id": "t1"}, {"id": "j"}, None
            )
        self.assertIsNone(attribution.current())

    def test_owner_propagates_into_parallel_workers(self):
        # handler 内的 _parallel 走 submit_ctx(提交时刻快照):owner 必须跟进子线程,
        # 否则并行解析的每一笔 AI 调用照旧落成无主行。
        from services.recon_jobs._handler_common import _parallel

        def handler(params, input_ref, progress_cb):
            return _parallel(lambda _x: (attribution.current() or {}).get("tenant_id"), [1, 2])

        got = worker._run_handler_attributed(
            handler, {"user_id": "u1", "tenant_id": "t1"}, {"id": "j"}, None
        )
        self.assertEqual(got, ["t1", "t1"])

    def test_missing_owner_leaves_attribution_empty_but_runs(self):
        seen = {}

        def handler(params, input_ref, progress_cb):
            seen["attr"] = attribution.current()
            return ("t", 2)

        result = worker._run_handler_attributed(handler, {}, {"id": None}, None)
        self.assertEqual(result, ("t", 2))
        self.assertIsNone(seen["attr"]["tenant_id"])
        self.assertIsNone(seen["attr"]["user_id"])


class FacadePagesAttributionTests(unittest.TestCase):
    """facade 进 controller 前,usage_context 必须已带 entry/doc/pages。"""

    def _capture_run(self, captured):
        def fake_run(req):
            captured["usage"] = uc.current()
            return SimpleNamespace(data={"ok": True}, task=req.task, elapsed_ms=1)

        return fake_run

    def test_bank_statement_facade_fills_pages(self):
        from services.recon import bank_recon_facades as f

        captured = {}
        with (
            mock.patch("services.ocr.controller.run", side_effect=self._capture_run(captured)),
            mock.patch.object(f, "doc_page_count", return_value=4),
        ):
            f.parse_bank_statement_pdf(b"x", "stmt.pdf")
        self.assertEqual(
            captured["usage"],
            {"entry_point": "bank_recon", "doc_type": "bank_statement", "pages": 4},
        )

    def test_bank_gl_facade_fills_pages(self):
        from services.recon import bank_recon_facades as f

        captured = {}
        with (
            mock.patch("services.ocr.controller.run", side_effect=self._capture_run(captured)),
            mock.patch.object(f, "doc_page_count", return_value=2),
        ):
            f.parse_gl(b"x", "gl.pdf")
        self.assertEqual(
            captured["usage"],
            {"entry_point": "bank_recon", "doc_type": "gl_ledger", "pages": 2},
        )

    def test_vat_report_facade_fills_pages(self):
        from services.vat import vat_report_parser as vp

        captured = {}
        with (
            mock.patch("services.ocr.controller.run", side_effect=self._capture_run(captured)),
            mock.patch("services.ocr.pdf_utils.doc_page_count", return_value=3),
        ):
            vp.parse_vat_report(b"x", "report.pdf")
        self.assertEqual(
            captured["usage"],
            {"entry_point": "vat_recon", "doc_type": "vat_report", "pages": 3},
        )

    def test_glvat_gl_facade_fills_pages(self):
        from services.recon import gl_vat_parse_excel as g

        captured = {}
        with (
            mock.patch("services.ocr.controller.run", side_effect=self._capture_run(captured)),
            mock.patch("services.ocr.pdf_utils.doc_page_count", return_value=5),
        ):
            g.parse_gl(b"x", "gl.pdf")
        self.assertEqual(
            captured["usage"],
            {"entry_point": "vat_recon", "doc_type": "gl_vat", "pages": 5},
        )

    def test_table_file_keeps_pages_unknown(self):
        # Excel 按字符计费:pages=None 落 NULL 归「页数未知」,不许拿 0 冒充
        from services.recon import bank_recon_facades as f

        captured = {}
        with mock.patch("services.ocr.controller.run", side_effect=self._capture_run(captured)):
            f.parse_bank_statement_pdf(b"x", "stmt.xlsx")
        self.assertIsNone(captured["usage"]["pages"])


if __name__ == "__main__":
    unittest.main()

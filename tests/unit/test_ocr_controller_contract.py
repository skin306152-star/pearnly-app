# -*- coding: utf-8 -*-
"""OCR 统一编排(contracts/policy/controller/handlers)+ 旧入口 facade 契约测试。

守的是「行为不变」:facade 原样透传 handler 返回值与参数,
错误语义(未知扩展名 ValueError / 未知 task KeyError)不变。
"""

import unittest
from unittest import mock

from services.ocr import controller, policy
from services.ocr.contracts import OCR_TASKS, OcrRequest


def _req(task, filename="a.pdf", **kw):
    return OcrRequest(task=task, file_bytes=b"x", filename=filename, **kw)


class PolicyTest(unittest.TestCase):
    def test_all_tasks_declared(self):
        self.assertEqual(set(policy.POLICIES), set(OCR_TASKS))

    def test_unknown_task_raises(self):
        with self.assertRaises(KeyError):
            policy.policy_for("nope")

    def test_primary_model_resolves_by_tier(self):
        from services.ocr import gemini_models

        self.assertEqual(policy.primary_model("id_card"), gemini_models.flash_lite())
        self.assertEqual(policy.primary_model("invoice"), gemini_models.flash())
        for task in OCR_TASKS:
            self.assertTrue(policy.primary_model(task))


class ControllerTest(unittest.TestCase):
    def test_unknown_task_raises_before_dispatch(self):
        with self.assertRaises(KeyError):
            controller.run(_req("nope"))

    def test_invoice_dispatch_pdf_passes_max_pages(self):
        sentinel = object()
        with mock.patch(
            "services.ocr.handlers.invoice.run_on_pdf_bytes", return_value=sentinel
        ) as m:
            res = controller.run(_req("invoice", "bill.PDF", options={"max_pages": 7}))
        self.assertIs(res.data, sentinel)
        self.assertEqual(res.task, "invoice")
        self.assertGreaterEqual(res.elapsed_ms, 0)
        m.assert_called_once_with(b"x", max_pages=7, api_key=None)

    def test_invoice_dispatch_image_and_table(self):
        with mock.patch(
            "services.ocr.handlers.invoice.run_on_image_bytes", return_value="img"
        ) as mi:
            self.assertEqual(controller.run(_req("invoice", "r.jpg")).data, "img")
        mi.assert_called_once_with(b"x", api_key=None)
        with mock.patch(
            "services.ocr.handlers.invoice.run_on_table_bytes", return_value="tbl"
        ) as mt:
            self.assertEqual(controller.run(_req("invoice", "r.xlsx")).data, "tbl")
        mt.assert_called_once_with(b"x", filename="r.xlsx", api_key=None)

    def test_invoice_unsupported_ext_raises_valueerror(self):
        with self.assertRaises(ValueError):
            controller.run(_req("invoice", "notes.zip"))


class FacadeTest(unittest.TestCase):
    """旧入口签名不变,经 controller 透传到原实现。"""

    def test_run_pipeline_for_file(self):
        from services.ocr.entrypoints import run_pipeline_for_file

        with mock.patch("services.ocr.handlers.invoice.run_on_image_bytes", return_value="ok") as m:
            self.assertEqual(run_pipeline_for_file(b"i", "a.png", api_key="k"), "ok")
        m.assert_called_once_with(b"i", api_key="k")

    def test_extract_thai_id_card(self):
        from services.ocr import id_card_extract

        with mock.patch.object(
            id_card_extract, "_extract_id_card_impl", return_value={"ok": 1}
        ) as m:
            self.assertEqual(id_card_extract.extract_thai_id_card(b"img", "key"), {"ok": 1})
        m.assert_called_once_with(b"img", "key")

    def test_parse_bank_statement_pdf(self):
        from services.recon import bank_recon_v2

        with mock.patch.object(
            bank_recon_v2, "_parse_bank_statement_impl", return_value={"ok": True}
        ) as m:
            out = bank_recon_v2.parse_bank_statement_pdf(b"p", "s.pdf", "key", tenant_id="t1")
        self.assertEqual(out, {"ok": True})
        m.assert_called_once_with(b"p", "s.pdf", api_key="key", tenant_id="t1")

    def test_parse_gl(self):
        from services.recon import bank_recon_v2

        with mock.patch.object(bank_recon_v2, "_parse_gl_impl", return_value={"ok": True}) as m:
            out = bank_recon_v2.parse_gl(b"g", "gl.pdf", "1010", "key", tenant_id="t2")
        self.assertEqual(out, {"ok": True})
        m.assert_called_once_with(
            b"g", "gl.pdf", account_code="1010", api_key="key", tenant_id="t2"
        )

    def test_parse_vat_report(self):
        from services.vat import vat_report_parser

        with mock.patch.object(
            vat_report_parser, "_parse_vat_report_impl", return_value={"ok": True, "rows": []}
        ) as m:
            out = vat_report_parser.parse_vat_report(b"v", "vat.pdf", api_key="key")
        self.assertEqual(out, {"ok": True, "rows": []})
        m.assert_called_once_with(b"v", "vat.pdf", api_key="key")


if __name__ == "__main__":
    unittest.main()

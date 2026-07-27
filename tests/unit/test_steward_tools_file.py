# -*- coding: utf-8 -*-
"""吃附件的两只工具(services/steward/tools_file.py)+ 它们的注册面与文案。

锁的是「哪个文件由代码定,不由模型定」这条:执行侧必须恰好拿到一件料,多了少了、
不是自己传的、盘上取不回来 —— 一律返错误码,绝不自己挑一个跑。
"""

from __future__ import annotations

import io
import tempfile
import unittest
from unittest import mock

from services.steward import attachments, copy, registry, tools, tools_file
from services.steward.registry import ToolContext
from tests.unit._route_contract_fakes import CurCM, FakeCur

_USER = {"id": "u1", "tenant_id": "t-1"}


def _ctx(ids=("a1",)):
    return ToolContext(
        user=_USER, tenant_id="t-1", user_id="u1", session_id="s-1", attachment_ids=tuple(ids)
    )


def _row(path, rid="a1", user_id="u1", name="book.xlsx"):
    return {"id": rid, "user_id": user_id, "original_name": name, "file_ref": str(path)}


def _xlsx_bytes() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["date", "description", "amount"])
    ws.append(["2026-06-01", "sale", 100])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class _Sandbox(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(attachments, "_BASE", self._dir.name)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._dir.cleanup()

    def _land(self, content: bytes, name="book.xlsx"):
        return attachments.save(content, tenant_id="t-1", session_id="s-1", original_name=name)

    def _with_rows(self, rows):
        return (
            mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
            mock.patch.object(attachments, "list_by_ids", return_value=rows),
        )


class SelectionTests(_Sandbox):
    def test_no_attachment_is_refused(self):
        res = tools_file.file_convert(_ctx(ids=()), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_file.ERR_NO_ATTACHMENT)

    def test_two_attachments_are_refused_instead_of_picking_one(self):
        res = tools_file.file_convert(_ctx(ids=("a1", "a2")), {})
        self.assertEqual(res.error_code, tools_file.ERR_MANY_ATTACHMENTS)
        self.assertEqual(res.data["n"], 2)

    def test_someone_elses_attachment_is_invisible(self):
        path = self._land(_xlsx_bytes())
        p1, p2 = self._with_rows([_row(path, user_id="u2")])
        with p1, p2:
            res = tools_file.file_convert(_ctx(), {})
        self.assertEqual(res.error_code, tools_file.ERR_NO_ATTACHMENT)

    def test_path_outside_the_session_is_refused(self):
        p1, p2 = self._with_rows([_row("/etc/passwd")])
        with p1, p2:
            res = tools_file.file_convert(_ctx(), {})
        self.assertEqual(res.error_code, tools_file.ERR_UNREADABLE)


class FileConvertTests(_Sandbox):
    def test_excel_converts_and_registers_a_downloadable_artifact(self):
        path = self._land(_xlsx_bytes())
        p1, p2 = self._with_rows([_row(path)])
        with (
            p1,
            p2,
            mock.patch.object(attachments, "insert", return_value={"id": "out-1"}) as insert,
        ):
            res = tools_file.file_convert(_ctx(), {})
        self.assertTrue(res.ok)
        self.assertEqual(res.data["download"]["attachment_id"], "out-1")
        self.assertEqual(res.data["download"]["name"], "book.xlsx")
        self.assertEqual(insert.call_args.kwargs["status"], attachments.STATUS_ARTIFACT)
        self.assertGreaterEqual(res.data["row_count"], 1)

    def test_a_failed_artifact_save_does_not_undo_a_good_conversion(self):
        path = self._land(_xlsx_bytes())
        p1, p2 = self._with_rows([_row(path)])
        with p1, p2, mock.patch.object(attachments, "insert", side_effect=RuntimeError("db")):
            res = tools_file.file_convert(_ctx(), {})
        self.assertTrue(res.ok)
        self.assertEqual(res.data["download"], {})

    def test_rejected_conversion_never_returns_a_half_table(self):
        path = self._land(b"%PDF-not-really", name="scan.pdf")
        p1, p2 = self._with_rows([_row(path, name="scan.pdf")])
        with (
            p1,
            p2,
            mock.patch(
                "services.fileconv.convert.convert_pdf",
                return_value=mock.Mock(status="no_text_layer", tables=[], issues=[]),
            ),
        ):
            res = tools_file.file_convert(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_file.ERR_CONVERT_REJECTED)


class VatReportCheckTests(_Sandbox):
    _ROWS = [
        {"row_no": 1, "report_invoice_no": "IV69/001", "report_date": "2026-06-01",
         "report_buyer_tax_id": "0105500000001", "report_buyer_name": "A",
         "report_amount_pre_vat": 100, "report_vat_amount": 7, "report_amount": 107},
        {"row_no": 2, "report_invoice_no": "IV69/003", "report_date": "2026-06-02",
         "report_buyer_tax_id": "0105500000001", "report_buyer_name": "A",
         "report_amount_pre_vat": 200, "report_vat_amount": 14, "report_amount": 214},
    ]  # fmt: skip

    def test_missing_number_is_named_and_money_stays_exact(self):
        path = self._land(b"report", name="vat.xlsx")
        p1, p2 = self._with_rows([_row(path, name="vat.xlsx")])
        with (
            p1,
            p2,
            mock.patch(
                "services.vat.vat_report_parser.parse_vat_report",
                return_value={"ok": True, "rows": self._ROWS},
            ),
        ):
            res = tools_file.vat_report_check(_ctx(), {})
        self.assertTrue(res.ok)
        self.assertEqual(res.data["row_count"], 2)
        self.assertEqual(res.data["missing_count"], 1)
        self.assertEqual(res.data["missing"][0]["missing"], "2")
        self.assertEqual(res.data["period"], "2026-06")
        # 钱出线是定点字符串(Decimal 语义不落 float,不生税额毛刺)
        self.assertEqual(res.data["grand_total"]["vat_total"], "21")

    def test_unparsable_report_says_so_instead_of_returning_zero_rows(self):
        path = self._land(b"junk", name="vat.pdf")
        p1, p2 = self._with_rows([_row(path, name="vat.pdf")])
        with (
            p1,
            p2,
            mock.patch(
                "services.vat.vat_report_parser.parse_vat_report",
                return_value={"ok": False, "rows": [], "error": "unsupported"},
            ),
        ):
            res = tools_file.vat_report_check(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_file.ERR_REPORT_UNPARSED)


class RegistrationTests(unittest.TestCase):
    def test_both_tools_are_readonly_and_need_no_authorization_card(self):
        for name in registry.ATTACHMENT_TOOLS:
            spec = registry.get(name)
            self.assertIsNotNone(spec)
            self.assertTrue(spec.readonly)
            self.assertFalse(registry.requires_authorization(spec))
            self.assertEqual(spec.slots, ())  # 附件不是参数槽,模型不选文件
            self.assertEqual(spec.timeout_s, registry.FILE_TOOL_TIMEOUT_S)

    def test_both_tools_are_wired_to_an_executor(self):
        for name in registry.ATTACHMENT_TOOLS:
            self.assertIn(name, tools._HANDLERS)

    def test_replies_and_errors_render_in_both_languages(self):
        convert = {
            "filename": "gl.pdf", "doc_type": "gl_ledger", "row_no": 1,
            "row_count": 12, "issue_count": 2, "issues": [], "download": {},
        }  # fmt: skip
        check = {"filename": "vat.xlsx", "period": "2026-06", "row_count": 9}
        for lang in ("zh", "th"):
            for tool, data in (
                (registry.FILE_CONVERT, convert),
                (registry.VAT_REPORT_CHECK, check),
            ):
                text = copy.reply(tool, data, lang)
                self.assertTrue(text)
                self.assertNotIn("{", text)
            for code in (
                tools_file.ERR_NO_ATTACHMENT,
                tools_file.ERR_MANY_ATTACHMENTS,
                tools_file.ERR_UNREADABLE,
                tools_file.ERR_CONVERT_REJECTED,
                tools_file.ERR_REPORT_UNPARSED,
            ):
                text = copy.error(code, {"n": 2, "filename": "a.pdf", "status": "x"}, lang)
                self.assertTrue(text)
                self.assertNotIn("{", text)

    def test_download_link_points_at_the_real_endpoint(self):
        arts = copy.artifacts(
            registry.FILE_CONVERT,
            {"download": {"attachment_id": "a-1"}, "issues": []},
            "zh",
        )
        self.assertEqual([a["href"] for a in arts], ["/api/ai/steward/attachments/a-1/download"])


if __name__ == "__main__":
    unittest.main()

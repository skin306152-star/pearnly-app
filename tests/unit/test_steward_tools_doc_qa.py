# -*- coding: utf-8 -*-
"""读文问答(services/steward/tools_doc_qa.py)+ 它的注册面与文案。

锁五件:①格式分流(pdf 有/无文字层、表格族、拒绝类型)全走确定性规则,不猜;②提示词
写死「只答文中写了什么 / 不许算数 / 算数引去 table_generate」三条命门;③模型输出的引用
必须真能在送去的原文里找到,找不到的一条都不许端上桌;④注册表闭集里的位置(附件工具/
模型调用工具/正确 handler);⑤扫描件 PDF/图片的 OCR 计费网关(OcrGateTests)—— 没有
model_ok 绝不调 convert_pdf/convert_image,有文字层的 PDF 无论 model_ok 是什么值都绝不
落 OCR(钱路防线,mock 断言调用次数,不只看返回值)。
"""

from __future__ import annotations

import io
import tempfile
import unittest
from unittest import mock

from services.agent.contracts import ToolResult
from services.ai_gateway.tasks import ProviderOutcome
from services.steward import attachments, copy, registry, store, tools, tools_doc_qa
from services.steward.registry import ToolContext
from tests.unit._route_contract_fakes import CurCM, FakeCur

_USER = {"id": "u1", "tenant_id": "t-1"}


def _ctx(ids=("a1",)):
    return ToolContext(
        user=_USER, tenant_id="t-1", user_id="u1", session_id="s-1", attachment_ids=tuple(ids)
    )


def _row(path, rid="a1", user_id="u1", name="doc.pdf", message_id="m-1"):
    return {"id": rid, "user_id": user_id, "original_name": name, "file_ref": str(path)}


def _xlsx_bytes() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["date", "amount"])
    ws.append(["2026-06-01", 100])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _outcome(data):
    return ProviderOutcome(ok=True, data=data)


def _ocr_table():
    from services.fileconv.model import Table

    return Table(name="Table", columns=["date", "amount"], rows=[["2026-06-01", "500"]])


def _ocr_convert_result():
    from services.fileconv.model import STATUS_OK, ConvertResult

    return ConvertResult(
        doc_type="generic_table", status=STATUS_OK, source_name="x", tables=[_ocr_table()]
    )


class _Sandbox(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(attachments, "_BASE", self._dir.name)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._dir.cleanup()

    def _land(self, content: bytes, name="doc.pdf"):
        return attachments.save(content, tenant_id="t-1", session_id="s-1", original_name=name)

    def _with_rows(self, rows, question="这份合同的付款期限是多久"):
        return (
            mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
            mock.patch.object(attachments, "list_by_ids", return_value=rows),
            mock.patch.object(store, "message_text", return_value=question),
        )


class DispatchTests(_Sandbox):
    """格式分流:走桩,不真解析 PDF/Excel(那两条已由 fileconv 自己的测试覆盖)。"""

    def test_pdf_without_text_layer_needs_model_confirmation_first(self):
        """无文字层不再是永久拒绝——它现在是"要过一次模型",没 model_ok 就停在这里
        (真正的"绝不调 convert_pdf"钱路断言在 OcrGateTests,这里只锁错误码)。"""
        path = self._land(b"%PDF-scan", name="scan.pdf")
        p1, p2, p3 = self._with_rows([_row(path, name="scan.pdf")])
        with (
            p1,
            p2,
            p3,
            mock.patch("services.fileconv.text_layer.extract_pages", return_value=None),
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_doc_qa.ERR_NEEDS_MODEL)
        self.assertEqual(res.data["filename"], "scan.pdf")

    def test_pdf_with_text_layer_reaches_the_model(self):
        path = self._land(b"%PDF-1.4 real text", name="contract.pdf")
        p1, p2, p3 = self._with_rows([_row(path, name="contract.pdf")])
        pages = [
            "第一页正文:本合同约定,买方应于收到发票之日起 30 天内完成付款,付款期限不得延长。" * 2,
            "第二页是双方签字页,盖章确认,此处无其他条款约定。" * 2,
        ]
        with (
            p1,
            p2,
            p3,
            mock.patch("services.fileconv.text_layer.extract_pages", return_value=pages),
            mock.patch.object(
                tools_doc_qa,
                "ask_model",
                return_value=_outcome(
                    {
                        "answer": "付款期限为收到发票之日起 30 天。",
                        "citations": [{"page": 1, "quote": "30 天内完成付款"}],
                    }
                ),
            ),
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {})
        self.assertTrue(res.ok)
        self.assertEqual(res.data["answer"], "付款期限为收到发票之日起 30 天。")
        self.assertEqual(res.data["citations"][0]["page"], 1)

    def test_xlsx_is_rendered_to_text_grid_and_reaches_the_model(self):
        path = self._land(_xlsx_bytes(), name="book.xlsx")
        p1, p2, p3 = self._with_rows([_row(path, name="book.xlsx")], question="6 月 1 日卖了多少")
        with (
            p1,
            p2,
            p3,
            mock.patch.object(
                tools_doc_qa,
                "ask_model",
                return_value=_outcome({"answer": "100", "citations": []}),
            ) as ask,
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {})
        self.assertTrue(res.ok)
        prompt = ask.call_args.args[0]
        self.assertIn("100", prompt)  # 网格文本真的把样例数据带进了提示词

    def test_docx_is_refused_with_a_supported_list(self):
        path = self._land(b"docx-bytes", name="note.docx")
        p1, p2, p3 = self._with_rows([_row(path, name="note.docx")])
        with p1, p2, p3:
            res = tools_doc_qa.doc_read_qa(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_doc_qa.ERR_UNSUPPORTED_TYPE)
        self.assertEqual(res.data["ext"], ".docx")

    def test_no_question_is_refused_before_touching_the_model(self):
        path = self._land(b"%PDF-1.4", name="a.pdf")
        p1, p2, p3 = self._with_rows([_row(path, name="a.pdf")], question="")
        with (
            p1,
            p2,
            p3,
            mock.patch("services.fileconv.text_layer.extract_pages", return_value=["x" * 200]),
            mock.patch.object(tools_doc_qa, "ask_model") as ask,
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_doc_qa.ERR_NO_QUESTION)
        ask.assert_not_called()


class OcrGateTests(_Sandbox):
    """扫描件 PDF / 图片走与 file_convert 同一条 OCR 计费轨,但要先有 model_ok 这张凭据。
    四条钱路防线:①没 model_ok 绝不调 convert_pdf/convert_image;②有 model_ok 恰好调一次;
    ③引用核验/禁算数逻辑不变(与 ParseAnswerTests/PromptContractTests 共用同一份,这里不
    重复断言,只跑一次端到端确认没被绕开);④有文字层的 PDF 无论 model_ok 是什么值都绝不
    落 OCR。"""

    def test_scanned_pdf_without_model_ok_never_calls_convert_pdf(self):
        path = self._land(b"%PDF-scan", name="scan.pdf")
        p1, p2, p3 = self._with_rows([_row(path, name="scan.pdf")])
        with (
            p1,
            p2,
            p3,
            mock.patch("services.fileconv.text_layer.extract_pages", return_value=None),
            mock.patch("services.fileconv.convert.convert_pdf") as convert,
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_doc_qa.ERR_NEEDS_MODEL)
        convert.assert_not_called()

    def test_scanned_pdf_with_model_ok_calls_convert_pdf_once_and_answers(self):
        path = self._land(b"%PDF-scan", name="scan.pdf")
        p1, p2, p3 = self._with_rows([_row(path, name="scan.pdf")], question="总金额是多少")
        with (
            p1,
            p2,
            p3,
            mock.patch("services.fileconv.text_layer.extract_pages", return_value=None),
            mock.patch(
                "services.fileconv.convert.convert_pdf", return_value=_ocr_convert_result()
            ) as convert,
            mock.patch.object(
                tools_doc_qa,
                "ask_model",
                return_value=_outcome(
                    {"answer": "500", "citations": [{"page": 1, "quote": "500"}]}
                ),
            ) as ask,
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {"model_ok": True})
        self.assertTrue(res.ok)
        convert.assert_called_once()
        self.assertEqual(convert.call_args.kwargs["tenant_id"], "t-1")
        self.assertIn("500", ask.call_args.args[0])
        self.assertEqual(len(res.data["citations"]), 1)  # 引用核验对 OCR 出的页照样生效

    def test_image_without_model_ok_never_calls_convert_image(self):
        path = self._land(b"\x89PNG-bytes", name="receipt.png")
        p1, p2, p3 = self._with_rows([_row(path, name="receipt.png")])
        with (
            p1,
            p2,
            p3,
            mock.patch("services.fileconv.convert.convert_image") as convert,
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_doc_qa.ERR_NEEDS_MODEL)
        convert.assert_not_called()

    def test_image_with_model_ok_calls_convert_image_once_and_answers(self):
        path = self._land(b"\x89PNG-bytes", name="receipt.png")
        p1, p2, p3 = self._with_rows([_row(path, name="receipt.png")], question="总金额是多少")
        with (
            p1,
            p2,
            p3,
            mock.patch(
                "services.fileconv.convert.convert_image", return_value=_ocr_convert_result()
            ) as convert,
            mock.patch.object(
                tools_doc_qa, "ask_model", return_value=_outcome({"answer": "500", "citations": []})
            ),
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {"model_ok": True})
        self.assertTrue(res.ok)
        convert.assert_called_once()

    def test_pdf_with_text_layer_never_touches_ocr_even_with_model_ok(self):
        path = self._land(b"%PDF-1.4 real text", name="contract.pdf")
        p1, p2, p3 = self._with_rows([_row(path, name="contract.pdf")])
        with (
            p1,
            p2,
            p3,
            mock.patch(
                "services.fileconv.text_layer.extract_pages", return_value=["第一页正文" * 20]
            ),
            mock.patch("services.fileconv.convert.convert_pdf") as convert,
            mock.patch.object(
                tools_doc_qa, "ask_model", return_value=_outcome({"answer": "x", "citations": []})
            ),
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {"model_ok": True})
        self.assertTrue(res.ok)
        convert.assert_not_called()

    def test_ocr_rejection_status_is_reported_not_swallowed(self):
        """OCR 桥判读不全(截断/不可用)——绝不出半截文本假装答得出来。"""
        path = self._land(b"\x89PNG-bytes", name="receipt.png")
        p1, p2, p3 = self._with_rows([_row(path, name="receipt.png")])
        with (
            p1,
            p2,
            p3,
            mock.patch(
                "services.fileconv.convert.convert_image",
                return_value=mock.Mock(status="ocr_incomplete", tables=[]),
            ),
        ):
            res = tools_doc_qa.doc_read_qa(_ctx(), {"model_ok": True})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_doc_qa.ERR_UNREADABLE_TABLE)


class PromptContractTests(unittest.TestCase):
    """命门:提示词写死"只答文中写了什么"+"不许算数"+"算数引去 table_generate"。"""

    def test_prompt_forbids_computing_or_inventing_numbers(self):
        text = tools_doc_qa.PROMPT
        self.assertIn("绝不能编", text)
        self.assertIn("绝不能算", text)
        self.assertIn("table_generate", text)

    def test_prompt_requires_page_citations(self):
        self.assertIn("citations", tools_doc_qa.PROMPT)
        self.assertIn("第几页", tools_doc_qa.PROMPT)


class SelectPagesTests(unittest.TestCase):
    def test_pages_with_more_keyword_hits_are_kept_first_under_a_tight_budget(self):
        # 第 2 页字面命中问题的字数远多于第 1 页,且单独就能撑满预算——预算耗尽后
        # 低相关的第 1 页应被整页排除,不是"凑一点点"。
        pages = ["无关内容 " * 20, "付款期限 " * 10]
        kept = tools_doc_qa.select_pages(pages, "付款期限是多久", max_chars=20)
        self.assertEqual([no for no, _ in kept], [2])

    def test_no_keyword_overlap_falls_back_to_original_order(self):
        pages = ["alpha content", "beta content"]
        kept = tools_doc_qa.select_pages(pages, "ไม่มีคำที่ตรงกันเลย", max_chars=1000)
        self.assertEqual([no for no, _ in kept], [1, 2])

    def test_a_single_oversized_page_is_truncated_in_place(self):
        kept = tools_doc_qa.select_pages(["x" * 100], "x", max_chars=10)
        self.assertEqual(len(kept[0][1]), 10)

    def test_empty_pages_yield_nothing(self):
        self.assertEqual(tools_doc_qa.select_pages([], "q", max_chars=100), [])


class ParseAnswerTests(unittest.TestCase):
    """模型输出核对:citation 的 quote 必须真能在对应页原文里找到,找不到就丢。"""

    def test_valid_citation_survives(self):
        kept = [(1, "付款期限为发票日起 30 天")]
        parsed = tools_doc_qa.parse_answer(
            {"answer": "30 天", "citations": [{"page": 1, "quote": "发票日起 30 天"}]}, kept
        )
        self.assertEqual(len(parsed["citations"]), 1)

    def test_citation_quote_not_in_the_source_text_is_dropped(self):
        kept = [(1, "这一页完全不提付款")]
        parsed = tools_doc_qa.parse_answer(
            {"answer": "找不到", "citations": [{"page": 1, "quote": "编出来的一句话"}]}, kept
        )
        self.assertEqual(parsed["citations"], [])

    def test_citation_page_not_among_the_pages_sent_is_dropped(self):
        kept = [(1, "这一页有内容")]
        parsed = tools_doc_qa.parse_answer(
            {"answer": "答案", "citations": [{"page": 9, "quote": "这一页有内容"}]}, kept
        )
        self.assertEqual(parsed["citations"], [])

    def test_non_dict_output_is_rejected(self):
        self.assertIsNone(tools_doc_qa.parse_answer("not a dict", []))

    def test_empty_answer_is_rejected(self):
        self.assertIsNone(tools_doc_qa.parse_answer({"answer": "", "citations": []}, []))

    def test_degenerate_repeated_character_answer_is_rejected(self):
        """reply_guard.sane 的复读闸:失控生成(如无限重复同一字符)不当答案端出去。"""
        parsed = tools_doc_qa.parse_answer({"answer": "0" * 50, "citations": []}, [])
        self.assertIsNone(parsed)


class RegistrationTests(unittest.TestCase):
    def test_registered_as_a_readonly_model_call_attachment_tool(self):
        spec = registry.get(registry.DOC_READ_QA)
        self.assertIsNotNone(spec)
        self.assertTrue(spec.readonly)
        self.assertEqual(spec.slots, ())
        self.assertEqual(spec.timeout_s, registry.FILE_TOOL_TIMEOUT_S)
        self.assertIn(registry.DOC_READ_QA, registry.ATTACHMENT_TOOLS)
        self.assertIn(registry.DOC_READ_QA, registry.MODEL_CALL_TOOLS)

    def test_wired_to_its_handler(self):
        self.assertIs(tools._HANDLERS[registry.DOC_READ_QA], tools_doc_qa.doc_read_qa)

    def test_appears_in_the_prompt_catalog(self):
        self.assertIn(registry.DOC_READ_QA, registry.catalog())

    def test_run_dispatches_through_the_closed_set(self):
        # tools._HANDLERS 在 import 时就绑死了函数对象,patch 模块属性对已建好的字典无效
        # (同 test_steward_registry.test_run_swallows_tool_exception 的先例:改字典条目)。
        original = tools._HANDLERS[registry.DOC_READ_QA]
        handler = mock.Mock(return_value=ToolResult(ok=True, data={"answer": "x"}))
        tools._HANDLERS[registry.DOC_READ_QA] = handler
        try:
            res = tools.run(registry.DOC_READ_QA, _ctx(), {})
        finally:
            tools._HANDLERS[registry.DOC_READ_QA] = original
        handler.assert_called_once()
        self.assertTrue(res.ok)

    def test_reply_is_the_verified_answer(self):
        text = copy.reply(registry.DOC_READ_QA, {"answer": "答案在此", "citations": []}, "zh")
        self.assertIn("答案在此", text)

    def test_reply_hints_when_there_is_no_citation_to_verify_against(self):
        text = copy.reply(registry.DOC_READ_QA, {"answer": "答案在此", "citations": []}, "zh")
        self.assertIn("谨慎采信", text)

    def test_citations_render_as_a_table_artifact_with_page_numbers(self):
        arts = copy.artifacts(
            registry.DOC_READ_QA,
            {"answer": "x", "citations": [{"page": 3, "quote": "原文片段"}]},
            "zh",
        )
        self.assertEqual(len(arts), 1)
        self.assertEqual(arts[0]["kind"], "table")
        self.assertEqual(arts[0]["rows"][0]["page"], 3)

    def test_errors_render_in_both_languages(self):
        for lang in ("zh", "th"):
            for code in (
                tools_doc_qa.ERR_NEEDS_MODEL,
                tools_doc_qa.ERR_UNREADABLE_TABLE,
                tools_doc_qa.ERR_UNSUPPORTED_TYPE,
                tools_doc_qa.ERR_NO_QUESTION,
                tools_doc_qa.ERR_MODEL_FAILED,
            ):
                text = copy.error(code, {"filename": "a.pdf", "status": "x", "ext": ".docx"}, lang)
                self.assertTrue(text)
                self.assertNotIn("{", text)


if __name__ == "__main__":
    unittest.main()

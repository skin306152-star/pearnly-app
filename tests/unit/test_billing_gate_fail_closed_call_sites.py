# -*- coding: utf-8 -*-
"""钱闸 fail-closed 的跨端点契约:查不出计费状态 → 503,且与「余额不足」402 分成两个码。

单一事实源是 services/billing/account_status.get_billing_status_combined(它自己的契约测试在
test_services_billing_account_status_contract.py)。这里锁的是**每个付费入口都真的照做**——
历史上根因修好过、调用点各自那层 fail-open 还在,DB 抖一下照样全站免费。故一个端点一条断言,
少一个就等于给自己留一个免费口子。

两个码不许合并(诚实):
  insufficient_balance / 402 = 用户没钱 → 去充值
  lookup_error / 503          = 我们查不出来 → 稍后再试
把后者报成前者 = 让会计为我们的故障去充一笔本来就够的钱,充完照样跑不动。

各端点都断言「拒绝发生在花钱之前」:付费动作(读文件 / 建 job / 调模型)一次都没发生。
"""

import asyncio
import unittest
from unittest import mock

from fastapi import HTTPException

from core import db  # noqa: F401 - 必须先于 account_status(否则 dal_reexports 循环导入)
from services.billing import account_status

_LOOKUP_ERROR_STATUS = {
    "allowed": False,
    "is_exempt": False,
    "balance_thb": 0.0,
    "pages_used_this_month": 0,
    "error_code": account_status.LOOKUP_ERROR,
}

_USER = {"id": "u1", "tenant_id": "t1", "plan": "free"}


class _FakeUpload:
    """记账用的假上传:read() 被调过就说明「拒绝发生在读文件之后」= 闸摆错位置了。"""

    def __init__(self, filename="a.pdf"):
        self.filename = filename
        self.reads = 0

    async def read(self, *a):
        self.reads += 1
        return b"%PDF-1.4 fake"


def _assert_lookup_503(case, ctx):
    case.assertEqual(ctx.exception.status_code, 503)
    case.assertEqual(ctx.exception.detail, {"code": account_status.LOOKUP_ERROR})
    case.assertNotEqual(ctx.exception.detail.get("code"), "insufficient_balance")


class ReconSubmitPrecheckTests(unittest.TestCase):
    """routes/recon_jobs_routes._credits_precheck(对账异步 submit · 三个 submit 共用)。"""

    def _precheck(self, *, status=None, exc=None):
        from routes import recon_jobs_routes as rjr

        fake_db = mock.Mock()
        if exc is not None:
            fake_db.get_billing_status_combined.side_effect = exc
        else:
            fake_db.get_billing_status_combined.return_value = status
        fake_db.estimate_pdf_cost_thb.return_value = 4.5
        with mock.patch.object(rjr, "db", fake_db):
            return rjr._credits_precheck("u1", "t1", 3)

    def test_lookup_error_status_returns_503(self):
        with self.assertRaises(HTTPException) as ctx:
            self._precheck(status=_LOOKUP_ERROR_STATUS)
        _assert_lookup_503(self, ctx)

    def test_lookup_exception_returns_503_not_silent_pass(self):
        with self.assertRaises(HTTPException) as ctx:
            self._precheck(exc=RuntimeError("db down"))
        _assert_lookup_503(self, ctx)

    def test_insufficient_balance_keeps_its_own_402(self):
        broke = dict(_LOOKUP_ERROR_STATUS, error_code="insufficient_balance")
        with self.assertRaises(HTTPException) as ctx:
            self._precheck(status=broke)
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertEqual(ctx.exception.detail["code"], "insufficient_balance")

    def test_allowed_passes_the_status_through(self):
        ok = {"allowed": True, "is_exempt": False, "error_code": None}
        self.assertEqual(self._precheck(status=ok), ok)


class BankV2RunTests(unittest.TestCase):
    """routes/recon_routes_bankv2_run.bank_v2_run(旧同步对账入口)。"""

    def _run(self, gate, uploads):
        from routes import recon_routes_bankv2_run as bv2

        # _BANK_V2_OK=False 会先抛一个「模块不可用」的 503 —— 那会让本测试假绿,故显式置真;
        # 断言也连 detail 一起比,与那条 503(detail 是字符串)区分得开。
        with (
            mock.patch.object(bv2, "_BANK_V2_OK", True),
            mock.patch.object(bv2, "require_perm", lambda *a, **k: _USER),
            mock.patch("core.db.get_billing_status_combined", gate),
        ):
            return asyncio.run(
                bv2.bank_v2_run(
                    request=None, stmt_files=[uploads[0]], gl_files=[uploads[1]], lang="th"
                )
            )

    def test_lookup_error_returns_503_before_reading_files(self):
        uploads = [_FakeUpload("s.pdf"), _FakeUpload("g.xlsx")]
        with self.assertRaises(HTTPException) as ctx:
            self._run(lambda *a, **k: _LOOKUP_ERROR_STATUS, uploads)
        _assert_lookup_503(self, ctx)
        self.assertEqual([u.reads for u in uploads], [0, 0])

    def test_lookup_exception_returns_503(self):
        uploads = [_FakeUpload("s.pdf"), _FakeUpload("g.xlsx")]

        def _boom(*a, **k):
            raise RuntimeError("db down")

        with self.assertRaises(HTTPException) as ctx:
            self._run(_boom, uploads)
        _assert_lookup_503(self, ctx)
        self.assertEqual([u.reads for u in uploads], [0, 0])


class GlVatRunTests(unittest.TestCase):
    """routes/recon_routes_glvat.gl_vat_run(旧同步收入对账入口)。"""

    def _run(self, gate, uploads):
        from routes import recon_routes_glvat as glv

        with (
            mock.patch.object(glv, "require_perm", lambda *a, **k: _USER),
            mock.patch("core.db.get_billing_status_combined", gate),
        ):
            return asyncio.run(
                glv.gl_vat_run(request=None, gl_files=[uploads[0]], vat_files=[uploads[1]])
            )

    def test_lookup_error_returns_503_before_reading_files(self):
        uploads = [_FakeUpload("gl.xlsx"), _FakeUpload("vat.pdf")]
        with self.assertRaises(HTTPException) as ctx:
            self._run(lambda *a, **k: _LOOKUP_ERROR_STATUS, uploads)
        _assert_lookup_503(self, ctx)
        self.assertEqual([u.reads for u in uploads], [0, 0])

    def test_lookup_exception_returns_503(self):
        uploads = [_FakeUpload("gl.xlsx"), _FakeUpload("vat.pdf")]

        def _boom(*a, **k):
            raise RuntimeError("db down")

        with self.assertRaises(HTTPException) as ctx:
            self._run(_boom, uploads)
        _assert_lookup_503(self, ctx)


class VatExcelBuildTests(unittest.TestCase):
    """routes/vat_excel_routes.build_excel_endpoint(VAT 对账表)。"""

    def _run(self, gate, uploads):
        from routes import vat_excel_routes as vex

        with (
            mock.patch.object(vex, "_require_user", lambda request: _USER),
            mock.patch.object(vex.db, "get_billing_status_combined", gate),
        ):
            return asyncio.run(
                vex.build_excel_endpoint(
                    request=None, invoices=[uploads[0]], reports=[uploads[1]], lang="th"
                )
            )

    def test_lookup_error_returns_503_before_reading_files(self):
        uploads = [_FakeUpload("inv.pdf"), _FakeUpload("rep.pdf")]
        with self.assertRaises(HTTPException) as ctx:
            self._run(lambda *a, **k: _LOOKUP_ERROR_STATUS, uploads)
        _assert_lookup_503(self, ctx)
        self.assertEqual([u.reads for u in uploads], [0, 0])

    def test_lookup_exception_returns_503(self):
        uploads = [_FakeUpload("inv.pdf"), _FakeUpload("rep.pdf")]

        def _boom(*a, **k):
            raise RuntimeError("db down")

        with self.assertRaises(HTTPException) as ctx:
            self._run(_boom, uploads)
        _assert_lookup_503(self, ctx)


class KnowledgeAskTests(unittest.TestCase):
    """routes/knowledge_ask_routes.ask_question(知识库问答 · 每答扣 ฿0.50)。"""

    def _ask(self, gate):
        from routes import knowledge_ask_routes as kar

        identity = mock.Mock(user_id="u1", tenant_id="t1")
        embedded = []
        with (
            mock.patch.object(kar, "require_perm", lambda *a, **k: _USER),
            mock.patch.object(kar, "resolve_caller", lambda request: (identity, [1])),
            mock.patch.object(kar.db, "get_billing_status_combined", gate),
            mock.patch.object(kar.embedding, "embed_texts", lambda *a, **k: embedded.append(1)),
        ):
            body = kar.AskRequest(question="ภาษีซื้อเดือนนี้เท่าไร")
            try:
                kar.ask_question(None, body)
            finally:
                self.embedded = embedded

    def test_lookup_error_returns_503_before_calling_the_model(self):
        with self.assertRaises(HTTPException) as ctx:
            self._ask(lambda *a, **k: _LOOKUP_ERROR_STATUS)
        _assert_lookup_503(self, ctx)
        self.assertEqual(self.embedded, [])  # 一次模型都没调

    def test_lookup_exception_returns_503(self):
        def _boom(*a, **k):
            raise RuntimeError("db down")

        with self.assertRaises(HTTPException) as ctx:
            self._ask(_boom)
        _assert_lookup_503(self, ctx)
        self.assertEqual(self.embedded, [])


class RecognizeCoreTests(unittest.TestCase):
    """services/ocr/recognize/core.run_recognition_core(识别中心主端点 · 流量最大的付费口)。"""

    def _run(self, gate):
        from services.ocr.recognize import core

        ran = []
        with (
            mock.patch.object(core.wc, "default_workspace_for_write", lambda tid: 1),
            mock.patch.object(core, "_ocr_get_cached", lambda *a, **k: None),
            mock.patch.object(core.db, "get_billing_status_combined", gate),
            mock.patch(
                "services.ocr.entrypoints.run_pipeline_for_file",
                lambda *a, **k: ran.append(1),
            ),
        ):
            try:
                core.run_recognition_core(_USER, b"fake-image-bytes", _FakeUpload("a.jpg"))
            finally:
                self.ran = ran

    def test_lookup_error_returns_503_before_running_ocr(self):
        with self.assertRaises(HTTPException) as ctx:
            self._run(lambda *a, **k: _LOOKUP_ERROR_STATUS)
        _assert_lookup_503(self, ctx)
        self.assertEqual(self.ran, [])  # 管线一次都没跑 = 一分钱模型费都没花

    def test_lookup_exception_returns_503(self):
        def _boom(*a, **k):
            raise RuntimeError("db down")

        with self.assertRaises(HTTPException) as ctx:
            self._run(_boom)
        _assert_lookup_503(self, ctx)
        self.assertEqual(self.ran, [])


class BillingQuoteTests(unittest.TestCase):
    """services/ocr/entrypoints.billing_quote(LINE 图 / 采购收料 / 邮件收料共用报价闸)。"""

    def _quote(self, status):
        from services.ocr import entrypoints

        with mock.patch.object(
            entrypoints.db, "get_billing_status_combined", return_value=status
        ):
            # 图片扩展名:page_count=1 直达计费检查,不碰 PDF 解析
            return entrypoints.billing_quote(dict(_USER), b"fake", "a.jpg")

    def test_lookup_error_is_not_reported_as_insufficient_balance(self):
        out = self._quote(_LOOKUP_ERROR_STATUS)
        self.assertFalse(out["allowed"])
        self.assertEqual(out["error_code"], account_status.LOOKUP_ERROR)

    def test_real_insufficient_keeps_its_own_code(self):
        from services.ocr import entrypoints

        broke = {"allowed": False, "is_exempt": False, "balance_thb": 0.0, "pages_used_this_month": 0}
        with mock.patch.object(entrypoints.db, "estimate_pdf_cost_thb", return_value=1.5):
            out = self._quote(broke)
        self.assertEqual(out["error_code"], "insufficient_balance")


class DmsIdOcrGateTests(unittest.TestCase):
    """services/erp/dms_id_ocr._billing_gate(DMS 身份证识别的余额闸)。"""

    def _gate(self, status):
        from services.erp import dms_id_ocr

        with mock.patch.object(
            dms_id_ocr.db, "get_billing_status_combined", return_value=status
        ):
            return dms_id_ocr._billing_gate(dict(_USER))

    def test_lookup_error_raises_503_not_402(self):
        from services.erp.dms_id_ocr import DmsOcrError

        with self.assertRaises(DmsOcrError) as ctx:
            self._gate(_LOOKUP_ERROR_STATUS)
        self.assertEqual(ctx.exception.http_status, 503)
        self.assertEqual(ctx.exception.detail, {"code": account_status.LOOKUP_ERROR})

    def test_real_insufficient_keeps_402(self):
        from services.erp import dms_id_ocr

        broke = {"allowed": False, "is_exempt": False, "balance_thb": 0.0, "pages_used_this_month": 0}
        with mock.patch.object(dms_id_ocr.db, "estimate_pdf_cost_thb", return_value=1.5):
            with self.assertRaises(dms_id_ocr.DmsOcrError) as ctx:
                self._gate(broke)
        self.assertEqual(ctx.exception.http_status, 402)
        self.assertEqual(ctx.exception.detail.get("code"), "insufficient_balance")


if __name__ == "__main__":
    unittest.main()

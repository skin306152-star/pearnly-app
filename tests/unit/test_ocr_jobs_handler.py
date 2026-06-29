# -*- coding: utf-8 -*-
"""services/ocr/jobs/handler.py 单测(缺口④ · web_ocr 处理器)。

mock run_recognition_core + db + 暂存文件:断言成功→{result,history_ids}、
HTTPException(非票/余额)→ ("__failed__", {error_code})、缺用户/缺文件→对应 failed sentinel。
不打真 DB / 不跑真 pipeline。
"""

import unittest
from unittest import mock

from fastapi import HTTPException

from core import db  # noqa: F401
from services.ocr.jobs import handler as h


def _params(**kw):
    base = {
        "job_id": "job-1",
        "user_id": "u1",
        "filename": "inv.pdf",
        "client_id": None,
        "workspace_client_id": None,
    }
    base.update(kw)
    return base


class ErrorCodeFromHttpTests(unittest.TestCase):
    def test_str_detail(self):
        self.assertEqual(
            h._error_code_from_http(HTTPException(400, detail="ocr.not_invoice")), "ocr.not_invoice"
        )

    def test_dict_code(self):
        self.assertEqual(
            h._error_code_from_http(HTTPException(402, detail={"code": "insufficient_balance"})),
            "insufficient_balance",
        )

    def test_fallback_when_no_detail(self):
        # detail 非 str/dict(如普通异常无 detail 属性)→ 兜底码
        self.assertEqual(h._error_code_from_http(Exception("x")), "ocr_failed")


class HandleWebOcrTests(unittest.TestCase):
    def setUp(self):
        # 用户存在 + 暂存文件存在 + 可读
        self._find = mock.patch.object(h.db, "find_user_by_id", return_value={"id": "u1"})
        self._find.start()
        self._isfile = mock.patch("os.path.isfile", return_value=True)
        self._isfile.start()
        self._open = mock.patch("builtins.open", mock.mock_open(read_data=b"PDFBYTES"))
        self._open.start()
        # PDF 留底 no-op
        self._pdf = mock.patch(
            "services.ocr.pdf_backfill.generate_and_save_pdf", return_value=(None, 0)
        )
        self._pdf.start()

    def tearDown(self):
        for p in (self._find, self._isfile, self._open, self._pdf):
            p.stop()

    def _patch_core(self, **kw):
        return mock.patch("services.ocr.recognize.core.run_recognition_core", **kw)

    def test_success_returns_result_and_history(self):
        with self._patch_core(
            return_value={"response": {"pages": [1]}, "raw_pages": [], "history_ids": ["h1"]}
        ):
            out = h.handle_web_ocr(_params(), [], lambda p: None)
        self.assertEqual(out["result"], {"pages": [1]})
        self.assertEqual(out["history_ids"], ["h1"])

    def test_http_exception_maps_to_failed(self):
        with self._patch_core(side_effect=HTTPException(400, detail="ocr.not_invoice")):
            out = h.handle_web_ocr(_params(), [], lambda p: None)
        self.assertEqual(out, ("__failed__", {"error_code": "ocr.not_invoice"}))

    def test_insufficient_balance_maps_to_failed(self):
        with self._patch_core(
            side_effect=HTTPException(402, detail={"code": "insufficient_balance"})
        ):
            out = h.handle_web_ocr(_params(), [], lambda p: None)
        self.assertEqual(out, ("__failed__", {"error_code": "insufficient_balance"}))

    def test_progress_emitted_before_core(self):
        seen = []
        with self._patch_core(return_value={"response": {}, "raw_pages": [], "history_ids": []}):
            h.handle_web_ocr(_params(), [], lambda p: seen.append(p))
        self.assertTrue(any(s.get("stage") == "running" for s in seen))


class GuardTests(unittest.TestCase):
    def test_user_not_found(self):
        with mock.patch.object(h.db, "find_user_by_id", return_value=None):
            out = h.handle_web_ocr(_params(), [], lambda p: None)
        self.assertEqual(out, ("__failed__", {"error_code": "user_not_found"}))

    def test_staged_file_missing(self):
        with mock.patch.object(h.db, "find_user_by_id", return_value={"id": "u1"}):
            with mock.patch("os.path.isfile", return_value=False):
                out = h.handle_web_ocr(_params(), [], lambda p: None)
        self.assertEqual(out, ("__failed__", {"error_code": "staged_file_missing"}))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""契约测试 · services/erp/push_dispatch.dispatch_endpoint_batch(P1c)

锁定:
  1. mrerp 批量:一次 upload_invoice_batch 返回多行 ImportResult → 按 invoice_no
     正确回映射到每张 history(顺序对齐 · success/failed 各归各的)。
  2. build_mrerp_adapter 失败 → 批内每张都拿同一个 err 结果(不漏张)。
  3. 批级异常(MRERPAuthError 等)→ 每张同一个错误结果。
  4. 非 mrerp adapter → 循环 push_to_endpoint(统一接口)。
  5. 结果 shape 与 push_to_endpoint 对齐(success/http_status/response_body/...).
"""

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from services.erp import erp_push
from services.erp import push_dispatch


class _FakeAdapter:
    """支持 with 语境的假 adapter。upload_invoice_batch 返回预置 result。"""

    def __init__(self, result=None, raises=None):
        self._result = result
        self._raises = raises
        self.batch_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def upload_invoice_batch(self, flats, mappings):
        self.batch_calls += 1
        if self._raises is not None:
            raise self._raises
        return self._result


def _result(success_rows, failed_rows):
    return SimpleNamespace(
        success=success_rows,
        failed=failed_rows,
        elapsed_ms=1234,
        xlsx_size_bytes=999,
    )


def _success(inv, bill):
    return SimpleNamespace(invoice_no=inv, mrerp_bill_no=bill, original={})


def _failed(inv, reasons):
    return SimpleNamespace(
        invoice_no=inv, reasons=reasons, original={}, reasons_friendly=[], evidence_screenshot=None
    )


_EP = {"id": "ep-1", "adapter": "mrerp", "user_id": None, "config": {}}


class DispatchMrerpBatchTests(unittest.TestCase):
    def setUp(self):
        # 让 invoice_no 派生 = history['invoice_no'](可预测回映射键)。
        p = mock.patch.object(
            push_dispatch, "_mrerp_history_invoice_no", lambda hf: hf.get("invoice_no")
        )
        p.start()
        self.addCleanup(p.stop)

    def test_maps_success_and_failed_by_invoice_no(self):
        histories = [
            {"id": "h1", "invoice_no": "INV001", "pages": []},
            {"id": "h2", "invoice_no": "INV002", "pages": []},
            {"id": "h3", "invoice_no": "INV003", "pages": []},
        ]
        result = _result(
            success_rows=[_success("INV001", "SI-1"), _success("INV003", "SI-3")],
            failed_rows=[_failed("INV002", ["ไม่พบลูกค้า"])],
        )
        fake = _FakeAdapter(result=result)
        with mock.patch.object(erp_push, "build_mrerp_adapter", return_value=(fake, None)):
            out = push_dispatch.dispatch_endpoint_batch(_EP, histories)

        self.assertEqual(fake.batch_calls, 1, "整批必须只一次 upload_invoice_batch")
        self.assertEqual(len(out), 3)
        # h1 → success INV001
        self.assertTrue(out[0]["success"])
        self.assertEqual(out[0]["mrerp_bill_no"], "SI-1")
        self.assertEqual(out[0]["request_body"]["history_id"], "h1")
        # h2 → failed INV002
        self.assertFalse(out[1]["success"])
        self.assertIn("ไม่พบลูกค้า", out[1]["error_msg"])
        body = json.loads(out[1]["response_body"])
        self.assertFalse(body["ok"])
        self.assertEqual(body["reasons"], ["ไม่พบลูกค้า"])
        # h3 → success INV003
        self.assertTrue(out[2]["success"])
        self.assertEqual(out[2]["mrerp_bill_no"], "SI-3")
        # shape 对齐 push_to_endpoint
        for r in out:
            for k in (
                "success",
                "http_status",
                "response_body",
                "error_msg",
                "elapsed_ms",
                "request_body",
                "adapter",
            ):
                self.assertIn(k, r)
            self.assertEqual(r["adapter"], "mrerp")

    def test_invoice_no_not_in_result_falls_back_unknown(self):
        histories = [{"id": "h1", "invoice_no": "INV404", "pages": []}]
        result = _result(success_rows=[], failed_rows=[])
        fake = _FakeAdapter(result=result)
        with mock.patch.object(erp_push, "build_mrerp_adapter", return_value=(fake, None)):
            out = push_dispatch.dispatch_endpoint_batch(_EP, histories)
        self.assertFalse(out[0]["success"])
        self.assertIn("ERR_UNKNOWN_UPLOAD_OUTCOME", out[0]["error_msg"])

    def test_build_error_marks_every_history(self):
        histories = [
            {"id": "h1", "invoice_no": "INV001", "pages": []},
            {"id": "h2", "invoice_no": "INV002", "pages": []},
        ]
        err = {"http_status": 401, "body": "no_credentials", "error_msg": "ERR_NO_CREDS: x"}
        with mock.patch.object(erp_push, "build_mrerp_adapter", return_value=(None, err)):
            out = push_dispatch.dispatch_endpoint_batch(_EP, histories)
        self.assertEqual(len(out), 2)
        for r, h in zip(out, histories):
            self.assertFalse(r["success"])
            self.assertEqual(r["http_status"], 401)
            self.assertEqual(r["error_msg"], "ERR_NO_CREDS: x")
            self.assertEqual(r["request_body"]["history_id"], h["id"])

    def test_batch_level_auth_error_marks_every_history(self):
        from services.erp.mrerp_adapter import MRERPAuthError

        histories = [
            {"id": "h1", "invoice_no": "INV001", "pages": []},
            {"id": "h2", "invoice_no": "INV002", "pages": []},
        ]
        fake = _FakeAdapter(raises=MRERPAuthError("session kicked"))
        with mock.patch.object(erp_push, "build_mrerp_adapter", return_value=(fake, None)):
            out = push_dispatch.dispatch_endpoint_batch(_EP, histories)
        self.assertEqual(len(out), 2)
        for r in out:
            self.assertFalse(r["success"])
            self.assertIn("ERR_AUTH", r["error_msg"])


class DispatchNonMrerpTests(unittest.TestCase):
    def test_non_mrerp_loops_push_to_endpoint(self):
        ep = {"id": "ep-w", "adapter": "webhook", "config": {}}
        histories = [{"id": "h1"}, {"id": "h2"}]
        calls = []

        def fake_push(endpoint, h):
            calls.append(h["id"])
            return {
                "success": True,
                "http_status": 200,
                "response_body": "ok",
                "error_msg": None,
                "elapsed_ms": 1,
                "request_body": {},
                "adapter": "webhook",
            }

        with mock.patch.object(erp_push, "push_to_endpoint", side_effect=fake_push):
            out = push_dispatch.dispatch_endpoint_batch(ep, histories)
        self.assertEqual(calls, ["h1", "h2"])
        self.assertEqual(len(out), 2)
        self.assertTrue(all(r["success"] for r in out))

    def test_empty_histories_returns_empty(self):
        self.assertEqual(push_dispatch.dispatch_endpoint_batch(_EP, []), [])


if __name__ == "__main__":
    unittest.main()

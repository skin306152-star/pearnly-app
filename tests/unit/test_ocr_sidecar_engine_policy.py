# -*- coding: utf-8 -*-
"""旁路 OCR 入口必须消费 Earn 引擎策略。

salesvat 与 fileconv 都直接调用 ai_gateway transport；若入口没进入 engine_context，
后台切到 qwen 后仍会落默认 Gemini。这里锁真实线程边界与两次 fileconv 调用，避免只测
resolve_mode 却漏掉运行期 contextvar。
"""

import unittest
from unittest import mock

from services.ai_gateway import backends
from services.ai_gateway.tasks import ProviderOutcome
from services.fileconv import ocr_bridge
from services.fileconv.model import STATUS_OK
from services.ocr import contracts, policy
from services.vat.vat_ocr_batch import extract_invoices_batched_parallel
from services.vat.vat_ocr_extract import extract_invoices_parallel

_QWEN_ENV = {
    "OCR_ENGINE_MODE": "qwen",
    "OCR_LLM_BACKEND": "aistudio",
    "GEMINI_API_KEY": "",
    "GOOGLE_API_KEY": "",
}


def _invoice_data(index=None):
    row = {
        "buyer_tax_id": "0105550000001",
        "buyer_name": "ACME",
        "buyer_branch": "00000",
        "invoice_no": "INV-1",
        "invoice_date": "01/05/2026",
        "period": "05/2026",
        "amount_pre_vat": "100.00",
        "vat_amount": "7.00",
        "total_amount": "107.00",
    }
    if index is not None:
        row["index"] = index
    return row


class SidecarPolicyRegistrationTests(unittest.TestCase):
    def test_sidecar_tasks_are_admin_policy_options(self):
        for task in ("salesvat", "fileconv_ocr"):
            self.assertIn(task, contracts.OCR_TASKS)
            self.assertEqual(policy.policy_for(task).task, task)


class SalesvatEngineContextTests(unittest.TestCase):
    def test_single_invoice_threads_keep_qwen_backend(self):
        seen = []

        def fake_transport(*args, **kwargs):
            seen.append(backends.override_backend())
            return ProviderOutcome(ok=True, data=_invoice_data(), model="qwen-test")

        files = [{"filename": "invoice.jpg", "bytes": b"jpg"}]
        with (
            mock.patch.dict("os.environ", _QWEN_ENV, clear=False),
            mock.patch("services.ai_gateway.transport.multimodal_to_json", fake_transport),
        ):
            result = extract_invoices_parallel(
                files, api_key="key", max_workers=1, plan_code="M", is_exempt=False
            )

        self.assertTrue(result[0]["ok"])
        self.assertEqual(seen, ["qwen"])
        self.assertIsNone(backends.override_backend())

    def test_batch_threads_keep_qwen_backend(self):
        seen = []

        def fake_transport(*args, **kwargs):
            seen.append(backends.override_backend())
            return ProviderOutcome(
                ok=True,
                data={"invoices": [_invoice_data(1), _invoice_data(2)]},
                model="qwen-test",
            )

        files = [
            {"filename": "a.jpg", "bytes": b"a"},
            {"filename": "b.jpg", "bytes": b"b"},
        ]
        with (
            mock.patch.dict("os.environ", _QWEN_ENV, clear=False),
            mock.patch("services.ai_gateway.transport.multimodal_to_json", fake_transport),
        ):
            result = extract_invoices_batched_parallel(
                files,
                api_key="key",
                batch_size=2,
                max_workers=1,
                plan_code="M",
                is_exempt=False,
            )

        self.assertTrue(all(row["ok"] for row in result))
        self.assertEqual(seen, ["qwen"])
        self.assertIsNone(backends.override_backend())


class FileconvEngineContextTests(unittest.TestCase):
    def test_classify_and_extract_share_qwen_backend(self):
        seen = []
        outcomes = [
            ProviderOutcome(ok=True, data={"document_type": "generic_table"}),
            ProviderOutcome(ok=True, data={"headers": ["amount"], "rows": [{"amount": "7"}]}),
        ]

        def fake_transport(*args, **kwargs):
            seen.append(backends.override_backend())
            return outcomes.pop(0)

        with (
            mock.patch.dict("os.environ", _QWEN_ENV, clear=False),
            mock.patch("services.ai_gateway.transport.multimodal_to_json", fake_transport),
        ):
            result = ocr_bridge.convert_images(
                [b"image"],
                "table.jpg",
                tenant_id="t1",
                api_key="key",
                plan_code="M",
                is_exempt=False,
            )

        self.assertEqual(result.status, STATUS_OK)
        self.assertEqual(seen, ["qwen", "qwen"])
        self.assertIsNone(backends.override_backend())


if __name__ == "__main__":
    unittest.main()

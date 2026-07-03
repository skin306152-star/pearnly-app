# -*- coding: utf-8 -*-
"""P2E AI Gateway:run_task 契约、Gemini provider 异常→error_kind 映射、日志不存原文、成本估算。"""

import unittest
from unittest import mock

from services.ai_gateway import costing, router
from services.ai_gateway import tasks as T
from services.ai_gateway.providers import gemini


class FakeProvider:
    NAME = "fake"

    def __init__(self, outcome):
        self._o = outcome
        self.calls = []

    def generate_json(self, **kw):
        self.calls.append(kw)
        return self._o


class RunTaskTests(unittest.TestCase):
    def test_success_returns_structured(self):
        fp = FakeProvider(
            T.ProviderOutcome(
                ok=True, data={"intent": "record"}, model="m", input_tokens=10, output_tokens=4
            )
        )
        res = router.run_task(
            "line_text_understand", prompt="p", text="t", api_key="k", provider=fp
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.data, {"intent": "record"})
        self.assertEqual(res.task, "line_text_understand")
        self.assertEqual(res.schema_version, "1")
        self.assertEqual(res.provider, "fake")
        self.assertGreaterEqual(res.latency_ms, 0)
        self.assertGreater(res.cost_thb, 0)

    def test_task_spec_drives_timeout_and_tier(self):
        fp = FakeProvider(T.ProviderOutcome(ok=True, data={}))
        router.run_task("expense_category_choose", prompt="p", text="t", api_key="k", provider=fp)
        self.assertEqual(fp.calls[0]["timeout_s"], 12)  # task 默认
        self.assertEqual(fp.calls[0]["model_tier"], "brain")  # LINE 通道挂大脑档(与 OCR 档独立)
        self.assertEqual(fp.calls[0]["max_retries"], 1)

    def test_timeout_override(self):
        fp = FakeProvider(T.ProviderOutcome(ok=True, data={}))
        router.run_task(
            "expense_category_choose", prompt="p", text="t", api_key="k", timeout_s=5, provider=fp
        )
        self.assertEqual(fp.calls[0]["timeout_s"], 5)

    def test_error_kind_passthrough(self):
        for kind in T.ERROR_KINDS:
            fp = FakeProvider(T.ProviderOutcome(ok=False, error_kind=kind))
            res = router.run_task(
                "line_text_understand", prompt="p", text="t", api_key="k", provider=fp
            )
            self.assertFalse(res.ok)
            self.assertEqual(res.error_kind, kind)
            self.assertIsNone(res.data)

    def test_unknown_task_raises(self):
        with self.assertRaises(KeyError):
            router.run_task("nope", prompt="p", text="t", api_key="k", provider=FakeProvider(None))


class GeminiProviderMappingTests(unittest.TestCase):
    """各家原始异常收敛到标准 error_kind;成功返回结构化 data。"""

    def _run(self, side_effect=None, ret=None):
        with mock.patch("services.ocr.layer2_gemini._call_gemini_with_retry") as call:
            if side_effect is not None:
                call.side_effect = side_effect
            else:
                call.return_value = ret
            return gemini.generate_json(
                prompt="p", text="t", api_key="k", model_tier="flash", timeout_s=5, max_retries=1
            )

    def test_success(self):
        out = self._run(ret=({"choice": 2}, {"input_tokens": 5, "output_tokens": 2}))
        self.assertTrue(out.ok)
        self.assertEqual(out.data, {"choice": 2})
        self.assertEqual(out.input_tokens, 5)

    def test_auth_quota_timeout_parse_provider(self):
        from services.ocr.layer2_gemini import (
            Layer2AuthError,
            Layer2QuotaError,
            Layer2TransientError,
        )

        self.assertEqual(self._run(side_effect=Layer2AuthError("x")).error_kind, "auth")
        self.assertEqual(self._run(side_effect=Layer2QuotaError("x")).error_kind, "quota")
        self.assertEqual(self._run(side_effect=Layer2TransientError("x")).error_kind, "timeout")
        self.assertEqual(self._run(side_effect=ValueError("bad json")).error_kind, "parse")
        self.assertEqual(self._run(side_effect=RuntimeError("boom")).error_kind, "provider")

    def test_no_key_returns_auth_without_calling_transport(self):
        with mock.patch("services.ocr.layer2_gemini._call_gemini_with_retry") as call:
            out = gemini.generate_json(
                prompt="p", text="t", api_key=None, model_tier="flash", timeout_s=5, max_retries=1
            )
            self.assertFalse(out.ok)
            self.assertEqual(out.error_kind, "auth")
            call.assert_not_called()


class LoggingPrivacyTests(unittest.TestCase):
    def test_log_has_no_raw_text_or_prompt_or_key(self):
        secret_text = "ค่ากาแฟ SECRET_TEXT_42 ที่ร้านลับ"
        secret_prompt = "SECRET_PROMPT_SYS"
        fp = FakeProvider(T.ProviderOutcome(ok=True, data={"x": 1}, model="m", input_tokens=3))
        with self.assertLogs("ai_gateway", level="INFO") as cm:
            router.run_task(
                "line_text_understand",
                prompt=secret_prompt,
                text=secret_text,
                api_key="SECRET_KEY_99",
                tenant_id="T1",
                provider=fp,
            )
        blob = "\n".join(cm.output)
        self.assertNotIn("SECRET_TEXT_42", blob)
        self.assertNotIn("SECRET_PROMPT_SYS", blob)
        self.assertNotIn("SECRET_KEY_99", blob)
        self.assertIn("payload_hash=", blob)
        self.assertIn("task=line_text_understand", blob)


class CostingTests(unittest.TestCase):
    def test_zero_tokens_zero_cost(self):
        self.assertEqual(costing.estimate_thb("m", 0, 0), 0.0)
        self.assertEqual(costing.estimate_thb("m", None, None), 0.0)

    def test_positive(self):
        self.assertGreater(costing.estimate_thb("m", 1000, 1000), 0)


if __name__ == "__main__":
    unittest.main()

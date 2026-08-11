# -*- coding: utf-8 -*-
"""qwen provider 契约:档位→模型、载荷两条硬约定、无凭据收敛、转写形态。

守的是三件会静默烧钱/变慢的事:
  ① tier 必须真分模型(读取臂 flash / 升级臂 max 差 60 倍单价),映错就是账单错;
  ② 每个 chat 请求都带 enable_thinking=false(千问默认开思考链);
  ③ 不发 response_format(DashScope 视觉模型对它不稳,JSON 靠 prompt + _parse_json)。
"""

import unittest
from unittest import mock

from services.ai_gateway import transport
from services.ai_gateway.providers import qwen

_ENV = {
    "QWEN_OCR_URL": "https://example.invalid/compatible-mode/v1",
    "QWEN_OCR_KEY": "test-key",
    "QWEN_MODEL_FLASH": "",
    "QWEN_MODEL_ESCALATE": "",
    "QWEN_MODEL_VLOCR": "",
}


def _body(content: str) -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 3},
    }


class _Post:
    """post_json 替身:记下每次请求载荷,按序回放响应。"""

    def __init__(self, *responses):
        self.calls = []
        self._responses = list(responses) or [(_body('{"ok": 1}'), None)]

    def __call__(self, url, headers, payload, timeout_s):
        self.calls.append({"url": url, "headers": headers, "payload": payload})
        return self._responses[min(len(self.calls) - 1, len(self._responses) - 1)]


class TierMappingTests(unittest.TestCase):
    def test_read_arm_and_escalate_arm_are_different_models(self):
        with mock.patch.dict("os.environ", _ENV):
            self.assertEqual(qwen.model_for_tier("flash"), qwen.DEFAULT_FLASH)
            self.assertEqual(qwen.model_for_tier("flash_lite"), qwen.DEFAULT_FLASH)
            self.assertEqual(qwen.model_for_tier("fallback"), qwen.DEFAULT_ESCALATE)
            self.assertEqual(qwen.model_for_tier("escalate"), qwen.DEFAULT_ESCALATE)
            self.assertEqual(qwen.model_for_tier(qwen.TIER_VLOCR), qwen.DEFAULT_VLOCR)

    def test_env_overrides_each_arm_independently(self):
        with mock.patch.dict("os.environ", {**_ENV, "QWEN_MODEL_ESCALATE": "qwen9-test"}):
            self.assertEqual(qwen.model_for_tier("escalate"), "qwen9-test")
            self.assertEqual(qwen.model_for_tier("flash"), qwen.DEFAULT_FLASH)

    def test_unknown_tier_falls_back_to_read_arm(self):
        with mock.patch.dict("os.environ", _ENV):
            self.assertEqual(qwen.model_for_tier("brain"), qwen.DEFAULT_FLASH)


class PayloadTests(unittest.TestCase):
    def test_chat_disables_thinking_and_omits_response_format(self):
        post = _Post((_body('{"total_amount": "70.00"}'), None))
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            out = qwen.multimodal_to_json("p", [(b"img", "image/png")], tier="flash")
        payload = post.calls[0]["payload"]
        self.assertTrue(out.ok)
        self.assertIs(payload["enable_thinking"], False)
        self.assertNotIn("response_format", payload)
        self.assertEqual(payload["model"], qwen.DEFAULT_FLASH)
        self.assertEqual(out.data, {"total_amount": "70.00"})
        self.assertEqual((out.input_tokens, out.output_tokens), (11, 3))

    def test_escalate_tier_sends_escalate_model(self):
        post = _Post((_body('{"total_amount": "70.00"}'), None))
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            qwen.multimodal_to_json("p", [(b"img", "image/png")], tier="escalate")
        self.assertEqual(post.calls[0]["payload"]["model"], qwen.DEFAULT_ESCALATE)

    def test_transcription_model_gets_no_thinking_toggle(self):
        post = _Post((_body("บริษัท ตัวอย่าง"), None))
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            out = qwen.multimodal_to_text("transcribe", [(b"img", "image/png")])
        payload = post.calls[0]["payload"]
        self.assertNotIn("enable_thinking", payload)
        self.assertEqual(payload["model"], qwen.DEFAULT_VLOCR)
        self.assertEqual(out.data, "บริษัท ตัวอย่าง")

    def test_thinking_toggle_follows_the_lane_not_the_model_name(self):
        """带不带 enable_thinking 由车道定 —— 从模型名反猜的话,env 换个名字就默默失灵。"""
        env = {**_ENV, "QWEN_MODEL_VLOCR": "ocr-renamed-2027", "QWEN_MODEL_FLASH": "qwen-vl-flash"}
        post = _Post((_body("บริษัท ตัวอย่าง"), None))
        with mock.patch.dict("os.environ", env), mock.patch.object(qwen, "post_json", post):
            qwen.multimodal_to_text("transcribe", [(b"img", "image/png")])
        self.assertNotIn("enable_thinking", post.calls[0]["payload"])

        post = _Post((_body('{"total_amount": "70.00"}'), None))
        with mock.patch.dict("os.environ", env), mock.patch.object(qwen, "post_json", post):
            qwen.multimodal_to_json("p", [(b"img", "image/png")], tier="flash")
        self.assertIs(post.calls[0]["payload"]["enable_thinking"], False)

    def test_image_travels_as_data_uri_part(self):
        post = _Post()
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            qwen.multimodal_to_json("p", [(b"img", "image/png")], tier="flash")
        parts = post.calls[0]["payload"]["messages"][0]["content"]
        self.assertEqual(parts[0]["type"], "text")
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/png;base64,"))


class FailureTests(unittest.TestCase):
    def test_missing_endpoint_is_auth(self):
        with mock.patch.dict("os.environ", {**_ENV, "QWEN_OCR_URL": ""}):
            self.assertEqual(qwen.text_to_json("p").error_kind, "auth")
            self.assertEqual(qwen.multimodal_to_text("p", [(b"i", "image/png")]).error_kind, "auth")

    def test_unparsable_json_returns_parse_with_raw(self):
        post = _Post((_body("ไม่ใช่ JSON"), None))
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            out = qwen.text_to_json("p", max_retries=0)
        self.assertFalse(out.ok)
        self.assertEqual(out.error_kind, "parse")
        self.assertEqual(out.raw, "ไม่ใช่ JSON")

    def test_array_response_takes_first_object(self):
        # 升级臂的提示词允许"同页多票 → 数组";只认对象会把读对的一页判成 parse 失败
        # (2026-08-11 真机冒烟实锤,白烧一次 max)。
        post = _Post((_body('[{"total_amount": "70.00"}, {"total_amount": "80.00"}]'), None))
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            out = qwen.multimodal_to_json("p", [(b"i", "image/png")], tier="escalate")
        self.assertTrue(out.ok)
        self.assertEqual(out.data, {"total_amount": "70.00"})

    def test_array_without_object_is_parse_failure(self):
        post = _Post((_body("[1, 2, 3]"), None))
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            out = qwen.multimodal_to_json(
                "p", [(b"i", "image/png")], tier="escalate", max_retries=0
            )
        self.assertFalse(out.ok)
        self.assertEqual(out.error_kind, "parse")

    def test_http_error_kind_passes_through(self):
        post = _Post((None, "quota"))
        with mock.patch.dict("os.environ", _ENV), mock.patch.object(qwen, "post_json", post):
            out = qwen.multimodal_to_json("p", [(b"i", "image/png")], tier="flash")
        self.assertEqual(out.error_kind, "quota")

    def test_embedding_and_function_calling_declared_unsupported(self):
        self.assertEqual(qwen.embed(["a"]).error_kind, "unsupported")
        self.assertEqual(qwen.text_to_action("p", tools=[]).error_kind, "unsupported")


class TransportFormTests(unittest.TestCase):
    def test_backend_without_the_form_returns_unsupported(self):
        class _NoTextForm:
            NAME = "fake"

        with mock.patch("services.ai_gateway.backends.get_provider", return_value=_NoTextForm):
            out = transport.multimodal_to_text("p", [(b"i", "image/png")])
        self.assertFalse(out.ok)
        self.assertEqual(out.error_kind, "unsupported")

    def test_transport_forwards_to_qwen_provider(self):
        post = _Post((_body("printed text"), None))
        with (
            mock.patch.dict("os.environ", _ENV),
            mock.patch.object(qwen, "post_json", post),
            mock.patch("services.ai_gateway.backends.get_provider", return_value=qwen),
        ):
            out = transport.multimodal_to_text("p", [(b"i", "image/png")], tier=qwen.TIER_VLOCR)
        self.assertTrue(out.ok)
        self.assertEqual(out.data, "printed text")


if __name__ == "__main__":
    unittest.main()

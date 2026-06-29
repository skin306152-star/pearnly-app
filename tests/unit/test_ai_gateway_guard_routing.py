# -*- coding: utf-8 -*-
"""网关 guard 站点路由测试:OCR_LLM_BACKEND != aistudio 时,L2/L3/银行/身份证的
guard 分支必须改走 ai_gateway.transport(默认 aistudio 走原生路,不在此覆盖)。

覆盖:tier_for_model 反向映射 + 各 guard 站点在非 aistudio 后端下的转发/错误语义。
默认 aistudio 路径的字节级一致由各模块原有契约测试保证,这里只测后端切换分支。
"""

import unittest
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.ocr import gemini_models


def _outcome(**kw):
    return lambda *a, **k: ProviderOutcome(**kw)


class TierForModelTests(unittest.TestCase):
    def test_reverse_mapping(self):
        self.assertEqual(gemini_models.tier_for_model(gemini_models.flash()), "flash")
        self.assertEqual(gemini_models.tier_for_model(gemini_models.flash_lite()), "flash_lite")
        self.assertEqual(gemini_models.tier_for_model(gemini_models.fallback()), "fallback")
        self.assertEqual(gemini_models.tier_for_model("totally-unknown-model"), "flash")
        self.assertEqual(gemini_models.tier_for_model(""), "flash")


class GuardRoutingTests(unittest.TestCase):
    """所有用例在 is_aistudio()=False(模拟 vertex/selfhost)下跑。"""

    def setUp(self):
        p = mock.patch("services.ai_gateway.backends.is_aistudio", return_value=False)
        p.start()
        self.addCleanup(p.stop)

    def test_id_card_routes_through_transport(self):
        from services.ocr import id_card_extract

        captured = {}

        def fake_mm(prompt, images, **kw):
            captured["tier"] = kw.get("tier")
            captured["mime"] = images[0][1]
            return ProviderOutcome(ok=True, data={"people_id": "1234567890123"})

        with mock.patch("services.ai_gateway.transport.multimodal_to_json", fake_mm):
            out = id_card_extract.extract_thai_id_card(b"\xff\xd8\xff\x00fake-jpeg", api_key="k")
        self.assertEqual(out["id_card"]["people_id"], "1234567890123")
        self.assertEqual(captured["tier"], "flash_lite")  # 复刻原 DEFAULT_MODEL=flash-lite
        self.assertEqual(captured["mime"], "image/jpeg")

    def test_id_card_raises_on_gateway_failure(self):
        from services.ocr import id_card_extract

        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            _outcome(ok=False, error_kind="quota"),
        ):
            with self.assertRaises(id_card_extract.IdCardExtractError):
                id_card_extract.extract_thai_id_card(b"\xff\xd8\xff\x00fake", api_key="k")

    def test_bank_gl_routes_and_raises_for_fallback(self):
        """银行 guard:成功返回 out.data;失败抛 RuntimeError 让 try_with_fallback 升档。"""
        from services.recon import bank_gl_gemini

        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            _outcome(ok=True, data={"rows": []}),
        ):
            self.assertEqual(
                bank_gl_gemini._call_json(gemini_models.flash(), b"%PDF-1", "p"), {"rows": []}
            )
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            _outcome(ok=False, error_kind="timeout"),
        ):
            with self.assertRaises(RuntimeError):
                bank_gl_gemini._call_json(gemini_models.flash(), b"%PDF-1", "p")

    def test_l2_returns_data_meta_tuple(self):
        from services.ocr import layer2_gemini

        with mock.patch(
            "services.ai_gateway.transport.text_to_json",
            _outcome(ok=True, data={"x": 1}, input_tokens=7, output_tokens=3),
        ):
            data, meta = layer2_gemini._call_l2_via_gateway(
                "prompt", "k", gemini_models.flash(), 1, 30
            )
        self.assertEqual(data, {"x": 1})
        self.assertEqual(meta, {"input_tokens": 7, "output_tokens": 3, "retries": 0})

    def test_l2_maps_auth_kind_to_layer2_error(self):
        from services.ocr import layer2_gemini

        with mock.patch(
            "services.ai_gateway.transport.text_to_json",
            _outcome(ok=False, error_kind="auth"),
        ):
            with self.assertRaises(layer2_gemini.Layer2AuthError):
                layer2_gemini._call_l2_via_gateway("prompt", "k", gemini_models.flash(), 0, 30)

    def test_l3_returns_data_meta_tuple(self):
        from services.ocr import layer3_gemini

        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            _outcome(ok=True, data={"invoice_number": "IV1"}, input_tokens=5, output_tokens=2),
        ):
            data, meta = layer3_gemini._call_l3_via_gateway(
                b"img", "image/png", "sys", "user", "k", gemini_models.flash(), 1, 10
            )
        self.assertEqual(data, {"invoice_number": "IV1"})
        self.assertEqual(meta, {"input_tokens": 5, "output_tokens": 2, "retries": 0})


if __name__ == "__main__":
    unittest.main()

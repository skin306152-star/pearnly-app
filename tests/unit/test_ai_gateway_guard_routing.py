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
        # 三档互异时逐档反解;默认(全 3.5 同名)塌缩映到中性 "flash"。
        ladder = {
            "OCR_FLASH_MODEL": "gemini-2.5-flash",
            "OCR_FLASHLITE_MODEL": "gemini-2.5-flash-lite",
            "OCR_FALLBACK_MODEL": "gemini-3.6-flash",
        }
        with mock.patch.dict("os.environ", ladder):
            self.assertEqual(gemini_models.tier_for_model(gemini_models.flash()), "flash")
            self.assertEqual(gemini_models.tier_for_model(gemini_models.flash_lite()), "flash_lite")
            self.assertEqual(gemini_models.tier_for_model(gemini_models.fallback()), "fallback")
        self.assertEqual(gemini_models.tier_for_model("totally-unknown-model"), "flash")
        self.assertEqual(gemini_models.tier_for_model(""), "flash")
        self.assertEqual(gemini_models.tier_for_model(gemini_models.flash()), "flash")


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

        ladder = {"OCR_FLASHLITE_MODEL": "gemini-2.5-flash-lite"}  # 与主力档区分开才能验首读档
        with (
            mock.patch.dict("os.environ", ladder),
            mock.patch("services.ai_gateway.transport.multimodal_to_json", fake_mm),
        ):
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


class LineBrainProviderRoutingTests(unittest.TestCase):
    """router 用的 providers.gemini.generate_json(LINE 记账大脑通道):
    非 aistudio 后端必须转 backends.get_provider().text_to_json,prompt+text 合并为单 prompt。
    """

    def test_non_aistudio_routes_to_backend_provider(self):
        from services.ai_gateway.providers import gemini

        captured = {}

        class _Prov:
            def text_to_json(self, prompt, **kw):
                captured["prompt"] = prompt
                captured["tier"] = kw.get("tier")
                captured["mime"] = kw.get("response_mime")
                return ProviderOutcome(ok=True, data={"intent": "expense"})

        with (
            mock.patch("services.ai_gateway.backends.is_aistudio", return_value=False),
            mock.patch("services.ai_gateway.backends.get_provider", return_value=_Prov()),
        ):
            out = gemini.generate_json(
                prompt="SYS",
                text="买咖啡 50",
                api_key="k",
                model_tier="flash",
                timeout_s=12,
                max_retries=1,
            )
        self.assertTrue(out.ok)
        self.assertEqual(out.data, {"intent": "expense"})
        self.assertEqual(captured["prompt"], "SYS\n\n买咖啡 50")
        self.assertEqual(captured["tier"], "flash")
        self.assertTrue(captured["mime"])

    def test_non_aistudio_works_without_api_key(self):
        """vertex 凭据走 SA·api_key 缺失也不该提前 auth 失败。"""
        from services.ai_gateway.providers import gemini

        class _Prov:
            def text_to_json(self, prompt, **kw):
                return ProviderOutcome(ok=True, data={})

        with (
            mock.patch("services.ai_gateway.backends.is_aistudio", return_value=False),
            mock.patch("services.ai_gateway.backends.get_provider", return_value=_Prov()),
        ):
            out = gemini.generate_json(
                prompt="", text="hi", api_key=None, model_tier="flash", timeout_s=8, max_retries=0
            )
        self.assertTrue(out.ok)

    def test_aistudio_default_path_unchanged(self):
        """默认 aistudio:不碰 backend provider,仍走原生 _call_gemini_with_retry。"""
        from services.ai_gateway.providers import gemini

        with (
            mock.patch("services.ai_gateway.backends.is_aistudio", return_value=True),
            mock.patch(
                "services.ocr.layer2_gemini._call_gemini_with_retry",
                return_value=({"ok": 1}, {"input_tokens": 2, "output_tokens": 1}),
            ) as native,
        ):
            out = gemini.generate_json(
                prompt="SYS", text="t", api_key="k", model_tier="flash", timeout_s=10, max_retries=1
            )
        self.assertTrue(out.ok)
        self.assertEqual(out.data, {"ok": 1})
        native.assert_called_once()


if __name__ == "__main__":
    unittest.main()

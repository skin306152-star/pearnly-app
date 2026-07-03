# -*- coding: utf-8 -*-
"""model_client 契约:模型名→tier 反解 + 三形态透传 + json_from_pdf 失败升档语义。
另守模型收口红线:业务代码(services/ 除 ai_gateway/providers)不得 import google.generativeai。
"""

import pathlib
import re
import unittest
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.ocr import gemini_models, model_client


class ModelClientTest(unittest.TestCase):
    def test_json_from_text_maps_model_to_tier(self):
        captured = {}

        def fake(prompt, **kw):
            captured.update(kw, prompt=prompt)
            return ProviderOutcome(ok=True, data={"a": 1})

        with mock.patch("services.ai_gateway.transport.text_to_json", fake):
            out = model_client.json_from_text(
                "p", model_name=gemini_models.flash_lite(), task="t.x", api_key="k"
            )
        self.assertTrue(out.ok)
        self.assertEqual(captured["tier"], "flash_lite")
        self.assertEqual(captured["task"], "t.x")
        self.assertEqual(captured["max_retries"], 0)
        self.assertEqual(captured["temperature"], 0.0)

    def test_json_from_images_passes_through(self):
        def fake(prompt, images, **kw):
            self.assertEqual(images, [(b"i", "image/png")])
            return ProviderOutcome(ok=True, data={"b": 2})

        with mock.patch("services.ai_gateway.transport.multimodal_to_json", fake):
            out = model_client.json_from_images(
                "p", [(b"i", "image/png")], model_name=gemini_models.flash(), task="t.y"
            )
        self.assertEqual(out.data, {"b": 2})

    def test_json_from_pdf_ok_and_raise(self):
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            return_value=ProviderOutcome(ok=True, data={"rows": [1]}),
        ):
            self.assertEqual(
                model_client.json_from_pdf(gemini_models.flash(), b"%PDF", "p", "bank.gl"),
                {"rows": [1]},
            )
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            return_value=ProviderOutcome(ok=False, error_kind="timeout"),
        ):
            with self.assertRaises(RuntimeError):
                model_client.json_from_pdf(gemini_models.flash(), b"%PDF", "p", "bank.stmt")


class NoDirectSdkImportTest(unittest.TestCase):
    def test_no_generativeai_import_outside_providers(self):
        root = pathlib.Path(__file__).resolve().parents[2] / "services"
        allowed = root / "ai_gateway" / "providers"
        offenders = []
        for py in root.rglob("*.py"):
            if allowed in py.parents:
                continue
            text = py.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"^\s*(import|from) google\.generativeai", text, re.MULTILINE):
                offenders.append(str(py.relative_to(root)))
        self.assertEqual(offenders, [], f"业务文件直连 SDK: {offenders}")


if __name__ == "__main__":
    unittest.main()

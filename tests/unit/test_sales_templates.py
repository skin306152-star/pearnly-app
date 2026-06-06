# -*- coding: utf-8 -*-
"""销项 §L4 · 发票模板预设解析守门。"""

import unittest

from services.sales import templates


class TemplateResolveTests(unittest.TestCase):
    def test_six_presets_present(self):
        for key in ("classic", "minimal", "brand", "compact", "thai_official", "mono"):
            self.assertIn(key, templates.TEMPLATES)

    def test_unknown_template_falls_back_to_classic(self):
        r = templates.resolve("bogus")
        self.assertEqual(r["accent"], templates.TEMPLATES["classic"]["accent"])

    def test_none_template_uses_default(self):
        self.assertEqual(templates.resolve(None)["template_id"], templates.DEFAULT_TEMPLATE)

    def test_brand_template_uses_brand_color(self):
        self.assertEqual(templates.resolve("brand", "#10b981")["accent"], "#10B981")

    def test_brand_template_without_color_falls_back(self):
        self.assertEqual(templates.resolve("brand", None)["accent"], templates._FALLBACK_ACCENT)

    def test_invalid_hex_falls_back(self):
        self.assertEqual(
            templates.resolve("brand", "not-a-color")["accent"], templates._FALLBACK_ACCENT
        )

    def test_short_hex_accepted(self):
        self.assertEqual(templates.resolve("brand", "#0f0")["accent"], "#0F0")

    def test_grid_styles_are_known(self):
        for cfg in templates.TEMPLATES.values():
            self.assertIn(cfg["grid"], ("full", "light", "none"))


if __name__ == "__main__":
    unittest.main()

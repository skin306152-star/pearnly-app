# -*- coding: utf-8 -*-
"""泰语图卡 imagemap 构建器 + 出图路由单测。"""

import unittest

from fastapi.testclient import TestClient

from services.line_binding import line_imagemap as im
from services.line_binding.line_bind_i18n import CONNECT_URL


class CardMessageTests(unittest.TestCase):
    def test_button_card_is_imagemap_with_connect_uri(self):
        msg = im.card_message("need_bind")
        self.assertEqual(msg["type"], "imagemap")
        self.assertEqual(msg["baseSize"], {"width": 1040, "height": 1040})
        self.assertTrue(msg["baseUrl"].endswith("/A3-need-connect-text"))
        self.assertTrue(msg["altText"])
        uris = [a["linkUri"] for a in msg["actions"] if a["type"] == "uri"]
        self.assertIn(CONNECT_URL, uris)

    def test_decorative_card_is_plain_image(self):
        for key in ("bind_success", "ocr_failed", "unsupported"):
            msg = im.card_message(key)
            self.assertEqual(msg["type"], "image", key)
            self.assertTrue(msg["originalContentUrl"].endswith("/1040"))

    def test_welcome_has_connect_and_capability_actions(self):
        msg = im.card_message("welcome")
        self.assertEqual(msg["type"], "imagemap")
        kinds = {a["type"] for a in msg["actions"]}
        self.assertEqual(kinds, {"uri", "message"})
        msg_action = next(a for a in msg["actions"] if a["type"] == "message")
        self.assertEqual(msg_action["text"], "ทำอะไรได้บ้าง")

    def test_conflict_two_uri_buttons(self):
        msg = im.card_message("bind_conflict")
        self.assertEqual(len([a for a in msg["actions"] if a["type"] == "uri"]), 2)

    def test_unknown_card_returns_none(self):
        self.assertIsNone(im.card_message("nope"))

    def test_has_card(self):
        self.assertTrue(im.has_card("need_bind"))
        self.assertFalse(im.has_card("nope"))

    def test_all_actions_within_bounds(self):
        for key in ("welcome", "capability", "need_bind", "bind_conflict"):
            msg = im.card_message(key)
            h = msg["baseSize"]["height"]
            for a in msg["actions"]:
                ar = a["area"]
                self.assertLessEqual(ar["x"] + ar["width"], 1040, key)
                self.assertLessEqual(ar["y"] + ar["height"], h, key)


class CardImageRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from routes.line_card_image_routes import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    def test_known_card_served(self):
        r = self.client.get("/api/line/card/A1-welcome/1040")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "image/jpeg")

    def test_size_segment_ignored(self):
        for size in ("240", "460", "700", "1040"):
            self.assertEqual(
                self.client.get(f"/api/line/card/A3-need-connect-text/{size}").status_code, 200
            )

    def test_unknown_card_404(self):
        self.assertEqual(self.client.get("/api/line/card/evil-path/1040").status_code, 404)

    def test_path_traversal_blocked(self):
        self.assertEqual(self.client.get("/api/line/card/..%2f..%2fsecret/1040").status_code, 404)


if __name__ == "__main__":
    unittest.main()

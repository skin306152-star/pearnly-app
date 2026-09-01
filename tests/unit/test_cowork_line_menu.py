from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from services.cowork_line import menu_cards, rich_menu


def cells(card: dict) -> list[dict]:
    contents = card["contents"]["body"]["contents"]
    return [
        item
        for item in contents
        if item.get("type") == "box"
        and item.get("layout") == "horizontal"
        and item.get("cornerRadius") == "14px"
    ]


def texts(value) -> list[str]:
    if isinstance(value, dict):
        found = [str(value["text"])] if "text" in value else []
        for child in value.values():
            found.extend(texts(child))
        return found
    if isinstance(value, list):
        found = []
        for child in value:
            found.extend(texts(child))
        return found
    return []


class CoworkLineMenuTests(unittest.TestCase):
    def test_each_language_shows_only_the_available_entry(self):
        unavailable_copy = {
            "th": "เร็ว ๆ นี้",
            "en": "Coming soon",
            "zh": "即将开放",
            "ja": "近日公開",
        }
        for lang, unavailable in unavailable_copy.items():
            with self.subTest(lang=lang):
                card = menu_cards.menu_card(lang)
                menu_cells = cells(card)
                self.assertEqual(len(menu_cells), 1)
                self.assertEqual(
                    menu_cells[0]["action"]["data"],
                    "action=cowork_erp_start",
                )
                self.assertNotIn(unavailable, texts(card))
                self.assertIn(
                    "/static/dms/line-icons/", menu_cells[0]["contents"][0]["contents"][0]["url"]
                )
                self.assertEqual(menu_cells[0]["contents"][-1]["text"], "›")

    def test_unknown_language_falls_back_to_thai(self):
        self.assertEqual(
            menu_cards.menu_card("fr")["altText"], menu_cards.menu_card("th")["altText"]
        )

    def test_rich_menu_has_only_first_cell_action(self):
        payload = rich_menu.build_payload()
        self.assertEqual(payload["size"], {"width": 2500, "height": 1686})
        self.assertEqual(len(payload["areas"]), 1)
        self.assertEqual(
            payload["areas"][0],
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "postback",
                    "data": "action=cowork_erp_start",
                    "displayText": "ส่งเอกสารเข้า ERP",
                },
            },
        )

    def test_publish_replaces_old_menu_only_after_new_default(self):
        events = []
        with tempfile.NamedTemporaryFile(suffix=".png") as image:
            image.write(b"png")
            image.flush()
            with (
                patch.object(
                    rich_menu,
                    "_list_menus",
                    return_value=[{"name": rich_menu.MENU_NAME, "richMenuId": "OLD"}],
                ),
                patch.object(
                    rich_menu.line_client,
                    "create_rich_menu",
                    side_effect=lambda *a, **kw: events.append(("create", kw["channel"])) or "NEW",
                ),
                patch.object(
                    rich_menu,
                    "_upload_image",
                    side_effect=lambda *a: events.append(("upload", a[0])) or True,
                ),
                patch.object(
                    rich_menu,
                    "_set_default",
                    side_effect=lambda value: events.append(("default", value)) or True,
                ),
                patch.object(
                    rich_menu,
                    "_delete_menu",
                    side_effect=lambda value: events.append(("delete", value)) or True,
                ),
            ):
                self.assertEqual(rich_menu.setup_default_menu(image.name), "NEW")
        self.assertEqual(
            events,
            [
                ("create", "cowork"),
                ("upload", "NEW"),
                ("default", "NEW"),
                ("delete", "OLD"),
            ],
        )

    def test_generated_asset_matches_line_dimensions(self):
        path = Path(rich_menu.IMAGE_PATH)
        self.assertTrue(path.exists())
        with Image.open(path) as image:
            self.assertEqual(image.size, (2500, 1686))
            self.assertEqual(image.format, "PNG")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from services.line_erp import rich_menu
from services.line_platform import rich_menu as publisher


class ErpLineRichMenuTests(unittest.TestCase):
    def test_payload_has_two_actions_and_four_inert_cells(self):
        payload = rich_menu.build_payload()
        self.assertEqual(payload["size"], {"width": 2500, "height": 1686})
        self.assertEqual(payload["chatBarText"], "เมนู ERP")
        self.assertEqual(len(payload["areas"]), 2)
        self.assertEqual(
            payload["areas"][0],
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "postback",
                    "data": "a=mode%3Apurchase",
                    "displayText": "ซื้อ",
                },
            },
        )
        self.assertEqual(
            payload["areas"][1],
            {
                "bounds": {"x": 833, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "postback",
                    "data": "a=mode%3Asales",
                    "displayText": "ขาย",
                },
            },
        )

    def test_setup_uses_erp_channel_and_dedicated_asset(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as image:
            image.write(b"png")
            image.flush()
            with patch.object(publisher, "replace_default", return_value="NEW") as replace:
                self.assertEqual(rich_menu.setup_default_menu(image.name), "NEW")
        replace.assert_called_once_with(
            "erp",
            "pearnly-erp-v1",
            rich_menu.build_payload(),
            b"png",
        )

    def test_publisher_replaces_old_menu_only_after_new_default(self):
        events = []
        with (
            patch.object(
                publisher,
                "list_menus",
                return_value=[{"name": "pearnly-erp-v1", "richMenuId": "OLD"}],
            ),
            patch.object(
                publisher.line_client,
                "create_rich_menu",
                side_effect=lambda *a, **kw: events.append(("create", kw["channel"])) or "NEW",
            ),
            patch.object(
                publisher,
                "upload_image",
                side_effect=lambda *a: events.append(("upload", a[1])) or True,
            ),
            patch.object(
                publisher,
                "set_default",
                side_effect=lambda *a: events.append(("default", a[1])) or True,
            ),
            patch.object(
                publisher,
                "delete_menu",
                side_effect=lambda *a: events.append(("delete", a[1])) or True,
            ),
        ):
            result = publisher.replace_default(
                "erp",
                "pearnly-erp-v1",
                rich_menu.build_payload(),
                b"png",
            )
        self.assertEqual(result, "NEW")
        self.assertEqual(
            events,
            [
                ("create", "erp"),
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

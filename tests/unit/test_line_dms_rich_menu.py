import os
import tempfile
import unittest
from unittest.mock import patch

from services.line_dms import rich_menu


class DmsRichMenuTests(unittest.TestCase):
    def test_portal_external_url(self):
        with patch.dict(os.environ, {"LINE_DMS_LIFF_ID": "DMS-LIFF"}, clear=False):
            self.assertEqual(
                rich_menu.portal_external_url(),
                "https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1",
            )
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(rich_menu.portal_external_url(), "https://pearnly.com/dms")

    def test_portal_external_url_accepts_dms_or_shared_liff_config(self):
        with patch.dict(
            os.environ,
            {"LINE_DMS_LIFF_ID": "DMS-LIFF", "LINE_LIFF_ID": "SHARED-LIFF"},
            clear=True,
        ):
            self.assertEqual(
                rich_menu.portal_external_url(),
                "https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1",
            )

    def test_credentials_liff_and_desktop_urls(self):
        with patch.dict(os.environ, {"LINE_DMS_LIFF_ID": "DMS-LIFF"}, clear=True):
            self.assertEqual(
                rich_menu.credentials_liff_url(),
                "https://liff.line.me/DMS-LIFF/dms-booking?credentials=dms",
            )
            self.assertEqual(
                rich_menu.credentials_desktop_url(),
                "https://pearnly.com/home/dms-booking?credentials=dms",
            )

    def test_credentials_liff_fallback_does_not_change_portal(self):
        with patch.dict(os.environ, {"LINE_LIFF_ID": "SHARED-LIFF"}, clear=True):
            self.assertEqual(
                rich_menu.credentials_liff_url(),
                "https://liff.line.me/SHARED-LIFF/dms-booking?credentials=dms",
            )
            self.assertEqual(
                rich_menu.portal_external_url(),
                "https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1",
            )
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(rich_menu.credentials_liff_url(), "https://pearnly.com/dms")

    def test_portal_external_url_falls_back_to_shared_liff_id(self):
        with patch.dict(os.environ, {"LINE_LIFF_ID": "SHARED-LIFF"}, clear=True):
            self.assertEqual(
                rich_menu.portal_external_url(),
                "https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1",
            )
        with patch.dict(
            os.environ,
            {"LINE_DMS_LIFF_ID": "  ", "LINE_LIFF_ID": "SHARED-LIFF"},
            clear=True,
        ):
            self.assertEqual(
                rich_menu.portal_external_url(),
                "https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1",
            )

    def test_payload_has_query_in_fifth_cell(self):
        with patch.dict(os.environ, {"LINE_DMS_LIFF_ID": "DMS-LIFF"}, clear=False):
            payload = rich_menu.build_payload(can_query=True)
        self.assertEqual(payload["size"], {"width": 2500, "height": 1686})
        self.assertLessEqual(len(payload["chatBarText"]), 14)
        self.assertEqual(len(payload["areas"]), 5)
        self.assertEqual(
            [(a["bounds"]["x"], a["bounds"]["width"]) for a in payload["areas"][:3]],
            [(0, 833), (833, 833), (1666, 834)],
        )
        self.assertTrue(
            all(
                a["bounds"]["y"] == 0 and a["bounds"]["height"] == 843 for a in payload["areas"][:3]
            )
        )
        self.assertEqual(
            [a["action"]["type"] for a in payload["areas"]],
            ["postback", "postback", "uri", "uri", "postback"],
        )
        self.assertEqual(
            payload["areas"][2]["action"]["uri"],
            "https://pearnly.com/home/dms-booking?portal=dms&openExternalBrowser=1",
        )
        self.assertEqual(
            payload["areas"][3]["bounds"],
            {"x": 0, "y": 843, "width": 833, "height": 843},
        )
        self.assertEqual(
            payload["areas"][3]["action"]["uri"],
            "https://liff.line.me/DMS-LIFF/dms-booking?credentials=dms",
        )
        self.assertEqual(
            payload["areas"][4]["bounds"],
            {"x": 833, "y": 843, "width": 833, "height": 843},
        )
        self.assertEqual(payload["areas"][4]["action"]["data"], "action=menu_query")

    def _image_path(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(b"png")
        tmp.close()
        self.addCleanup(lambda: os.path.exists(tmp.name) and os.unlink(tmp.name))
        return tmp.name

    def test_publish_both_variants_then_sets_safe_default(self):
        events = []
        with (
            patch.object(
                rich_menu.line_client, "create_rich_menu", side_effect=["BASIC", "QUERY"]
            ) as create,
            patch.object(
                rich_menu,
                "_upload_image",
                side_effect=lambda menu_id, *_: events.append(("upload", menu_id)) or True,
            ),
            patch.object(
                rich_menu,
                "_set_default",
                side_effect=lambda menu_id: events.append(("default", menu_id)) or True,
            ),
            patch.object(rich_menu, "_delete_menu") as delete,
        ):
            self.assertEqual(rich_menu.setup_default_menu(self._image_path()), "BASIC")
        self.assertEqual(events, [("upload", "BASIC"), ("upload", "QUERY"), ("default", "BASIC")])
        self.assertEqual([len(c.args[0]["areas"]) for c in create.call_args_list], [4, 5])
        delete.assert_not_called()

    def test_failed_upload_deletes_only_new_menu(self):
        deleted = []
        with (
            patch.object(
                rich_menu,
                "_list_menus",
                return_value=[{"name": rich_menu.MENU_NAME, "richMenuId": "OLD"}],
            ),
            patch.object(rich_menu.line_client, "create_rich_menu", return_value="NEW"),
            patch.object(rich_menu, "_upload_image", return_value=False),
            patch.object(rich_menu, "_set_default") as set_default,
            patch.object(
                rich_menu,
                "_delete_menu",
                side_effect=lambda menu_id: deleted.append(menu_id) or True,
            ),
        ):
            self.assertIsNone(rich_menu.setup_default_menu(self._image_path()))
        self.assertEqual(deleted, ["NEW"])
        set_default.assert_not_called()

    def test_uncertain_default_does_not_delete_possibly_active_menu(self):
        with (
            patch.object(rich_menu.line_client, "create_rich_menu", side_effect=["BASIC", "QUERY"]),
            patch.object(rich_menu, "_upload_image", return_value=True),
            patch.object(rich_menu, "_set_default", return_value=False),
            patch.object(rich_menu, "_delete_menu") as delete,
        ):
            self.assertIsNone(rich_menu.setup_default_menu(self._image_path()))
        delete.assert_not_called()

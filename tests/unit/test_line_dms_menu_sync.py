import unittest
from unittest.mock import patch

from services.line_dms import menu_sync, rich_menu


class MenuPermissionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(
            patch.object(
                rich_menu,
                "_list_menus",
                return_value=[
                    {"name": rich_menu.MENU_NAME, "richMenuId": "basic"},
                    {"name": rich_menu.QUERY_MENU_NAME, "richMenuId": "query"},
                ],
            )
        )

    def test_default_has_only_four_actions_and_no_query(self):
        payload = rich_menu.build_payload()
        self.assertEqual(len(payload["areas"]), 4)
        self.assertNotIn("menu_query", str(payload))
        self.assertEqual(payload["areas"][2]["bounds"]["x"], 0)
        self.assertEqual(payload["areas"][2]["bounds"]["y"], 843)

    def test_permission_revoked_replaces_existing_query_menu(self):
        with (
            patch.object(menu_sync, "_allowed", return_value=False),
            patch.object(menu_sync, "_request", return_value={"richMenuId": "query"}) as api,
        ):
            menu_sync.sync("line-1")
        api.assert_any_call("POST", "user/line-1/richmenu/basic")

    def test_permission_change_during_remote_link_is_reconciled(self):
        with (
            patch.object(menu_sync, "_allowed", side_effect=[True, False, False, False]),
            patch.object(menu_sync, "_request", return_value={}) as api,
        ):
            menu_sync.sync("line-1")
        self.assertEqual(
            [c.args[1] for c in api.call_args_list if c.args[0] == "POST"],
            ["user/line-1/richmenu/query", "user/line-1/richmenu/basic"],
        )

    def test_stable_menu_is_not_relinked(self):
        with (
            patch.object(menu_sync, "_allowed", return_value=False),
            patch.object(menu_sync, "_request", return_value={"richMenuId": "basic"}) as api,
        ):
            menu_sync.sync("line-1")
        api.assert_called_once_with("GET", "user/line-1/richmenu")

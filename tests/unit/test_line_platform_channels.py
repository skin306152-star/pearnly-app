# -*- coding: utf-8 -*-
"""LINE OA registry: public identity is browser-safe and credential resolution stays env-only.

Multi-OA acceptance depends on the browser never receiving secret material and on every public
field (display name, Basic ID, add-friend URL, QR payload) coming from one source of truth.
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.line_platform import channels


class PublicIdentityTests(unittest.TestCase):
    def test_three_dms_oas_registered_with_stable_keys(self):
        keys = [c["channel_key"] for c in channels.list_public()]
        self.assertEqual(keys, ["dms", "dms_a", "dms_b"])

    def test_public_payload_has_no_secret_material(self):
        allowed = {
            "channel_key",
            "channel_name",
            "basic_id",
            "add_friend_url",
            "qr_image_url",
        }
        for item in channels.list_public():
            self.assertEqual(set(item), allowed)
            blob = str(item).lower()
            for forbidden in ("secret", "token", "access_token", "channel_secret"):
                self.assertNotIn(forbidden, blob)

    def test_basic_ids_and_display_names(self):
        self.assertEqual(channels.public("dms")["basic_id"], "@264tuqln")
        self.assertEqual(channels.public("dms")["channel_name"], "ลั่วหยง DMS")
        self.assertEqual(channels.public("dms_a")["basic_id"], "@260oecde")
        self.assertEqual(channels.public("dms_a")["channel_name"], "A DMS")
        self.assertEqual(channels.public("dms_b")["basic_id"], "@145xbbjo")
        self.assertEqual(channels.public("dms_b")["channel_name"], "B DMS")

    def test_qr_payload_matches_add_friend_url(self):
        """QR 内容、加好友链接、Basic ID 必须同源 —— 弹窗三者不许漂移。"""
        for key in ("dms", "dms_a", "dms_b"):
            item = channels.public(key)
            self.assertEqual(item["add_friend_url"], "https://line.me/R/ti/p/" + item["basic_id"])
            self.assertIn(
                channels.qr_image_url(item["add_friend_url"]).split("data=", 1)[1],
                item["qr_image_url"],
            )
            self.assertTrue(item["qr_image_url"].endswith("%40" + item["basic_id"][1:]))

    def test_unknown_key_falls_back_to_legacy_default(self):
        self.assertEqual(channels.normalize("nope"), "dms")
        self.assertEqual(channels.public("nope")["channel_key"], "dms")
        self.assertFalse(channels.is_valid("nope"))
        self.assertIsNone(channels.get("nope"))

    def test_resolve_is_strict_for_invariant_paths(self):
        """Binding/state/lock scoping must never rewrite an unknown key to the legacy OA."""
        self.assertEqual(channels.resolve(""), "dms")
        self.assertEqual(channels.resolve(None), "dms")
        self.assertEqual(channels.resolve("dms_b"), "dms_b")
        self.assertIsNone(channels.resolve("nope"))
        self.assertEqual(channels.resolve(" dms_a "), "dms_a")
        self.assertIsNone(channels.resolve(" nope "))

    def test_liff_id_never_falls_back_across_oas(self):
        with mock.patch.dict(
            "os.environ",
            {"LINE_DMS_LIFF_ID": "DMS-LIFF", "LINE_LIFF_ID": "SHARED-LIFF"},
            clear=True,
        ):
            self.assertEqual(channels.liff_id("dms"), "DMS-LIFF")
            self.assertEqual(channels.liff_id("dms_a"), "")  # 不给 A/B 回落旧 LIFF
            self.assertEqual(channels.liff_id("dms_b"), "")
        with mock.patch.dict("os.environ", {"LINE_DMS_A_LIFF_ID": "A-LIFF"}, clear=True):
            self.assertEqual(channels.liff_id("dms_a"), "A-LIFF")

    def test_menu_name_suffix_only_for_non_legacy(self):
        self.assertEqual(channels.menu_name("pearnly-dms-basic", "dms"), "pearnly-dms-basic")
        self.assertEqual(
            channels.menu_name("pearnly-dms-basic", "dms_a"), "pearnly-dms-basic-dms_a"
        )

    def test_liff_env_name_is_per_channel_and_unknown_is_empty(self):
        self.assertEqual(channels.liff_env_name("dms"), "LINE_DMS_LIFF_ID")
        self.assertEqual(channels.liff_env_name("dms_a"), "LINE_DMS_A_LIFF_ID")
        self.assertEqual(channels.liff_env_name("dms_b"), "LINE_DMS_B_LIFF_ID")
        self.assertEqual(channels.liff_env_name("nope"), "")


class CredentialResolutionTests(unittest.TestCase):
    def test_individual_env_wins(self):
        with mock.patch.dict(
            "os.environ",
            {
                "LINE_DMS_A_CHANNEL_SECRET": "sec",
                "LINE_DMS_A_CHANNEL_ACCESS_TOKEN": "tok",
                "LINE_DMS_A_CREDENTIALS": '{"channel_secret": "blobsec", "channel_access_token": "blobtok"}',
            },
            clear=True,
        ):
            self.assertEqual(
                channels.resolve_credentials(
                    "LINE_DMS_A_CHANNEL_SECRET",
                    "LINE_DMS_A_CHANNEL_ACCESS_TOKEN",
                    "LINE_DMS_A_CREDENTIALS",
                ),
                ("sec", "tok"),
            )

    def test_json_blob_fallback(self):
        with mock.patch.dict(
            "os.environ",
            {"LINE_DMS_B_CREDENTIALS": '{"channel_secret": "bs", "channel_access_token": "bt"}'},
            clear=True,
        ):
            self.assertEqual(
                channels.resolve_credentials(
                    "LINE_DMS_B_CHANNEL_SECRET",
                    "LINE_DMS_B_CHANNEL_ACCESS_TOKEN",
                    "LINE_DMS_B_CREDENTIALS",
                ),
                ("bs", "bt"),
            )

    def test_dotenv_blob_fallback(self):
        blob = "LINE_DMS_A_CHANNEL_SECRET=ds\nLINE_DMS_A_CHANNEL_ACCESS_TOKEN=dt\n"
        with mock.patch.dict("os.environ", {"LINE_DMS_A_CREDENTIALS": blob}, clear=True):
            self.assertEqual(
                channels.resolve_credentials(
                    "LINE_DMS_A_CHANNEL_SECRET",
                    "LINE_DMS_A_CHANNEL_ACCESS_TOKEN",
                    "LINE_DMS_A_CREDENTIALS",
                ),
                ("ds", "dt"),
            )

    def test_secret_manager_blob_uses_line_channel_field_names(self):
        """A/B Secret Manager 挂载的 JSON 用 LINE_CHANNEL_SECRET/ACCESS_TOKEN 两个字段。"""
        blob = '{"LINE_CHANNEL_SECRET": "sm-sec", "LINE_CHANNEL_ACCESS_TOKEN": "sm-tok"}'
        with mock.patch.dict("os.environ", {"LINE_DMS_B_CREDENTIALS": blob}, clear=True):
            self.assertEqual(
                channels.resolve_credentials(
                    "LINE_DMS_B_CHANNEL_SECRET",
                    "LINE_DMS_B_CHANNEL_ACCESS_TOKEN",
                    "LINE_DMS_B_CREDENTIALS",
                ),
                ("sm-sec", "sm-tok"),
            )

    def test_per_channel_field_names_win_over_generic_blob_fields(self):
        blob = (
            '{"channel_secret": "per", "channel_access_token": "pertok", '
            '"LINE_CHANNEL_SECRET": "generic", "LINE_CHANNEL_ACCESS_TOKEN": "generictok"}'
        )
        with mock.patch.dict("os.environ", {"LINE_DMS_A_CREDENTIALS": blob}, clear=True):
            self.assertEqual(
                channels.resolve_credentials(
                    "LINE_DMS_A_CHANNEL_SECRET",
                    "LINE_DMS_A_CHANNEL_ACCESS_TOKEN",
                    "LINE_DMS_A_CREDENTIALS",
                ),
                ("per", "pertok"),
            )

    def test_missing_material_is_empty_not_error(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                channels.resolve_credentials("X_SECRET", "X_TOKEN", "X_CREDENTIALS"), ("", "")
            )
            self.assertEqual(channels.resolve_credentials("", "", ""), ("", ""))


if __name__ == "__main__":
    unittest.main()

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

    def test_dms_oas_reuse_their_provider_liff_unless_overridden(self):
        with mock.patch.dict(
            "os.environ",
            {"LINE_DMS_LIFF_ID": "DMS-LIFF", "LINE_LIFF_ID": "SHARED-LIFF"},
            clear=True,
        ):
            self.assertEqual(channels.liff_id("dms"), "DMS-LIFF")
            self.assertEqual(channels.liff_id("dms_a"), "SHARED-LIFF")
            self.assertEqual(channels.liff_id("dms_b"), "SHARED-LIFF")
        with mock.patch.dict("os.environ", {"LINE_DMS_A_LIFF_ID": "A-LIFF"}, clear=True):
            self.assertEqual(channels.liff_id("dms_a"), "A-LIFF")

    def test_menu_name_suffix_only_for_non_legacy(self):
        self.assertEqual(channels.menu_name("pearnly-dms-basic", "dms"), "pearnly-dms-basic")
        self.assertEqual(
            channels.menu_name("pearnly-dms-basic", "dms_a"), "pearnly-dms-basic-dms_a"
        )

    def test_liff_env_name_tracks_override_or_provider_fallback(self):
        with mock.patch.dict("os.environ", {"LINE_LIFF_ID": "SHARED"}, clear=True):
            self.assertEqual(channels.liff_env_name("dms"), "LINE_LIFF_ID")
            self.assertEqual(channels.liff_env_name("dms_a"), "LINE_LIFF_ID")
            self.assertEqual(channels.liff_env_name("dms_b"), "LINE_LIFF_ID")
            self.assertEqual(channels.liff_env_name("nope"), "")
        with mock.patch.dict("os.environ", {"LINE_DMS_A_LIFF_ID": "A-LIFF"}, clear=True):
            self.assertEqual(channels.liff_env_name("dms_a"), "LINE_DMS_A_LIFF_ID")


class RegistryDeclarationGateTests(unittest.TestCase):
    """新增 OA 的门禁:registry 条目必须显式声明 LIFF 归属与独立凭据 env 名。

    同 Provider 复用共享 LINE Login 应用是**声明式**的:只写在 ``provider_liff_env`` 里。
    没有声明(未来新 OA 忘了填)→ liff_id/liff_env_name 都是空、签名入口不借共享 LIFF,
    由下面这条失败关闭断言与 test_dms_channel_registry_contract 的公共契约一起拦住。
    """

    def test_every_channel_declares_its_liff_ownership(self):
        for key, cfg in channels.DMS_CHANNELS.items():
            with self.subTest(channel=key):
                self.assertTrue(cfg.liff_env, f"{key} 缺自己的 LIFF env 名")
                self.assertIn(
                    cfg.provider_liff_env,
                    channels.PROVIDER_LIFF_ENVS,
                    f"{key} 的 provider LIFF 必须是 registry 声明的共享 Provider 应用",
                )

    def test_credential_and_liff_envs_are_unique_per_channel(self):
        for field in ("secret_env", "token_env", "credentials_env", "liff_env"):
            values = [getattr(cfg, field) for cfg in channels.DMS_CHANNELS.values()]
            with self.subTest(field=field):
                self.assertEqual(len(values), len(set(values)), values)

    def test_provider_liff_envs_are_verifiable_login_channels(self):
        from services.line_platform import liff

        self.assertTrue(
            set(channels.PROVIDER_LIFF_ENVS) <= set(liff._SHARED_LOGIN_CHANNEL_ENVS),
            "共享 Provider LIFF env 必须能通过 verify_id_token 的共享登录频道判定",
        )

    def test_channel_without_liff_declaration_fails_closed(self):
        bare = channels.LineChannel(
            key="dms_c",
            product="dms",
            display_name="C DMS",
            basic_id="@000c",
            secret_env="LINE_DMS_C_CHANNEL_SECRET",
            token_env="LINE_DMS_C_CHANNEL_ACCESS_TOKEN",
        )
        with (
            mock.patch.dict(channels.DMS_CHANNELS, {"dms_c": bare}),
            mock.patch.dict("os.environ", {"LINE_LIFF_ID": "SHARED-LIFF"}, clear=True),
        ):
            self.assertEqual(channels.liff_id("dms_c"), "")
            self.assertEqual(channels.liff_env_name("dms_c"), "")
            self.assertEqual(channels.webhook_path("dms_c"), "/api/line/dms/webhook/c")

    def test_unknown_channel_has_no_liff_and_no_webhook(self):
        with mock.patch.dict("os.environ", {"LINE_LIFF_ID": "SHARED-LIFF"}, clear=True):
            self.assertEqual(channels.liff_id("dms_zzz"), "")
            self.assertEqual(channels.liff_env_name("dms_zzz"), "")
        self.assertEqual(channels.webhook_path("dms_zzz"), "")
        self.assertEqual(channels.webhook_path("nope"), "")

    def test_webhook_paths_match_the_registered_entrances(self):
        self.assertEqual(channels.webhook_path(""), "/api/line/dms/webhook")
        self.assertEqual(channels.webhook_path("dms"), "/api/line/dms/webhook")
        self.assertEqual(channels.webhook_path("dms_a"), "/api/line/dms/webhook/a")
        self.assertEqual(channels.webhook_path("dms_b"), "/api/line/dms/webhook/b")


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

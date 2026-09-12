# -*- coding: utf-8 -*-
"""Multi-OA frontend contract: the bind-code dialog renders the assigned OA from the API only.

No OA constant may live in the roster source. LINE ID / QR / add-friend link all come from the
same backend ``line`` object, so changing an account's OA never needs a frontend edit.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class RosterDialogContractTests(unittest.TestCase):
    def test_roster_html_has_no_hardcoded_oa(self):
        source = _read("static/dms/dms-roster-html.js")
        self.assertNotIn("264tuqln", source)
        self.assertNotIn("line.me/R/ti/p/", source)
        self.assertNotIn("FRIEND_URL", source)
        self.assertNotIn("QR_URL", source)

    def test_roster_html_renders_from_api_line_object(self):
        source = _read("static/dms/dms-roster-html.js")
        self.assertIn('id="dms-op-code-line"', source)
        self.assertIn("function lineBlock(line)", source)
        self.assertIn("lineBlock: lineBlock", source)
        for field in ("add_friend_url", "qr_image_url", "basic_id", "channel_name"):
            self.assertIn(field, source)

    def test_roster_logic_fills_block_from_bind_code_response(self):
        source = _read("static/dms/dms-roster.js")
        self.assertIn("renderLineBlock(d.line)", source)
        self.assertIn("H().lineBlock(line)", source)
        self.assertIn("dms-op-code-line", source)

    def test_built_bundle_has_no_hardcoded_oa(self):
        dist = ROOT / "static/dist/dms.js"
        if not dist.exists():
            self.skipTest("dms bundle not built in this checkout")
        self.assertNotIn("264tuqln", dist.read_text(encoding="utf-8"))

    def test_bundle_includes_roster_html_module(self):
        self.assertIn("dms/dms-roster-html.js", _read("scripts/build-home-js.mjs"))


class AdminInviteContractTests(unittest.TestCase):
    def test_admin_html_has_channel_select(self):
        source = _read("static/admin/admin.html")
        self.assertIn('id="adm-dms-invite-channel"', source)
        self.assertIn("adm-dms-oa-label", source)

    def test_admin_js_sends_channel_and_supports_change(self):
        source = _read("static/admin/admin.js")
        self.assertIn("line_channel_key", source)
        self.assertIn("/api/admin/dms/channel", source)
        self.assertIn("data-adm-dms-oa", source)
        self.assertIn("adm-dms-oa-change-confirm", source)

    def test_admin_js_channel_options_come_from_api(self):
        source = _read("static/admin/admin.js")
        self.assertIn("_fillDmsChannels", source)
        self.assertIn("d.channels", source)


class I18nContractTests(unittest.TestCase):
    def test_dms_line_id_key_in_every_language(self):
        for lang in ("th", "zh", "en", "ja"):
            with self.subTest(lang=lang):
                self.assertIn("dms-op-code-line-id", _read(f"static/dms/dms-i18n-{lang}.js"))

    def test_admin_oa_keys_in_both_languages(self):
        source = _read("static/admin/admin-i18n.js")
        for key in (
            "adm-dms-oa-label",
            "adm-dms-oa-save-btn",
            "adm-dms-oa-change-confirm",
            "adm-dms-line-bound-count",
            "adm-dms-line-unbound",
            "adm-dms-invalid-channel",
        ):
            with self.subTest(key=key):
                self.assertGreaterEqual(source.count("'" + key + "'"), 2)


class BookingLiffChannelContractTests(unittest.TestCase):
    """The LIFF editor must carry the entry OA through URL, liff.state, config and auth."""

    def test_api_reads_channel_from_url_and_liff_state(self):
        source = _read("static/dms-booking-edit/dms-booking-api.js")
        self.assertIn("liff.state", source)
        self.assertIn("param('channel')", source)
        self.assertIn("encodeURIComponent(channel)", source)

    def test_api_sends_channel_to_config_and_auth(self):
        source = _read("static/dms-booking-edit/dms-booking-api.js")
        self.assertIn("/api/line/dms-booking/config", source)
        self.assertIn("channel: channelKey", source)
        self.assertIn("dms_booking.liff_unavailable", source)
        self.assertIn("redirectUri: window.location.href", source)

    def test_editor_maps_liff_unavailable_to_its_own_message(self):
        source = _read("static/dms-booking-edit/dms-booking-edit.js")
        self.assertIn("function errorKey(e, fallback)", source)
        self.assertIn("ERROR_KEYS[e.code]", source)
        i18n = _read("static/dms-booking-edit/dms-booking-i18n.js")
        self.assertIn("'dms_booking.liff_unavailable': 'liffUnavailable'", i18n)
        for lang in ("th", "en", "zh", "ja"):
            with self.subTest(lang=lang):
                self.assertIn("liffUnavailable", i18n)

    def test_shell_bumps_changed_scripts(self):
        html = _read("static/dms-booking-edit/dms-booking-edit.html")
        for needle in (
            "dms-booking-i18n.js?v=9",
            "dms-booking-api.js?v=7",
            "dms-credentials.js?v=5",
            "dms-booking-edit.js?v=16",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, html)


if __name__ == "__main__":
    unittest.main()

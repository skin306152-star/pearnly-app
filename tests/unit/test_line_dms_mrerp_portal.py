# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from services.line_dms import mrerp_portal


class MrerpPortalCredentialTests(unittest.TestCase):
    @patch("services.erp.erp_dms_push._dms_plain_creds", return_value=("staff", "secret"))
    @patch("services.erp.dms_id_ocr.resolve_dms_endpoint")
    def test_uses_current_employees_endpoint(self, resolve, plain_creds):
        resolve.return_value = {"config": {"username_enc": "cipher"}}
        self.assertEqual(mrerp_portal.load_credentials("user-9"), ("staff", "secret"))
        resolve.assert_called_once_with("user-9", None)
        plain_creds.assert_called_once_with(resolve.return_value["config"])

    @patch("services.erp.dms_id_ocr.resolve_dms_endpoint", return_value=None)
    def test_missing_endpoint_is_honest(self, _resolve):
        with self.assertRaises(mrerp_portal.PortalCredentialsMissing):
            mrerp_portal.load_credentials("user-9")

    @patch("services.erp.erp_dms_push._dms_plain_creds", return_value=("", ""))
    @patch("services.erp.dms_id_ocr.resolve_dms_endpoint", return_value={"config": {}})
    def test_missing_credentials_is_honest(self, _resolve, _plain_creds):
        with self.assertRaises(mrerp_portal.PortalCredentialsMissing):
            mrerp_portal.load_credentials("user-9")

    @patch("services.erp.erp_dms_push._dms_plain_creds", side_effect=ValueError("bad key"))
    @patch("services.erp.dms_id_ocr.resolve_dms_endpoint", return_value={"config": {}})
    def test_decryption_error_does_not_escape(self, _resolve, _plain_creds):
        with self.assertRaisesRegex(mrerp_portal.PortalUnavailable, "credential_unavailable"):
            mrerp_portal.load_credentials("user-9")


class MrerpPortalHtmlTests(unittest.TestCase):
    def setUp(self):
        self.password = "p&ss'\"><script>alert(1)</script>"
        self.page, self.nonce = mrerp_portal.render_login_relay("u&'\"", self.password)

    def test_posts_expected_fields_to_mrerp(self):
        self.assertIn(f'action="{mrerp_portal.MRERP_LOGIN_URL}"', self.page)
        self.assertIn('name="txtusers"', self.page)
        self.assertIn('name="txtpasswords"', self.page)
        self.assertIn('name="btnsubmit" value="Submit"', self.page)
        self.assertNotIn("<iframe", self.page)

    def test_credentials_are_attribute_escaped(self):
        self.assertNotIn(self.password, self.page)
        self.assertIn("p&amp;ss&#x27;&quot;&gt;&lt;script&gt;", self.page)
        self.assertNotIn("<script>alert(1)</script>", self.page)

    def test_user_click_opens_top_level_mrerp_before_login_and_navigation(self):
        self.assertIn("button.addEventListener('click'", self.page)
        self.assertIn(f"window.open('{mrerp_portal.MRERP_ROOT_URL}',windowName)", self.page)
        self.assertIn("form.target=windowName", self.page)
        self.assertIn("form.submit()", self.page)
        self.assertIn("input.value=''", self.page)
        self.assertIn("form.remove()", self.page)
        self.assertIn(f"portal.location='{mrerp_portal.MRERP_HOME_URL}'", self.page)

    def test_visible_relay_copy_is_thai(self):
        self.assertIn('<html lang="th">', self.page)
        self.assertIn("เข้าสู่ระบบ DMS", self.page)
        self.assertIn("กดปุ่มด้านล่างเพื่อเปิดระบบ DMS ในเบราว์เซอร์", self.page)
        self.assertNotIn("Confirm", self.page)
        self.assertNotIn("确认", self.page)

    def test_password_never_appears_in_a_url_or_storage_call(self):
        for url in (
            mrerp_portal.MRERP_LOGIN_URL,
            mrerp_portal.MRERP_HOME_URL,
            mrerp_portal.MRERP_ROOT_URL,
        ):
            self.assertNotIn(self.password, url)
        for forbidden in ("localStorage", "sessionStorage", "indexedDB", "document.cookie"):
            self.assertNotIn(forbidden, self.page)

    def test_nonce_is_applied_to_inline_code(self):
        self.assertIn(f'<script nonce="{self.nonce}">', self.page)
        self.assertIn(f'<style nonce="{self.nonce}">', self.page)

    def test_security_headers_are_no_store_and_origin_limited(self):
        headers = mrerp_portal.security_headers(self.nonce)
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(headers["Pragma"], "no-cache")
        self.assertEqual(headers["Expires"], "0")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(headers["X-Robots-Tag"], "noindex, nofollow")
        csp = headers["Content-Security-Policy"]
        self.assertIn(f"script-src 'nonce-{self.nonce}'", csp)
        self.assertIn(f"form-action {mrerp_portal.MRERP_ORIGIN}", csp)
        self.assertNotIn("frame-src", csp)


if __name__ == "__main__":
    unittest.main()

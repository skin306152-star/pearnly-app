# -*- coding: utf-8 -*-
"""Contract tests for the user settings DAL reexports."""

import unittest
from unittest import mock

from core import db
from services.user_settings import store


class UserSettingsReexportContract(unittest.TestCase):
    def test_funcs_provided_by_service_and_reexported(self):
        names = [
            "get_user_dup_check_enabled",
            "set_user_dup_check_enabled",
            "set_user_gemini_key",
            "get_user_gemini_key",
            "get_user_gemini_key_masked",
            "update_user_preferred_lang",
        ]
        for name in names:
            self.assertTrue(hasattr(store, name), f"service missing {name}")
            self.assertIs(getattr(db, name), getattr(store, name))

    def test_preferred_lang_rejects_bad_lang(self):
        with mock.patch("core.db.get_cursor", side_effect=AssertionError("must not hit DB")):
            self.assertFalse(store.update_user_preferred_lang("u1", "xx"))


class UserSettingsBehaviorContract(unittest.TestCase):
    def _fake_cursor(self, fetchone_ret):
        cur = mock.MagicMock()
        cur.fetchone.return_value = fetchone_ret
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur
        ctx.__exit__.return_value = False
        return ctx, cur

    def test_dup_check_defaults_true_when_no_row(self):
        ctx, _ = self._fake_cursor(None)
        with mock.patch("core.db.get_cursor", return_value=ctx):
            self.assertTrue(store.get_user_dup_check_enabled("u1"))

    def test_gemini_key_masked_preview(self):
        with mock.patch.object(store, "get_user_gemini_key", return_value="AIzaSomeLongKey9Y2"):
            out = store.get_user_gemini_key_masked("u1")
        self.assertTrue(out["has_key"])
        self.assertEqual(out["preview"], "AIza...y9Y2")

    def test_gemini_key_masked_no_key(self):
        with mock.patch.object(store, "get_user_gemini_key", return_value=None):
            self.assertEqual(
                store.get_user_gemini_key_masked("u1"), {"has_key": False, "preview": ""}
            )


if __name__ == "__main__":
    unittest.main()

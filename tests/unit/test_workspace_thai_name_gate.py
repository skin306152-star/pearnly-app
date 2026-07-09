# -*- coding: utf-8 -*-
"""M1-B2 · services.workspace.thai_name_gate 单测(泰文注册名判定 + 错误文案)。"""

import unittest

from services.workspace import thai_name_gate as gate


class HasThaiRegisteredNameTests(unittest.TestCase):
    def test_pure_thai_name_true(self):
        self.assertTrue(gate.has_thai_registered_name("บริษัท ปิยะนุช จำกัด"))

    def test_mixed_thai_and_latin_true(self):
        self.assertTrue(gate.has_thai_registered_name("Sister Makeup บริษัท จำกัด"))

    def test_single_thai_char_true(self):
        self.assertTrue(gate.has_thai_registered_name("ABC ก"))

    def test_pure_english_false(self):
        self.assertFalse(gate.has_thai_registered_name("Sister Makeup Co Ltd"))

    def test_none_false(self):
        self.assertFalse(gate.has_thai_registered_name(None))

    def test_empty_string_false(self):
        self.assertFalse(gate.has_thai_registered_name(""))

    def test_whitespace_only_false(self):
        self.assertFalse(gate.has_thai_registered_name("   "))

    def test_digits_and_symbols_only_false(self):
        self.assertFalse(gate.has_thai_registered_name("ACME-01 #2"))


class ErrorPayloadTests(unittest.TestCase):
    def test_required_code_has_four_languages(self):
        out = gate.error_payload(gate.ERR_THAI_NAME_REQUIRED)
        self.assertEqual(out["code"], gate.ERR_THAI_NAME_REQUIRED)
        for lang in ("zh", "en", "th", "ja"):
            self.assertTrue(out["message"][lang].strip())

    def test_locked_code_has_four_languages(self):
        out = gate.error_payload(gate.ERR_THAI_NAME_LOCKED)
        self.assertEqual(out["code"], gate.ERR_THAI_NAME_LOCKED)
        for lang in ("zh", "en", "th", "ja"):
            self.assertTrue(out["message"][lang].strip())


if __name__ == "__main__":
    unittest.main()

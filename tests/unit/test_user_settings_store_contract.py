# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · user_settings DAL 抽取契约

锁定:
  1. 7 个函数 + ERP_PUSH_MODES 常量都从 services.user_settings.store 提供,
     且 db.py 经 re-export 暴露同一对象(调用点 db.xxx 零改动)。
  2. 纯结构性搬家 0 逻辑改:验关键行为(默认值/非法值拒写/遮罩)经
     mock.patch("core.db.get_cursor") 仍生效。
"""

import unittest
from unittest import mock

from core import db
from services.user_settings import store


class UserSettingsReexportContract(unittest.TestCase):
    def test_funcs_provided_by_service_and_reexported(self):
        names = [
            "get_user_dup_check_enabled",
            "set_user_dup_check_enabled",
            "get_erp_push_mode",
            "set_erp_push_mode",
            "set_user_gemini_key",
            "get_user_gemini_key",
            "get_user_gemini_key_masked",
            "update_user_preferred_lang",  # REFACTOR-B2 · 后搬入
        ]
        for n in names:
            self.assertTrue(hasattr(store, n), f"service missing {n}")
            self.assertIs(
                getattr(db, n), getattr(store, n), f"db.{n} not re-exporting service object"
            )

    def test_erp_push_modes_constant(self):
        self.assertEqual(store.ERP_PUSH_MODES, ("smart", "fixed", "ocr_only"))
        self.assertIs(db.ERP_PUSH_MODES, store.ERP_PUSH_MODES)

    def test_preferred_lang_rejects_bad_lang(self):
        # 非法语言码 → 早返 False,不触库
        with mock.patch("core.db.get_cursor", side_effect=AssertionError("must not hit DB")):
            self.assertFalse(store.update_user_preferred_lang("u1", "xx"))

    def test_set_erp_push_mode_rejects_garbage(self):
        # 非法值不触库直接 False(纯逻辑 · 不需 cursor)
        self.assertFalse(store.set_erp_push_mode("u1", "garbage"))
        self.assertFalse(store.set_erp_push_mode("u1", ""))


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

    def test_erp_push_mode_defaults_smart_on_bad_value(self):
        ctx, _ = self._fake_cursor({"erp_push_mode": "weird"})
        with mock.patch("core.db.get_cursor", return_value=ctx):
            self.assertEqual(store.get_erp_push_mode("u1"), "smart")

    def test_gemini_key_masked_preview(self):
        with mock.patch.object(store, "get_user_gemini_key", return_value="AIzaSomeLongKey9Y2"):
            out = store.get_user_gemini_key_masked("u1")
        self.assertTrue(out["has_key"])
        self.assertEqual(out["preview"], "AIza...y9Y2")  # 前4 + 后4

    def test_gemini_key_masked_no_key(self):
        with mock.patch.object(store, "get_user_gemini_key", return_value=None):
            self.assertEqual(
                store.get_user_gemini_key_masked("u1"), {"has_key": False, "preview": ""}
            )


if __name__ == "__main__":
    unittest.main()

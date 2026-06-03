# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · LINE 绑定 DAL 抽取契约

锁定:
  1. 6 个函数从 services.line_binding.store 提供,db.py 经 re-export 暴露同一对象
     (调用点 db.xxx 零改动 · app/line_binding_routes/notification_routes/exception_checks)。
  2. 纯结构性 0 逻辑改:consume_line_binding_code 的格式校验(非 6 位数字早返 None · 不触库)
     经 mock.patch("core.db.get_cursor") 仍生效。
"""

import unittest
from unittest import mock

from core import db
from services.line_binding import store


class LineBindingReexportContract(unittest.TestCase):
    def test_funcs_reexported_same_object(self):
        for n in [
            "generate_line_binding_code",
            "consume_line_binding_code",
            "create_or_update_line_binding",
            "get_line_binding_by_user",
            "get_user_by_line_user_id",
            "unbind_line_by_user",
        ]:
            self.assertTrue(hasattr(store, n), f"service missing {n}")
            self.assertIs(
                getattr(db, n), getattr(store, n), f"db.{n} not re-exporting service object"
            )


class LineBindingBehaviorContract(unittest.TestCase):
    def test_consume_rejects_bad_format_without_db(self):
        # 非 6 位数字 → 早返 None,不应触库
        with mock.patch("core.db.get_cursor", side_effect=AssertionError("must not hit DB")):
            for bad in ["", "abc", "12345", "1234567", "12a456", None]:
                self.assertIsNone(store.consume_line_binding_code(bad))

    def test_consume_valid_code_returns_user_id(self):
        cur = mock.MagicMock()
        cur.fetchone.return_value = {"user_id": "u-9"}
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur
        ctx.__exit__.return_value = False
        with mock.patch("core.db.get_cursor", return_value=ctx):
            self.assertEqual(store.consume_line_binding_code("123456"), "u-9")


if __name__ == "__main__":
    unittest.main()

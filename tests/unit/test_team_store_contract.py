# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 员工管理 DAL 抽到 services/team/store.py

验证 4 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
add_employee 复用 db.find_user_by_username(留在 db.py)· 经 db.* 调用 · 可被 patch。
"""

import unittest

from core import db
from services.team import store

_MOVED = [
    "list_employees",
    "add_employee",
    "remove_employee",
    "toggle_employee_active",
]


class TeamStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"team.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")

    def test_add_employee_uses_db_find_user_by_username(self):
        # add_employee 内部走 db.find_user_by_username(留 db.py)· patch 应可拦截 ·
        # 命中已存在用户 → 返回 None(不建重复用户名)
        from unittest import mock

        with mock.patch("core.db.find_user_by_username", return_value={"id": "existing"}) as m:
            rid = db.add_employee("tenant-1", "dupuser", "pw123456")
        self.assertTrue(m.called, "add_employee 未经 db.find_user_by_username(re-export 失效?)")
        self.assertIsNone(rid)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""员工操作 DAL 单一来源守门(批5:services/team/store.py 处决 · 活函数并入 console_store)。

验证 3 个函数活在 console_store(调用点直调模块 · 不再经 db.* re-export,防 dal_reexports
循环 import);旧模块 services/team/store 与 db.* 旧名不许复活;add_employee 随宿主退役。
"""

import unittest

from core import db
from services.team import console_store

_MOVED = [
    "list_employees",
    "remove_employee",
    "toggle_employee_active",
]


class TeamStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_console_store(self):
        for name in _MOVED:
            self.assertTrue(hasattr(console_store, name), f"team.console_store 缺 {name}")
            self.assertTrue(callable(getattr(console_store, name)), name)

    def test_db_legacy_names_retired(self):
        for name in _MOVED + ["add_employee"]:
            self.assertFalse(hasattr(db, name), f"db.{name} 应随旧团队管理退役(直调 console_store)")

    def test_legacy_store_module_gone(self):
        with self.assertRaises(ModuleNotFoundError):
            import services.team.store  # noqa: F401

    def test_routes_call_console_store(self):
        import inspect

        from routes import admin_users_query_routes, console_team_routes

        self.assertIn(
            "console_store.list_employees",
            inspect.getsource(admin_users_query_routes.admin_user_detail),
        )
        self.assertIn(
            "console_store.remove_employee",
            inspect.getsource(console_team_routes.remove_member),
        )
        self.assertIn(
            "console_store.toggle_employee_active",
            inspect.getsource(console_team_routes.toggle_member),
        )


if __name__ == "__main__":
    unittest.main()

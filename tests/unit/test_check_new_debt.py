#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_new_debt.scan_diff 纯函数单测(REFACTOR-WC)
=================================================
喂合成 `git diff --unified=0` 文本,验证铁律 #5/#17 反模式检测无 git 依赖。
"""

import importlib.util
import unittest
from pathlib import Path

# scripts/ 非包 · 用 spec 直接按路径加载 check_new_debt
_MOD_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_new_debt.py"
_spec = importlib.util.spec_from_file_location("check_new_debt", _MOD_PATH)
check_new_debt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_new_debt)
scan_diff = check_new_debt.scan_diff


def _diff(path: str, added_lines: list[str]) -> str:
    """造一段最小 unified=0 diff:一个文件 + 若干新增行。"""
    body = "\n".join("+" + ln for ln in added_lines)
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        f"@@ -0,0 +1,{len(added_lines)} @@\n"
        f"{body}\n"
    )


class TestEnsureLaw5(unittest.TestCase):
    def test_new_ensure_in_db_flagged(self):
        d = _diff("db.py", ["def ensure_widgets_table(conn):", "    pass"])
        v = scan_diff(d)
        self.assertEqual(len(v), 1)
        self.assertIn("#5", v[0][0])
        self.assertEqual(v[0][1], "db.py")

    def test_new_ensure_in_services_flagged(self):
        d = _diff("services/billing/store.py", ["    async def ensure_ledger(self):"])
        v = scan_diff(d)
        self.assertEqual(len(v), 1)
        self.assertIn("#5", v[0][0])

    def test_ensure_outside_monitored_paths_ok(self):
        # 测试文件 / 其它模块里的 ensure_* 不拦(只盯 db.py + services/**)
        d = _diff("tests/unit/test_foo.py", ["def ensure_fixture():"])
        self.assertEqual(scan_diff(d), [])

    def test_non_ensure_def_ok(self):
        d = _diff("db.py", ["def get_user(uid):", "    return None"])
        self.assertEqual(scan_diff(d), [])

    def test_ensure_call_not_def_ok(self):
        # 调用 ensure_x() 不是定义 → 不拦
        d = _diff("services/x.py", ["    ensure_table_exists(conn)"])
        self.assertEqual(scan_diff(d), [])


class TestAppRouteLaw17(unittest.TestCase):
    def test_new_app_get_in_app_py_flagged(self):
        d = _diff("app.py", ['@app.get("/api/new")', "async def new_ep():"])
        v = scan_diff(d)
        self.assertEqual(len(v), 1)
        self.assertIn("#17", v[0][0])
        self.assertEqual(v[0][1], "app.py")

    def test_new_app_post_flagged(self):
        d = _diff("app.py", ['@app.post("/x")'])
        v = scan_diff(d)
        self.assertEqual(len(v), 1)
        self.assertIn("#17", v[0][0])

    def test_router_decorator_in_routes_module_ok(self):
        # 路由落在 *_routes.py 用 @router.get → 合规 · 不拦
        d = _diff("foo_routes.py", ['@router.get("/x")'])
        self.assertEqual(scan_diff(d), [])

    def test_app_route_in_other_file_ok(self):
        # 只盯 app.py · 别处的 @app.get 不在本闸范围
        d = _diff("legacy_app.py", ['@app.get("/x")'])
        self.assertEqual(scan_diff(d), [])


class TestDiffMechanics(unittest.TestCase):
    def test_context_and_removed_lines_ignored(self):
        # 上下文行(空格前缀)和删除行(-)不算新增 → 不拦
        diff = (
            "diff --git a/db.py b/db.py\n"
            "--- a/db.py\n"
            "+++ b/db.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def ensure_existing(conn):\n"  # 上下文(本来就有)→ 不拦
            "-def ensure_removed(conn):\n"  # 删除 → 不拦
            "+def ensure_added(conn):\n"  # 新增 → 拦
        )
        v = scan_diff(diff)
        self.assertEqual(len(v), 1)
        self.assertIn("ensure_added", v[0][2])

    def test_file_header_plusplusplus_not_treated_as_addition(self):
        # `+++ b/db.py` 文件头不能被误判为新增行
        d = _diff("db.py", ["def get_x():"])
        self.assertEqual(scan_diff(d), [])

    def test_deleted_file_dev_null_no_crash(self):
        diff = (
            "diff --git a/db.py b/db.py\n"
            "--- a/db.py\n"
            "+++ /dev/null\n"
            "@@ -1,1 +0,0 @@\n"
            "-def ensure_gone(conn):\n"
        )
        self.assertEqual(scan_diff(diff), [])

    def test_empty_diff_ok(self):
        self.assertEqual(scan_diff(""), [])


if __name__ == "__main__":
    unittest.main()

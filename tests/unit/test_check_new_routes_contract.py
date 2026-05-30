#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_new_routes_contract 纯函数单测(REFACTOR-WC)
==================================================
验证新增 *_routes.py 缺配套契约测试的检测逻辑 · 无 git 依赖。
"""

import importlib.util
import unittest
from pathlib import Path

_MOD = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_new_routes_contract.py"
_spec = importlib.util.spec_from_file_location("check_new_routes_contract", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
scan = mod.scan
expected_test_names = mod.expected_test_names


class TestExpectedNames(unittest.TestCase):
    def test_derives_three_acceptable_names(self):
        names = expected_test_names("foo_routes")
        self.assertIn("test_foo_routes_contract.py", names)
        self.assertIn("test_foo_contract.py", names)
        self.assertIn("test_foo_routes.py", names)


class TestScan(unittest.TestCase):
    def test_new_route_without_test_flagged(self):
        v = scan(["billing_routes.py"], known_tests=set())
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0][0], "billing_routes.py")

    def test_new_route_with_routes_contract_ok(self):
        v = scan(["billing_routes.py"], known_tests={"test_billing_routes_contract.py"})
        self.assertEqual(v, [])

    def test_new_route_with_short_contract_ok(self):
        v = scan(["billing_routes.py"], known_tests={"test_billing_contract.py"})
        self.assertEqual(v, [])

    def test_new_route_with_plain_routes_test_ok(self):
        v = scan(["admin_users_routes.py"], known_tests={"test_admin_users_routes.py"})
        self.assertEqual(v, [])

    def test_nested_path_route_uses_basename(self):
        v = scan(["sub/dir/foo_routes.py"], known_tests={"test_foo_routes_contract.py"})
        self.assertEqual(v, [])

    def test_non_routes_file_ignored(self):
        v = scan(["billing_store.py", "app.py"], known_tests=set())
        self.assertEqual(v, [])

    def test_multiple_routes_partial_coverage(self):
        v = scan(
            ["a_routes.py", "b_routes.py"],
            known_tests={"test_a_contract.py"},  # only a covered
        )
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0][0], "b_routes.py")

    def test_empty_input_ok(self):
        self.assertEqual(scan([], set()), [])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_tracked_imports 纯函数单测 · 复现 2026-06-11 未跟踪 import 部署崩事故。

纯函数注入"工作树存在集"和"HEAD 跟踪集",不依赖 git/文件系统。
"""

import importlib.util
import unittest
from pathlib import Path

_MOD_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_tracked_imports.py"
_spec = importlib.util.spec_from_file_location("check_tracked_imports", _MOD_PATH)
cti = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cti)


def _exists(present):
    return lambda rel: rel in present


class TestExtractImports(unittest.TestCase):
    def test_collects_import_and_from(self):
        src = "import os\nimport routes.x\nfrom services.a.b import c\n"
        self.assertEqual(cti.extract_imports(src), ["os", "routes.x", "services.a.b"])

    def test_skips_relative_imports(self):
        # 相对 import 不跨模块边界 · 不参与跟踪判定
        src = "from . import sibling\nfrom ..pkg import thing\n"
        self.assertEqual(cti.extract_imports(src), [])


class TestResolveLocalModule(unittest.TestCase):
    def test_resolves_module_file(self):
        present = {"routes/accounting_bank_routes.py"}
        self.assertEqual(
            cti.resolve_local_module("routes.accounting_bank_routes", _exists(present)),
            "routes/accounting_bank_routes.py",
        )

    def test_resolves_package_init(self):
        present = {"services/__init__.py"}
        self.assertEqual(
            cti.resolve_local_module("services", _exists(present)),
            "services/__init__.py",
        )

    def test_third_party_returns_none(self):
        # 项目里没有 fastapi/__init__.py · 不是本地模块
        self.assertIsNone(cti.resolve_local_module("fastapi", _exists(set())))


class TestFindUntrackedImports(unittest.TestCase):
    def test_flags_untracked_local_import(self):
        # 事故复现:app.py import 的 router 文件工作树存在但 HEAD 没有
        src = "from routes.accounting_bank_routes import router\n"
        present = {"routes/accounting_bank_routes.py", "routes/__init__.py"}
        tracked = {"routes/__init__.py"}  # router 文件未 git add
        bad = cti.find_untracked_imports(src, _exists(present), tracked)
        self.assertEqual(
            bad, [("routes.accounting_bank_routes", "routes/accounting_bank_routes.py")]
        )

    def test_tracked_import_passes(self):
        src = "from routes.accounting_bank_routes import router\n"
        present = {"routes/accounting_bank_routes.py"}
        tracked = {"routes/accounting_bank_routes.py"}
        self.assertEqual(cti.find_untracked_imports(src, _exists(present), tracked), [])

    def test_third_party_ignored(self):
        src = "import fastapi\nfrom psycopg2 import connect\n"
        self.assertEqual(cti.find_untracked_imports(src, _exists(set()), set()), [])


if __name__ == "__main__":
    unittest.main()

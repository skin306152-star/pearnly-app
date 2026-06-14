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
        # from pkg import name 既产出 pkg 也产出 pkg.name(覆盖"从已跟踪包 import 未跟踪子模块")
        src = "import os\nimport routes.x\nfrom services.a.b import c\n"
        self.assertEqual(
            cti.extract_imports(src), ["os", "routes.x", "services.a.b", "services.a.b.c"]
        )

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

    def test_flags_from_tracked_pkg_import_untracked_submodule(self):
        # 盲区修复:from 已跟踪包 import 未跟踪子模块文件(prod ModuleNotFoundError)
        src = "from services.purchase import drive\n"
        present = {"services/purchase/__init__.py", "services/purchase/drive.py"}
        tracked = {"services/purchase/__init__.py"}  # drive.py 未 git add
        bad = cti.find_untracked_imports(src, _exists(present), tracked)
        self.assertEqual(bad, [("services.purchase.drive", "services/purchase/drive.py")])

    def test_from_pkg_import_symbol_not_flagged(self):
        # name 是符号(函数/类)而非子模块文件 → pkg.name 在项目无对应文件 → 零误报
        src = "from services.purchase.totals import compute_purchase_totals\n"
        present = {"services/purchase/totals.py"}
        tracked = {"services/purchase/totals.py"}
        self.assertEqual(cti.find_untracked_imports(src, _exists(present), tracked), [])


class RelativeBaseTests(unittest.TestCase):
    def test_level1_is_current_package(self):
        self.assertEqual(cti._relative_base("services/ocr/page_runner.py", 1), ["services", "ocr"])

    def test_level2_is_parent_package(self):
        self.assertEqual(cti._relative_base("services/ocr/page_runner.py", 2), ["services"])

    def test_level3_reaches_root(self):
        self.assertEqual(cti._relative_base("services/ocr/page_runner.py", 3), [])

    def test_above_root_returns_none(self):
        self.assertIsNone(cti._relative_base("services/ocr/page_runner.py", 4))


class RelativeTargetsTests(unittest.TestCase):
    def test_from_dot_import_sibling(self):
        src = "from . import image_first\n"
        targets = cti._relative_targets(src, "services/ocr/page_runner.py")
        self.assertIn("services/ocr/image_first", [s for s, _ in targets])

    def test_from_dot_module_import_name(self):
        src = "from .drive import upload\n"
        stems = [s for s, _ in cti._relative_targets(src, "services/export/jobs.py")]
        # 既产出 drive 模块文件,也产出 drive/upload 子模块候选
        self.assertIn("services/export/drive", stems)
        self.assertIn("services/export/drive/upload", stems)


class FindUntrackedRelativeImportsTests(unittest.TestCase):
    def test_flags_untracked_relative_sibling(self):
        # 盲区修复:from . import 未跟踪兄弟模块(services/ 层盛行,prod 会崩)
        src = "from . import image_first\n"
        present = {"services/ocr/__init__.py", "services/ocr/image_first.py"}
        tracked = {"services/ocr/__init__.py"}  # image_first.py 未 git add
        bad = cti.find_untracked_imports(
            src, _exists(present), tracked, rel_path="services/ocr/page_runner.py"
        )
        self.assertEqual(bad, [("from . import image_first", "services/ocr/image_first.py")])

    def test_flags_untracked_relative_submodule(self):
        src = "from .drive import upload_tree\n"
        present = {"services/export/__init__.py", "services/export/drive.py"}
        tracked = {"services/export/__init__.py"}  # drive.py 未 git add
        bad = cti.find_untracked_imports(
            src, _exists(present), tracked, rel_path="services/export/jobs.py"
        )
        self.assertEqual(bad, [("from .drive", "services/export/drive.py")])

    def test_tracked_relative_sibling_passes(self):
        src = "from . import image_first\n"
        present = {"services/ocr/image_first.py"}
        tracked = {"services/ocr/image_first.py"}
        bad = cti.find_untracked_imports(
            src, _exists(present), tracked, rel_path="services/ocr/page_runner.py"
        )
        self.assertEqual(bad, [])

    def test_relative_symbol_not_flagged(self):
        # from .totals import compute(符号)→ totals/compute 无文件 → 零误报
        src = "from .totals import compute_purchase_totals\n"
        present = {"services/purchase/totals.py"}
        tracked = {"services/purchase/totals.py"}
        bad = cti.find_untracked_imports(
            src, _exists(present), tracked, rel_path="services/purchase/docs.py"
        )
        self.assertEqual(bad, [])

    def test_no_rel_path_skips_relative(self):
        # 不给 rel_path(向后兼容)→ 相对 import 不解析(同旧行为)
        src = "from . import image_first\n"
        present = {"services/ocr/image_first.py"}
        bad = cti.find_untracked_imports(src, _exists(present), set())
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()

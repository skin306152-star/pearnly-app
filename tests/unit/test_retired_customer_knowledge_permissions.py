# -*- coding: utf-8 -*-
"""客户知识与通用权限管理下线守门；ERP 团队管理不在删除范围。"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class RetiredFeatureFilesTests(unittest.TestCase):
    def test_customer_knowledge_runtime_files_are_deleted(self):
        retired = (
            "routes/knowledge_routes.py",
            "routes/knowledge_ask_routes.py",
            "src/home/page-knowledge.ts",
            "src/home/knowledge-center.ts",
        )
        for path in retired:
            self.assertFalse((ROOT / path).exists(), path)
        self.assertFalse(list((ROOT / "services/knowledge").rglob("*.*")))

    def test_general_permissions_console_files_are_deleted(self):
        retired = (
            "routes/console_team_routes.py",
            "routes/console_invite_routes.py",
            "routes/console_roles_routes.py",
            "services/team/console_store.py",
            "services/team/invitations.py",
            "static/dist/console.html",
            "static/dist/invite.html",
        )
        for path in retired:
            self.assertFalse((ROOT / path).exists(), path)
        self.assertFalse(list((ROOT / "static/console").rglob("*.*")))


class FrontendEntryTests(unittest.TestCase):
    def test_retired_nodes_are_absent_from_source_and_build(self):
        for path in (
            "src/home/app-shell-sidebar-html.ts",
            "src/home/app-shell-html.ts",
            "home.html",
            "static/dist/home.html",
        ):
            source = read(path)
            self.assertNotIn("nav-knowledge", source, path)
            self.assertNotIn("page-knowledge", source, path)
            self.assertNotIn("avatar-menu-console", source, path)

    def test_erp_team_source_and_built_entry_remain(self):
        self.assertTrue((ROOT / "routes/erp_team_routes.py").is_file())
        self.assertTrue((ROOT / "services/erp/team_access.py").is_file())
        self.assertTrue((ROOT / "services/erp/team_members.py").is_file())
        self.assertIn("nav-erp-team", read("src/home/app-shell-sidebar-html.ts"))
        self.assertIn("page-erp-team", read("static/dist/home.html"))
        self.assertIn("/api/erp/team/access", read("static/dist/main.js"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「应收追踪」(receivables 占位页)防回潮钉。

历史上该 coming-soon 占位靠 data-module 隐藏,导航改版复位子项 display 时反复借尸还魂,
2026-07-10 拍板物理删除(EN-9)。本测试钉死删除面:侧栏/路由表/cmdk/占位页/home.html/i18n
任何一处再冒出 receivables 路由或其 i18n 键即红。注意 receivable【模块】(b2b 业态开关、
mod.receivable 等文案)是另一套活体系,不在钉死范围。
"""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 曾承载过 receivables 占位的前端骨架文件(全部不得再出现 receivables 路由字样)
SHELL_FILES = [
    "src/home/app-shell-sidebar-html.ts",
    "src/home/cmdk-mask-html.ts",
    "src/home/page-placeholders.ts",
    "src/home/route-table.ts",
    "src/home/sidebar-nav-group.ts",
    "home.html",
]


class ReceivablesRemovedTests(unittest.TestCase):
    def test_shell_files_have_no_receivables(self):
        for rel in SHELL_FILES:
            text = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("receivables", text, msg=f"{rel} 里 receivables 又诈尸了")
            self.assertNotIn("page-receivables", text, msg=f"{rel} 里 page-receivables 又诈尸了")

    def test_i18n_keys_deleted_all_langs(self):
        text = (PROJECT_ROOT / "static/i18n-data.js").read_text(encoding="utf-8")
        self.assertNotIn("nav-receivables", text, msg="i18n 键 nav-receivables 又诈尸了")
        self.assertNotIn("cs-receivables-", text, msg="i18n 占位页键 cs-receivables-* 又诈尸了")

    def test_deep_link_fallback_intact(self):
        # 深链兜底:#/receivables 书签走 routeTo 的非法路由回落 → dms-intake,
        # 回落逻辑与回落目标都得在,书签用户不能白屏。
        routes = (PROJECT_ROOT / "src/home/route-table.ts").read_text(encoding="utf-8")
        self.assertIn("'dms-intake'", routes)
        boot = (PROJECT_ROOT / "src/home/core-boot.ts").read_text(encoding="utf-8")
        self.assertIn("if (!VALID_ROUTES.includes(route)) route = 'dms-intake';", boot)


if __name__ == "__main__":
    unittest.main()

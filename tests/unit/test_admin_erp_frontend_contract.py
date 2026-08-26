# -*- coding: utf-8 -*-
"""Earn 超管 · ERP 邀请前端契约(2026-08-27 · 照 DMS/AI 邀请页范式)。

后端 /api/admin/erp/{overview,invite,revoke} 契约已在 test_admin_erp_routes_contract 钉死;
本文件锁前端入口(admin SPA)确实接线:侧栏 page-admin-erp + 路由 erp + adm-erp-* 词表,
且只做 列表/邀请/撤销 —— 绝不新增「重置密码」入口(不把砍掉的通用改密能力开回来)。
"""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class AdminErpFrontendContractTests(unittest.TestCase):
    def test_admin_html_declares_erp_page_and_sidebar(self):
        text = _read("static/admin/admin.html")
        self.assertIn('id="page-admin-erp"', text)
        self.assertIn('data-admin-route="erp"', text)
        self.assertIn('href="/admin/erp"', text)
        self.assertIn('data-i18n="adm-sidebar-erp"', text)

    def test_admin_js_routes_erp_page(self):
        text = _read("static/admin/admin.js")
        self.assertIn("p === '/admin/erp' || p === '/admin/erp/'", text)
        self.assertIn("_renderErpPage", text)
        self.assertIn("'/api/admin/erp/overview'", text)
        self.assertIn("'/api/admin/erp/invite'", text)
        self.assertIn("'/api/admin/erp/revoke'", text)

    def test_erp_page_is_invite_only_without_reset(self):
        # ERP 邀请只做 列表/邀请/撤销,不复制 DMS 的重置密码:无 reset 端点/按钮/词表。
        js = _read("static/admin/admin.js")
        self.assertNotIn("/api/admin/erp/reset-password", js)
        self.assertNotIn("data-adm-erp-reset", js)
        html = _read("static/admin/admin.html")
        self.assertNotIn('data-i18n="adm-erp-reset', html)

    def test_admin_i18n_declares_erp_keys_both_langs(self):
        text = _read("static/admin/admin-i18n.js")
        # zh + th 两语言块都要有 ERP 邀请词表(与 DMS 同构)。
        self.assertGreaterEqual(text.count("'adm-sidebar-erp'"), 2)
        self.assertGreaterEqual(text.count("'adm-erp-title'"), 2)
        self.assertGreaterEqual(text.count("'adm-erp-invite-btn'"), 2)
        self.assertGreaterEqual(text.count("'adm-erp-revoke-btn'"), 2)


if __name__ == "__main__":
    unittest.main()

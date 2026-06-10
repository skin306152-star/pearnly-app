# -*- coding: utf-8 -*-
"""报税路由契约闸(docs/tax-filing/03):路由集合 / 信封 / 逐路由权限码 / 模块门控+套账解析。"""

import inspect
import unittest

import routes.tax_routes as mod
from routes.tax_routes import router

EXPECTED = {
    ("GET", "/api/tax/filings"),
    ("POST", "/api/tax/filings/generate"),
    ("GET", "/api/tax/filings/{filing_id}"),
    ("POST", "/api/tax/filings/{filing_id}/recompute"),
    ("POST", "/api/tax/filings/{filing_id}/check"),
    ("POST", "/api/tax/filings/{filing_id}/file"),
    ("POST", "/api/tax/filings/{filing_id}/mark-filed"),
    ("GET", "/api/tax/filings/{filing_id}/export"),
    ("POST", "/api/tax/wht-certs/{line_id}/issue"),
    ("GET", "/api/tax/settings"),
    ("PUT", "/api/tax/settings"),
}

# docs/permissions/02 矩阵:读=view · 生成/重算/凭证=create · 提交(不可逆)=approve · 设置写=manage
GATE_CODES = {
    "api_list_filings": "tax.filing.view",
    "api_generate_filings": "tax.filing.create",
    "api_get_filing": "tax.filing.view",
    "api_recompute_filing": "tax.filing.create",
    "api_check_filing": "tax.filing.view",
    "api_file_filing": "tax.filing.approve",
    "api_mark_filed": "tax.filing.approve",
    "api_export_filing": "tax.filing.view",
    "api_issue_wht_cert": "tax.filing.create",
    "api_get_settings": "tax.filing.view",
    "api_update_settings": "tax.settings.manage",
}


class TaxRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_uses_pos_envelope(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "PosError"))

    def test_every_handler_pins_perm_code(self):
        for name, code in GATE_CODES.items():
            fn = getattr(mod, name)
            self.assertIn(f'_auth(request, "{code}")', inspect.getsource(fn), f"{name} 没钉 {code}")

    def test_gate_codes_cover_all_router_handlers(self):
        handlers = {r.endpoint.__name__ for r in router.routes if hasattr(r, "endpoint")}
        self.assertEqual(handlers, set(GATE_CODES))

    def test_every_handler_gates_module_and_workspace(self):
        for name in GATE_CODES:
            fn = getattr(mod, name)
            self.assertIn("_gate", fn.__code__.co_names, f"{name} 缺模块门控")
            self.assertIn("_resolve_ws", fn.__code__.co_names, f"{name} 缺套账解析")

    def test_tax_codes_registered(self):
        from services.authz.registry import ALL_CODES

        for code in set(GATE_CODES.values()):
            self.assertIn(code, ALL_CODES, f"{code} 不在权限 registry")

    def test_helpers_use_tax_error_namespace(self):
        src = inspect.getsource(mod)
        self.assertIn('"accounting"', src)  # 模块门控 = accounting(报税吃账本)
        self.assertIn("tax.forbidden", src)
        self.assertIn("workspace.required", src)

    def test_close_period_hooks_tax_generation(self):
        # seam 闸:结账路由必须挂报税生成(docs/tax-filing/04)
        import routes.accounting_books_routes as books_routes

        src = inspect.getsource(books_routes.api_close_period)
        self.assertIn("tax_hooks.enqueue_generate", src)


if __name__ == "__main__":
    unittest.main()

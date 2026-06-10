# -*- coding: utf-8 -*-
"""做账路由契约闸(docs/accounting/03 · 批2:权限码接线):路由集合 / 信封 / 逐路由带码 / 模块门控。"""

import inspect
import unittest

import routes.accounting_routes as mod
from routes.accounting_routes import router

EXPECTED = {
    ("GET", "/api/accounting/vouchers"),
    ("GET", "/api/accounting/vouchers/{voucher_id}"),
    ("POST", "/api/accounting/vouchers/manual"),
    ("POST", "/api/accounting/vouchers/{voucher_id}/review"),
    ("PATCH", "/api/accounting/vouchers/{voucher_id}"),
    ("POST", "/api/accounting/vouchers/{voucher_id}/void"),
    ("POST", "/api/accounting/vouchers/{voucher_id}/unpost"),
    ("GET", "/api/accounting/review"),
    ("GET", "/api/accounting/accounts"),
    ("POST", "/api/accounting/accounts"),
    ("PATCH", "/api/accounting/accounts/{account_id}"),
    ("GET", "/api/accounting/mappings"),
    ("PUT", "/api/accounting/mappings"),
    ("GET", "/api/accounting/settings"),
    ("PUT", "/api/accounting/settings"),
    ("GET", "/api/accounting/learned"),
    ("DELETE", "/api/accounting/learned/{learned_id}"),
}

# 批2:逐路由权限码(docs/permissions/02 矩阵接线 · 写档分 review/approve/coa/settings,读=view)
GATE_CODES = {
    "api_list_vouchers": "acct.entry.view",
    "api_get_voucher": "acct.entry.view",
    "api_manual_voucher": "acct.entry.review",
    "api_review_voucher": "acct.entry.review",
    "api_patch_voucher": "acct.entry.review",
    "api_void_voucher": "acct.entry.approve",
    "api_unpost_voucher": "acct.entry.approve",
    "api_review_queue": "acct.entry.review",
    "api_list_accounts": "acct.entry.view",
    "api_create_account": "acct.coa.manage",
    "api_update_account": "acct.coa.manage",
    "api_list_mappings": "acct.entry.view",
    "api_set_mapping": "acct.coa.manage",
    "api_get_settings": "acct.entry.view",
    "api_update_settings": "acct.settings.manage",
    "api_list_learned": "acct.entry.view",
    "api_delete_learned": "acct.coa.manage",
}


class AccountingRoutesContractTests(unittest.TestCase):
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
            self.assertIn(
                f'auth_member(request, "{code}")', inspect.getsource(fn), f"{name} 没钉 {code}"
            )

    def test_gate_codes_cover_all_router_handlers(self):
        # 防新增路由漏进矩阵:GATE_CODES 键集 = router 全部 handler
        handlers = {r.endpoint.__name__ for r in router.routes if hasattr(r, "endpoint")}
        self.assertEqual(handlers, set(GATE_CODES))

    def test_every_handler_gates_module_and_workspace(self):
        for name in GATE_CODES:
            fn = getattr(mod, name)
            self.assertIn("gate", fn.__code__.co_names, f"{name} 缺模块门控")
            self.assertIn("resolve_ws", fn.__code__.co_names, f"{name} 缺套账解析")

    def test_common_helpers_gate_accounting_with_acct_codes(self):
        import inspect

        import routes.accounting_common as common

        src = inspect.getsource(common)
        self.assertIn('"accounting"', src)
        self.assertIn("acct.forbidden", src)
        self.assertIn("workspace.required", src)

    def test_accounting_module_registered(self):
        from services.modules.presets import BUSINESS_PRESETS
        from services.modules.store import DEFAULT_ENABLED, KNOWN_MODULES

        self.assertIn("accounting", KNOWN_MODULES)
        self.assertFalse(DEFAULT_ENABLED["accounting"])
        for business_type, keys in BUSINESS_PRESETS.items():
            self.assertIn("accounting", keys, f"{business_type} 预设缺 accounting")


if __name__ == "__main__":
    unittest.main()

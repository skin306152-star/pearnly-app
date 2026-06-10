# -*- coding: utf-8 -*-
"""做账路由契约闸(docs/accounting/03):路由集合 / 信封 / 权限接线 / 模块门控。"""

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

# 写接口 = 账号 owner 专属(员工只看 · docs/accounting/04 §六)
_OWNER_HANDLERS = (
    "api_manual_voucher",
    "api_review_voucher",
    "api_patch_voucher",
    "api_void_voucher",
    "api_unpost_voucher",
    "api_create_account",
    "api_update_account",
    "api_set_mapping",
    "api_update_settings",
    "api_delete_learned",
)
_MEMBER_HANDLERS = (
    "api_list_vouchers",
    "api_get_voucher",
    "api_review_queue",
    "api_list_accounts",
    "api_list_mappings",
    "api_get_settings",
    "api_list_learned",
)


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

    def test_write_handlers_gate_on_owner(self):
        for name in _OWNER_HANDLERS:
            fn = getattr(mod, name)
            self.assertIn("auth_owner", fn.__code__.co_names, f"{name} 没走 auth_owner")

    def test_read_handlers_allow_members(self):
        for name in _MEMBER_HANDLERS:
            fn = getattr(mod, name)
            self.assertIn("auth_member", fn.__code__.co_names, f"{name} 没走 auth_member")
            self.assertNotIn("auth_owner", fn.__code__.co_names, f"{name} 误锁 owner")

    def test_every_handler_gates_module_and_workspace(self):
        for name in _OWNER_HANDLERS + _MEMBER_HANDLERS:
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

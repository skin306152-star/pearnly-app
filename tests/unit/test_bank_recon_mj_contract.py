# -*- coding: utf-8 -*-
"""银行对账路由契约闸(docs/accounting/bank-recon-mj/04 §3):路由集合 / 逐路由权限码 / 信封 /
模块门控 + 套账解析 / schema 三表 + RLS 登记。"""

import inspect
import unittest

import routes.accounting_bank_routes as mod
from routes.accounting_bank_routes import router

EXPECTED = {
    ("GET", "/api/accounting/bank/accounts"),
    ("POST", "/api/accounting/bank/accounts"),
    ("POST", "/api/accounting/bank/import"),
    ("GET", "/api/accounting/bank/summary"),
    ("GET", "/api/accounting/bank/lines"),
    ("GET", "/api/accounting/bank/lines/{line_id}/candidates"),
    ("POST", "/api/accounting/bank/lines/{line_id}/match"),
    ("POST", "/api/accounting/bank/lines/{line_id}/unmatch"),
    ("POST", "/api/accounting/bank/lines/{line_id}/exclude"),
    ("POST", "/api/accounting/bank/lines/{line_id}/restore"),
    ("POST", "/api/accounting/bank/harvest"),
}

# 01 审计:复用 acct 六码不新增。读=view,导入/匹配/收割=review,撤销=approve,登记账户=settings.manage
GATE_CODES = {
    "api_bank_accounts": "acct.entry.view",
    "api_create_bank_account": "acct.settings.manage",
    "api_bank_import": "acct.entry.review",
    "api_bank_summary": "acct.entry.view",
    "api_bank_lines": "acct.entry.view",
    "api_bank_candidates": "acct.entry.review",
    "api_bank_match": "acct.entry.review",
    "api_bank_unmatch": "acct.entry.approve",
    "api_bank_exclude": "acct.entry.review",
    "api_bank_restore": "acct.entry.review",
    "api_bank_harvest": "acct.entry.review",
}


class BankReconRoutesContractTests(unittest.TestCase):
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
        handlers = {r.endpoint.__name__ for r in router.routes if hasattr(r, "endpoint")}
        self.assertEqual(handlers, set(GATE_CODES))

    def test_every_handler_gates_module_and_workspace(self):
        for name in GATE_CODES:
            fn = getattr(mod, name)
            self.assertIn("gate", fn.__code__.co_names, f"{name} 缺模块门控")
            self.assertIn("resolve_ws", fn.__code__.co_names, f"{name} 缺套账解析")


class BankReconSchemaTests(unittest.TestCase):
    def test_three_new_tables_and_indexes_present(self):
        from services.accounting import schema

        ddl = " ".join(schema._TABLES)
        for tbl in ("acct_bank_accounts", "acct_bank_lines", "acct_voucher_templates"):
            self.assertIn(tbl, ddl, f"缺表 {tbl}")
            self.assertIn(tbl, schema._RLS_TABLES, f"{tbl} 未登记 RLS")
        idx = " ".join(schema._INDEXES)
        self.assertIn("uq_bank_line_dedup", idx)
        self.assertIn("ix_bank_lines_status", idx)

    def test_bank_lines_dual_isolation_columns(self):
        from services.accounting import schema

        lines_ddl = next(t for t in schema._TABLES if "acct_bank_lines" in t)
        self.assertIn("tenant_id", lines_ddl)
        self.assertIn("workspace_client_id", lines_ddl)
        self.assertIn("ON DELETE CASCADE", lines_ddl)  # FK → acct_bank_accounts


if __name__ == "__main__":
    unittest.main()

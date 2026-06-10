# -*- coding: utf-8 -*-
"""出账本路由契约闸(docs/accounting/03 §5):路由集合 / 信封 / 权限分档 / PDF 渲染冒烟。"""

import unittest
from datetime import date
from decimal import Decimal

import routes.accounting_books_routes as mod
from routes.accounting_books_routes import router

EXPECTED = {
    ("GET", "/api/accounting/books"),
    ("GET", "/api/accounting/tax-reports"),
    ("GET", "/api/accounting/financials"),
    ("POST", "/api/accounting/close-period"),
    ("GET", "/api/accounting/export-package"),
}


class BooksRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_uses_pos_envelope(self):
        self.assertTrue(hasattr(mod, "ok"))
        self.assertTrue(hasattr(mod, "PosError"))

    def test_close_period_gates_on_approve_permission(self):
        fn = mod.api_close_period
        self.assertIn("auth_owner", fn.__code__.co_names)
        self.assertIn("acct.entry.approve", fn.__code__.co_consts)

    def test_export_package_requires_export_permission(self):
        fn = mod.api_export_package
        self.assertIn("acct.ledger.export", fn.__code__.co_consts)

    def test_pdf_downloads_escalate_to_export_permission(self):
        for name in ("api_books", "api_tax_reports", "api_financials"):
            fn = getattr(mod, name)
            self.assertIn("acct.ledger.export", fn.__code__.co_consts, f"{name} PDF 档没升 export")
            self.assertIn("acct.entry.view", fn.__code__.co_consts, f"{name} 预览档没用 view")

    def test_shared_report_path_gates_module_and_workspace(self):
        fn = mod._report
        for needed in ("auth_member", "gate", "resolve_ws"):
            self.assertIn(needed, fn.__code__.co_names, f"_report 缺 {needed}")

    def test_bad_kind_rejected(self):
        self.assertIsNone(mod._BOOK_FN.get("nope"))
        self.assertIsNone(mod._TAX_FN.get("nope"))
        self.assertEqual(set(mod._BOOK_FN), {"gl", "subsidiary", "trial_balance"})
        self.assertEqual(set(mod._TAX_FN), {"vat", "wht"})


class BooksPdfSmokeTests(unittest.TestCase):
    def test_trial_balance_pdf_renders(self):
        from services.accounting import books_pdf

        payload = {
            "period": "2026-06",
            "rows": [
                {
                    "code": "1010",
                    "name_zh": "现金",
                    "name_th": "เงินสด",
                    "debit": Decimal("107"),
                    "credit": Decimal("0"),
                }
            ],
            "totals": {"debit": Decimal("107"), "credit": Decimal("107")},
            "balanced": True,
        }
        pdf = books_pdf.render("trial_balance", payload, lang="en")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_vat_pdf_renders_with_sections(self):
        from services.accounting import books_pdf

        row = {
            "voucher_no": "JV1",
            "date": date(2026, 6, 2),
            "source_type": "sale",
            "ref": "INV-1",
            "description": "ขายสินค้า",
            "amount": Decimal("70"),
        }
        payload = {
            "period": "2026-06",
            "sales": {"rows": [row], "total": Decimal("70")},
            "purchase": {"rows": [], "total": Decimal("0")},
            "vat_payable": Decimal("70"),
        }
        pdf = books_pdf.render("vat", payload, lang="th")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_export_package_zips_every_kind(self):
        import io
        import zipfile
        from unittest import mock

        from services.accounting import books_pdf

        payloads = {k: {"period": "2026-06"} for k in ("gl", "trial_balance", "vat")}
        with mock.patch.object(books_pdf, "render", return_value=b"%PDF-fake"):
            data = books_pdf.export_package(payloads, period="2026-06")
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            self.assertEqual(
                sorted(zf.namelist()),
                ["gl_2026-06.pdf", "trial_balance_2026-06.pdf", "vat_2026-06.pdf"],
            )

    def test_unknown_kind_raises(self):
        from services.accounting import books_pdf

        with self.assertRaises(ValueError):
            books_pdf.render("nope", {"period": "2026-06"})

# -*- coding: utf-8 -*-
"""报税路由契约闸(docs/tax-filing/03):路由集合 / 信封 / 逐路由权限码 / 模块门控+套账解析
+ 导出分发诚实(EXPORT_FORMATS 每成员专属分支,不掉 zip 兜底)。"""

import inspect
import json
import unittest
from datetime import date
from decimal import Decimal

import routes.tax_routes as mod
from core.pos_api import PosError
from routes.tax_routes import router
from services.tax import efiling

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


def _pnd_filing(kind="pnd53", lines=None):
    return {
        "kind": kind,
        "period": "2026-07",
        "status": "prepared",
        "net_amount": Decimal("30"),
        "breakdown": {"wht_total": "30"},
        "anomalies": [],
        "due_date": date(2026, 8, 15),
        "lines": list(
            lines
            if lines is not None
            else [
                {
                    "payee_name": "ผู้รับ",
                    "payee_tax_id": "0105536000011",
                    "payee_type": "juristic",
                    "income_type": "service",
                    "base_amount": Decimal("1000"),
                    "wht_rate": Decimal("3"),
                    "wht_amount": Decimal("30"),
                    "source_purchase_id": "doc-1",
                    "cert_url": None,
                    "cert_status": "generated",
                }
            ]
        ),
    }


_TAXPAYER = {"tax_id": "0105551234567", "branch_no": "000000"}


class ExportDispatchTests(unittest.TestCase):
    """EXPORT_FORMATS 每个成员走 _export_payload 都得到专属格式——验参放行的 fmt 掉进
    zip 兜底返回错误格式 = 假成功(主窗打回项),此闸防回潮。"""

    def _dispatch(self, fmt, filing=None):
        return mod._export_payload(filing or _pnd_filing(), fmt, lang="th", taxpayer=_TAXPAYER)

    def test_every_export_format_gets_own_media_type(self):
        expected_media = {
            "pdf": "application/pdf",
            "xml": "application/xml",
            "zip": "application/zip",
            "rdprep": "text/plain; charset=utf-8",
        }
        self.assertEqual(set(expected_media), set(efiling.EXPORT_FORMATS))
        for fmt, media in expected_media.items():
            _, got_media, filename, _ = self._dispatch(fmt)
            self.assertEqual(got_media, media, f"fmt={fmt} 分发到了错的格式")
            self.assertTrue(filename, f"fmt={fmt} 缺文件名")

    def test_rdprep_returns_txt_content_and_filename(self):
        content, media, filename, headers = self._dispatch("rdprep")
        self.assertEqual(media, "text/plain; charset=utf-8")
        self.assertEqual(filename, "PND53_0105551234567_000000_2569_07_00_00.txt")
        text = content.decode("utf-8")
        self.assertTrue(text.startswith("H|"))
        self.assertIn("\r\nD|", text)
        self.assertEqual(headers["X-Rdprep-Excluded-Count"], "0")
        self.assertNotIn("X-Rdprep-Excluded", headers)

    def test_rdprep_excluded_lines_reported_in_header(self):
        no_address = {
            "payee_name": "ไม่มีที่อยู่",
            "payee_tax_id": "1234567890123",
            "payee_type": "individual",
            "income_type": "service",
            "base_amount": Decimal("100"),
            "wht_rate": Decimal("3"),
            "wht_amount": Decimal("3"),
            "source_purchase_id": "doc-2",
            "cert_url": None,
            "cert_status": "generated",
        }
        _, _, _, headers = self._dispatch("rdprep", _pnd_filing(kind="pnd3", lines=[no_address]))
        self.assertEqual(headers["X-Rdprep-Excluded-Count"], "1")
        excluded = json.loads(headers["X-Rdprep-Excluded"])
        self.assertEqual(excluded[0]["payee_tax_id"], "1234567890123")
        self.assertEqual(excluded[0]["reason"], "missing_address")
        # 泰文名经 \u 转义,header 值必须纯 ASCII 否则响应组装就炸
        headers["X-Rdprep-Excluded"].encode("ascii")

    def test_unknown_fmt_raises_not_falls_through(self):
        with self.assertRaises(PosError):
            self._dispatch("csv")


if __name__ == "__main__":
    unittest.main()

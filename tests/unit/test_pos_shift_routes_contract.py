# -*- coding: utf-8 -*-
"""POS 开/交班路由守门(PC-3 · 从 pos_sales 拆出 · docs/pos/04 §5)。

锁定:开/交班 path+method 契约 · app.py include · 审计走 pos_write after_commit(commit 后写、
不回滚交班)· 开班只认收银员 token。对账公式与连号在 services,路由只是薄信封。
"""

import inspect
import unittest

import routes.pos_shift_routes as mod
from routes.pos_shift_routes import router

EXPECTED = {
    ("POST", "/api/pos/shifts/open"),
    ("GET", "/api/pos/shifts/current"),
    ("POST", "/api/pos/shifts/{shift_id}/close"),
}


class PosShiftRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"pos-shift route missing from app: {p}")

    def test_audit_wired_after_commit_not_inline(self):
        # 审计挂 after_commit(commit 后独立写、失败不回滚交班),不在写事务内。
        open_src = inspect.getsource(mod.api_open_shift)
        close_src = inspect.getsource(mod.api_close_shift)
        self.assertIn("after_commit=shift_audit.after_open", open_src)
        self.assertIn("after_commit=shift_audit.after_close", close_src)

    def test_open_shift_requires_cashier(self):
        self.assertIn("cashier_id", inspect.getsource(mod.api_open_shift))
        self.assertIn('PosError("pos.forbidden", 403)', inspect.getsource(mod.api_open_shift))


if __name__ == "__main__":
    unittest.main()

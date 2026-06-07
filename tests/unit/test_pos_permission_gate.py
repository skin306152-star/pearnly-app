# -*- coding: utf-8 -*-
"""POS 越权守门测试(POS 项目 · 安全审计 · docs/pos/10 §5.1)。

收银员 token 只能干前台(卖货/班次);管理动作(开通收银、库存进货/盘点/调整、销售报表)
必须老板/会计。本测试锁 require_owner 的判定 + 库存写/报表路由确实接 require_owner(防回归)。"""

import unittest
from unittest import mock

from core import pos_api
from core.pos_api import PosError


class _Req:
    pass


class RequireOwnerTests(unittest.TestCase):
    def test_cashier_token_blocked_403(self):
        subject = {"tenant_id": "t", "id": "c", "role": "cashier", "is_super_admin": False}
        with mock.patch.object(pos_api, "pos_auth", return_value=subject):
            with self.assertRaises(PosError) as ctx:
                pos_api.require_owner(_Req())
        self.assertEqual(ctx.exception.code, "pos.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_owner_allowed(self):
        subject = {"tenant_id": "t", "id": "u", "role": "owner", "is_super_admin": False}
        with mock.patch.object(pos_api, "pos_auth", return_value=subject):
            tid, uid = pos_api.require_owner(_Req())
        self.assertEqual((tid, uid), ("t", "u"))

    def test_super_admin_allowed_even_if_cashier_role(self):
        subject = {"tenant_id": "t", "id": "s", "role": "cashier", "is_super_admin": True}
        with mock.patch.object(pos_api, "pos_auth", return_value=subject):
            tid, _ = pos_api.require_owner(_Req())
        self.assertEqual(tid, "t")

    def test_no_tenant_forbidden(self):
        with mock.patch.object(pos_api, "pos_auth", return_value={"role": "owner"}):
            with self.assertRaises(PosError) as ctx:
                pos_api.require_owner(_Req())
        self.assertEqual(ctx.exception.http_status, 403)


class WiringTests(unittest.TestCase):
    """库存写端 + 报表路由接 require_owner(收银员 token 调=403);库存读端用 require_tenant。"""

    def test_inventory_write_uses_require_owner(self):
        import routes.inventory_routes as inv

        self.assertIn("require_owner", inv._write.__code__.co_names)
        self.assertIn("require_tenant", inv._read.__code__.co_names)

    def test_report_route_uses_require_owner(self):
        import routes.pos_report_routes as rep

        self.assertTrue(hasattr(rep, "require_owner"))

    def test_onboarding_uses_require_owner(self):
        import routes.pos_auth_routes as auth

        self.assertIn("require_owner", auth.api_onboarding.__code__.co_names)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""采购越权守门测试(docs/purchasing/02 §鉴权 · 同 POS test_pos_permission_gate)。

录入(建/列/详单据·intake)= 任意成员;配置(供应商/科目/设置写)+ 审付款 + 作废 + 凭据生成 +
删附件 = 账号 owner(invited_by is None)。锁 auth_owner 判定 + 路由接线(防回归把 owner 动作
降级成成员可调)。"""

import unittest
from unittest import mock

from core.pos_api import PosError
from routes import purchase_common as pc


class _Req:
    pass


class AuthOwnerTests(unittest.TestCase):
    def test_member_blocked_403(self):
        member = {"tenant_id": "t", "id": "m", "invited_by": "owner-x"}
        with mock.patch.object(pc, "pos_auth", return_value=member):
            with self.assertRaises(PosError) as ctx:
                pc.auth_owner(_Req())
        self.assertEqual(ctx.exception.code, "purchase.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_owner_allowed(self):
        owner = {"tenant_id": "t", "id": "u", "invited_by": None}
        with mock.patch.object(pc, "pos_auth", return_value=owner):
            user, tid = pc.auth_owner(_Req())
        self.assertEqual(tid, "t")
        self.assertEqual(user["id"], "u")

    def test_super_admin_allowed_even_if_invited(self):
        sa = {"tenant_id": "t", "id": "s", "invited_by": "x", "is_super_admin": True}
        with mock.patch.object(pc, "pos_auth", return_value=sa):
            _, tid = pc.auth_owner(_Req())
        self.assertEqual(tid, "t")

    def test_member_can_pass_member_gate(self):
        member = {"tenant_id": "t", "id": "m", "invited_by": "owner-x"}
        with mock.patch.object(pc, "pos_auth", return_value=member):
            user, tid = pc.auth_member(_Req())
        self.assertEqual((tid, user["id"]), ("t", "m"))

    def test_no_tenant_forbidden(self):
        with mock.patch.object(pc, "pos_auth", return_value={"id": "x"}):
            with self.assertRaises(PosError) as ctx:
                pc.auth_member(_Req())
        self.assertEqual(ctx.exception.http_status, 403)


class WiringTests(unittest.TestCase):
    """owner 动作接 auth_owner;录入接 auth_member(防降级)。"""

    def test_config_writes_owner_reads_member(self):
        import routes.purchase_config_routes as cfg

        for fn in (cfg.api_create_supplier, cfg.api_save_settings, cfg.api_delete_supplier):
            self.assertIn("auth_owner", fn.__code__.co_names, fn.__name__)
        for fn in (cfg.api_list_suppliers, cfg.api_get_settings, cfg.api_get_categories):
            self.assertIn("auth_member", fn.__code__.co_names, fn.__name__)

    def test_pay_void_owner_create_member(self):
        import routes.purchase_routes as pr

        for fn in (pr.api_pay_doc, pr.api_void_doc, pr.api_delete_attachment):
            self.assertIn("auth_owner", fn.__code__.co_names, fn.__name__)
        for fn in (pr.api_create_doc, pr.api_list_docs, pr.api_post_doc):
            self.assertIn("auth_member", fn.__code__.co_names, fn.__name__)

    def test_credential_gen_is_owner(self):
        import routes.purchase_routes as pr

        # 凭据生成共用 _gen_credential,内部走 auth_owner。
        self.assertIn("auth_owner", pr._gen_credential.__code__.co_names)

    def test_intake_is_member(self):
        import routes.purchase_intake_routes as ir

        self.assertIn("auth_member", ir.api_intake.__code__.co_names)
        self.assertIn("auth_member", ir.api_quick_expense.__code__.co_names)


if __name__ == "__main__":
    unittest.main()

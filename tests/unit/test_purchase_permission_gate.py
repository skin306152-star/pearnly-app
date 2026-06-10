# -*- coding: utf-8 -*-
"""采购越权守门测试(docs/permissions/03 · 批2:require_perm_pos 统一执行点)。

录入 = purchase.doc.create / intake.upload;审付款/作废/入账/凭据生成 = purchase.doc.approve;
供应商/科目写 = purchase.supplier.manage;设置写 = purchase.settings.manage;读 = purchase.doc.view。
锁 auth_member 经 resolver 码集判定 + 路由逐条带码接线(防回归把高敏动作降级)。"""

import contextlib
import inspect
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from core.pos_api import PosError
from routes import purchase_common as pc
from services.authz import deps
from services.authz.registry import ALL_CODES
from services.authz.resolver import Authz


class _Req:
    def __init__(self):
        self.headers = {}


def _grant(*codes) -> Authz:
    return Authz(role_key="test", permissions=frozenset(codes))


@contextlib.contextmanager
def _gate(user, authz=None, module_disabled=False):
    """统一执行点打桩:pos_auth 出主体 · resolver 出码集 · 模块开关可控。"""
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch("core.pos_api.pos_auth", return_value=user))
        st.enter_context(mock.patch.object(deps, "_pos_token_payload", return_value=None))
        st.enter_context(mock.patch.object(deps, "_module_disabled", return_value=module_disabled))
        st.enter_context(mock.patch.object(deps, "_cached_authz", return_value=authz or _grant()))
        yield


class AuthGateTests(unittest.TestCase):
    def test_member_without_approve_code_blocked_403(self):
        member = {"tenant_id": "t", "id": "m", "role": "member"}
        with _gate(member, _grant("purchase.doc.view", "purchase.doc.create")):
            with self.assertRaises(PosError) as ctx:
                pc.auth_member(_Req(), "purchase.doc.approve")
        self.assertEqual(ctx.exception.code, "purchase.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_full_codes_pass_owner_gate(self):
        owner = {"tenant_id": "t", "id": "u", "role": "owner"}
        with _gate(owner, _grant(*ALL_CODES)):
            user, tid = pc.auth_owner(_Req())
        self.assertEqual((tid, user["id"]), ("t", "u"))

    def test_super_admin_short_circuits_resolver(self):
        sa = {"tenant_id": "t", "id": "s", "is_super_admin": True}
        with mock.patch("core.pos_api.pos_auth", return_value=sa):
            _, tid = pc.auth_owner(_Req(), "purchase.doc.approve")
        self.assertEqual(tid, "t")

    def test_member_with_view_code_passes_member_gate(self):
        member = {"tenant_id": "t", "id": "m", "role": "member"}
        with _gate(member, _grant("purchase.doc.view")):
            user, tid = pc.auth_member(_Req())
        self.assertEqual((tid, user["id"]), ("t", "m"))

    def test_cashier_role_blocked_on_purchase_codes(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier", "is_super_admin": False}
        with mock.patch("core.pos_api.pos_auth", return_value=cashier):
            with self.assertRaises(PosError) as ctx:
                pc.auth_member(_Req())
        self.assertEqual(ctx.exception.code, "purchase.forbidden")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_no_tenant_forbidden(self):
        with _gate({"id": "x"}):
            with self.assertRaises(PosError) as ctx:
                pc.auth_member(_Req())
        self.assertEqual(ctx.exception.http_status, 403)

    def test_module_disabled_403(self):
        member = {"tenant_id": "t", "id": "m"}
        with _gate(member, _grant(*ALL_CODES), module_disabled=True):
            with self.assertRaises(PosError) as ctx:
                pc.auth_member(_Req())
        self.assertEqual(ctx.exception.code, "pos.module_disabled")
        self.assertEqual(ctx.exception.http_status, 403)


def _src(fn) -> str:
    return inspect.getsource(fn)


class WiringTests(unittest.TestCase):
    """逐路由钉权限码 = 钉死矩阵接线(防回归把 approve 动作降成 view/create)。"""

    def test_config_writes_manage_reads_view(self):
        import routes.purchase_config_routes as cfg

        for fn in (
            cfg.api_create_supplier,
            cfg.api_update_supplier,
            cfg.api_delete_supplier,
            cfg.api_create_category,
            cfg.api_update_category,
            cfg.api_delete_category,
        ):
            self.assertIn('auth_member(request, "purchase.supplier.manage")', _src(fn), fn.__name__)
        self.assertIn(
            'auth_member(request, "purchase.settings.manage")', _src(cfg.api_save_settings)
        )
        for fn in (cfg.api_list_suppliers, cfg.api_get_settings, cfg.api_get_categories):
            self.assertIn('auth_member(request, "purchase.doc.view")', _src(fn), fn.__name__)

    def test_pay_void_post_are_approve_create_list_stay_lower(self):
        import routes.purchase_routes as pr

        for fn in (pr.api_pay_doc, pr.api_void_doc, pr.api_post_doc):
            self.assertIn('auth_member(request, "purchase.doc.approve")', _src(fn), fn.__name__)
        self.assertIn('auth_member(request, "purchase.doc.create")', _src(pr.api_create_doc))
        self.assertIn('auth_member(request, "purchase.doc.view")', _src(pr.api_list_docs))
        self.assertIn('auth_member(request, "purchase.doc.edit")', _src(pr.api_delete_attachment))

    def test_credential_gen_is_approve(self):
        import routes.purchase_routes as pr

        # 凭据生成(替代收据/扣缴凭证)共用 _gen_credential,内部钉 approve 码。
        self.assertIn('auth_member(request, "purchase.doc.approve")', _src(pr._gen_credential))

    def test_intake_codes(self):
        import routes.purchase_intake_routes as ir

        self.assertIn('auth_member(request, "intake.upload")', _src(ir.api_intake))
        self.assertIn('auth_member(request, "purchase.doc.create")', _src(ir.api_quick_expense))


if __name__ == "__main__":
    unittest.main()

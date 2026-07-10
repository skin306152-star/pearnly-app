# -*- coding: utf-8 -*-
"""POS 退货/作废店长授权闸测试(PS-1)。

锁三件事:① 授权判定核(本人有权/收银员需覆盖/店长 PIN 校验各分支);② 闸默认关(fail-closed);
③ 退货/作废路由把授权闸接线进去 + 闸开无权返 pos.approval_required + 授权成功写审计。"""

import inspect
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from core.pos_api import PosError
from services.authz.resolver import Authz
from services.pos import approval as approval_svc


class _Cur:
    """最小假游标:_load_user 的 SELECT 用;execute 记参数,fetchone 返预置行。"""

    def __init__(self, user_row=None):
        self._user_row = user_row

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._user_row


def _cashier_row(*, pin_hash="H", user_id="mgr-user", active=True, cid="mgr-cashier"):
    return {
        "id": cid,
        "pin_hash": pin_hash,
        "user_id": user_id,
        "is_active": active,
        "display_name": "Manager Nok",
    }


class AuthorizeCoreTests(unittest.TestCase):
    def _authz(self, *codes):
        return Authz(role_key="test", permissions=frozenset(codes))

    def test_actor_holds_code_returns_none(self):
        """老板本人持 pos.refund.approve → 无需外部授权(返 None)。"""
        owner = {"tenant_id": "t", "id": "u", "role": "owner", "is_super_admin": False}
        with mock.patch.object(approval_svc.deps, "actor_has_perm", return_value=True):
            out = approval_svc.authorize(
                _Cur(),
                request=None,
                user=owner,
                tenant_id="t",
                workspace_client_id=1,
                approval=None,
            )
        self.assertIsNone(out)

    def test_super_admin_returns_none(self):
        sa = {"tenant_id": "t", "id": "s", "role": "cashier", "is_super_admin": True}
        out = approval_svc.authorize(
            _Cur(), request=None, user=sa, tenant_id="t", workspace_client_id=1, approval=None
        )
        self.assertIsNone(out)

    def test_cashier_no_approval_block_requires_approval(self):
        """收银员无权且未带授权块 → pos.approval_required(前台据此弹窗)。"""
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier", "is_super_admin": False}
        with self.assertRaises(PosError) as ctx:
            approval_svc.authorize(
                _Cur(),
                request=None,
                user=cashier,
                tenant_id="t",
                workspace_client_id=1,
                approval=None,
            )
        self.assertEqual(ctx.exception.code, "pos.approval_required")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_valid_manager_pin_and_perm_returns_approver(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier", "is_super_admin": False}
        user_row = {
            "id": "mgr-user",
            "role": "owner",
            "tenant_id": "t",
            "invited_by": None,
            "is_super_admin": False,
        }
        with (
            mock.patch.object(approval_svc.cashier_dal, "get_cashier", return_value=_cashier_row()),
            mock.patch.object(approval_svc.pos_auth, "verify_pin", return_value=True),
            mock.patch.object(
                approval_svc, "resolve", return_value=self._authz("pos.refund.approve")
            ),
        ):
            out = approval_svc.authorize(
                _Cur(user_row),
                request=None,
                user=cashier,
                tenant_id="t",
                workspace_client_id=1,
                approval={"cashier_id": "mgr-cashier", "pin": "1234"},
            )
        self.assertEqual(out["user_id"], "mgr-user")
        self.assertEqual(out["cashier_id"], "mgr-cashier")
        self.assertEqual(out["name"], "Manager Nok")

    def test_wrong_pin_rejected(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier"}
        with (
            mock.patch.object(approval_svc.cashier_dal, "get_cashier", return_value=_cashier_row()),
            mock.patch.object(approval_svc.pos_auth, "verify_pin", return_value=False),
        ):
            with self.assertRaises(PosError) as ctx:
                approval_svc.authorize(
                    _Cur(),
                    request=None,
                    user=cashier,
                    tenant_id="t",
                    workspace_client_id=1,
                    approval={"cashier_id": "mgr-cashier", "pin": "0000"},
                )
        self.assertEqual(ctx.exception.code, "pos.pin_invalid")

    def test_manager_not_linked_to_user_denied(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier"}
        row = _cashier_row(user_id=None)
        with (
            mock.patch.object(approval_svc.cashier_dal, "get_cashier", return_value=row),
            mock.patch.object(approval_svc.pos_auth, "verify_pin", return_value=True),
        ):
            with self.assertRaises(PosError) as ctx:
                approval_svc.authorize(
                    _Cur(),
                    request=None,
                    user=cashier,
                    tenant_id="t",
                    workspace_client_id=1,
                    approval={"cashier_id": "mgr-cashier", "pin": "1234"},
                )
        self.assertEqual(ctx.exception.code, "pos.approval_denied")

    def test_manager_user_lacks_perm_denied(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier"}
        user_row = {
            "id": "mgr-user",
            "role": "cashier",
            "tenant_id": "t",
            "invited_by": "x",
            "is_super_admin": False,
        }
        with (
            mock.patch.object(approval_svc.cashier_dal, "get_cashier", return_value=_cashier_row()),
            mock.patch.object(approval_svc.pos_auth, "verify_pin", return_value=True),
            mock.patch.object(
                approval_svc, "resolve", return_value=self._authz("pos.sale.operate")
            ),
        ):
            with self.assertRaises(PosError) as ctx:
                approval_svc.authorize(
                    _Cur(user_row),
                    request=None,
                    user=cashier,
                    tenant_id="t",
                    workspace_client_id=1,
                    approval={"cashier_id": "mgr-cashier", "pin": "1234"},
                )
        self.assertEqual(ctx.exception.code, "pos.approval_denied")

    def test_inactive_manager_denied(self):
        cashier = {"tenant_id": "t", "id": "c", "role": "cashier"}
        with mock.patch.object(
            approval_svc.cashier_dal, "get_cashier", return_value=_cashier_row(active=False)
        ):
            with self.assertRaises(PosError) as ctx:
                approval_svc.authorize(
                    _Cur(),
                    request=None,
                    user=cashier,
                    tenant_id="t",
                    workspace_client_id=1,
                    approval={"cashier_id": "mgr-cashier", "pin": "1234"},
                )
        self.assertEqual(ctx.exception.code, "pos.approval_denied")


class GateDefaultTests(unittest.TestCase):
    def test_gate_fail_closed_default_false(self):
        """无 platform_settings 记录 → 闸关(现网 metta 逐字节不变)。"""
        from core import feature_flags

        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertFalse(feature_flags.pos_refund_approval_enabled_for("t-metta"))

    def test_gate_reads_tenant_key(self):
        from core import feature_flags

        seen = {}

        def _fake(key, uid):
            seen["key"], seen["uid"] = key, uid
            return True

        with mock.patch("services.platform_settings.store.is_enabled_for_user", _fake):
            self.assertTrue(feature_flags.pos_refund_approval_enabled_for("t-1"))
        self.assertEqual(seen["key"], "pos_refund_approval")
        self.assertEqual(seen["uid"], "t-1")


class RouteWiringTests(unittest.TestCase):
    """退货/作废路由把授权闸 + 审计接线进去(防回归被摘掉)。"""

    def test_refund_route_wires_gate_and_audit(self):
        import routes.pos_sales_routes as mod

        src = inspect.getsource(mod.api_refund)
        self.assertIn("_gated_write", src)
        self.assertIn('"pos.refund.approved"', src)

    def test_void_route_wires_gate_and_audit(self):
        import routes.pos_sales_routes as mod

        src = inspect.getsource(mod.api_void)
        self.assertIn("_gated_write", src)
        self.assertIn('"pos.void.approved"', src)

    def test_gate_short_circuits_when_off(self):
        with mock.patch("core.feature_flags.pos_refund_approval_enabled_for", return_value=False):
            gated, approver = approval_svc.guard(
                object(),
                request=None,
                user={"role": "cashier"},
                tenant_id="t",
                workspace_client_id=1,
                approval=None,
            )
        self.assertFalse(gated)
        self.assertIsNone(approver)


class _CursorCtx:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class GatedWriteTests(unittest.TestCase):
    """execute_gated_write:闸关直写;闸开无权 → 拦下且写动作绝不发生。"""

    _CASHIER = {
        "tenant_id": "t",
        "id": "c",
        "cashier_id": "c",
        "workspace_client_id": 7,
        "role": "cashier",
        "is_super_admin": False,
    }

    def _run(self, *, gate_on, write_fn):
        import core.db as coredb
        import core.pos_api as pos_api

        with (
            mock.patch.object(pos_api, "pos_auth", return_value=self._CASHIER),
            mock.patch.object(coredb, "get_cursor_rls", return_value=_CursorCtx()),
            mock.patch.object(pos_api, "assert_module_enabled"),
            mock.patch.object(pos_api, "require_workspace"),
            mock.patch("core.feature_flags.pos_refund_approval_enabled_for", return_value=gate_on),
        ):
            return approval_svc.execute_gated_write(
                None,
                ws_override=7,
                approval=None,
                write_fn=write_fn,
                action="pos.refund.approved",
                sale_id_of=lambda r: r["refund_sale"]["id"],
            )

    def test_gate_off_writes_without_approval(self):
        calls = []
        body = self._run(
            gate_on=False,
            write_fn=lambda cur, tid, ws, user: calls.append(1) or {"refund_sale": {"id": "r1"}},
        )
        self.assertTrue(body["ok"])
        self.assertEqual(len(calls), 1)

    def test_gate_on_cashier_no_approval_blocks_write(self):
        calls = []
        with self.assertRaises(PosError) as ctx:
            self._run(
                gate_on=True,
                write_fn=lambda *a: calls.append(1) or {"refund_sale": {"id": "r1"}},
            )
        self.assertEqual(ctx.exception.code, "pos.approval_required")
        self.assertEqual(calls, [])  # 无权 → 退货绝不发生


if __name__ == "__main__":
    unittest.main()

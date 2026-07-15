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


class SelfCapGrantTests(unittest.TestCase):
    """收银员本人 caps(can_refund/can_void)自持 → 免外部授权人(对标 Square/Loyverse 员工退货权)。

    pos_cashier_caps 闸开时读真 caps;闸关时恒最严(需审批·fail-safe)。self_cap 由动作决定
    (退货→can_refund / 作废→can_void),退货作废共用同一 RBAC code(pos.refund.approve)。"""

    _CASHIER = {"tenant_id": "t", "id": "c", "cashier_id": "c", "role": "cashier"}

    def _authorize(self, *, self_cap, approval=None):
        return approval_svc.authorize(
            _Cur(),
            request=None,
            user=self._CASHIER,
            tenant_id="t",
            workspace_client_id=1,
            approval=approval,
            self_cap=self_cap,
        )

    def _patch(self, *, flag_on, caps):
        return (
            mock.patch.object(
                approval_svc.feature_flags,
                "pos_cashier_caps_enabled_for",
                return_value=flag_on,
            ),
            mock.patch.object(approval_svc.caps_svc, "operator_caps", return_value=caps),
        )

    def test_flag_on_can_refund_true_grants(self):
        """闸开 + can_refund=True → authorize 放行(返 None,不要求外部授权人)。"""
        flag, caps = self._patch(flag_on=True, caps={"can_refund": True, "can_void": False})
        with flag, caps:
            out = self._authorize(self_cap="can_refund")
        self.assertIsNone(out)

    def test_flag_on_can_refund_false_still_requires_approval(self):
        """闸开 + can_refund=False + 无授权块 → 维持现状(pos.approval_required)。"""
        flag, caps = self._patch(flag_on=True, caps={"can_refund": False, "can_void": False})
        with flag, caps, self.assertRaises(PosError) as ctx:
            self._authorize(self_cap="can_refund")
        self.assertEqual(ctx.exception.code, "pos.approval_required")

    def test_flag_on_can_void_true_grants(self):
        flag, caps = self._patch(flag_on=True, caps={"can_refund": False, "can_void": True})
        with flag, caps:
            out = self._authorize(self_cap="can_void")
        self.assertIsNone(out)

    def test_flag_on_can_void_false_requires_approval(self):
        """can_refund=True 但 can_void=False → 作废(self_cap=can_void)仍需审批(权不串)。"""
        flag, caps = self._patch(flag_on=True, caps={"can_refund": True, "can_void": False})
        with flag, caps, self.assertRaises(PosError) as ctx:
            self._authorize(self_cap="can_void")
        self.assertEqual(ctx.exception.code, "pos.approval_required")

    def test_flag_off_never_reads_caps_and_requires_approval(self):
        """闸关 → 无论 caps 如何都要求审批,且绝不读 caps(fail-safe,不放松)。"""
        caps_mock = mock.Mock(return_value={"can_refund": True, "can_void": True})
        with (
            mock.patch.object(
                approval_svc.feature_flags, "pos_cashier_caps_enabled_for", return_value=False
            ),
            mock.patch.object(approval_svc.caps_svc, "operator_caps", caps_mock),
            self.assertRaises(PosError) as ctx,
        ):
            self._authorize(self_cap="can_refund")
        self.assertEqual(ctx.exception.code, "pos.approval_required")
        caps_mock.assert_not_called()

    def test_owner_holding_code_bypasses_cap_path(self):
        """owner 主账号持码 → _actor_holds_code 直放,不进 caps 路(回归不破)。"""
        owner = {"tenant_id": "t", "id": "u", "role": "owner", "is_super_admin": False}
        caps_mock = mock.Mock(return_value={"can_refund": False})
        with (
            mock.patch.object(approval_svc.deps, "actor_has_perm", return_value=True),
            mock.patch.object(approval_svc.caps_svc, "operator_caps", caps_mock),
        ):
            out = approval_svc.authorize(
                _Cur(),
                request=None,
                user=owner,
                tenant_id="t",
                workspace_client_id=1,
                approval=None,
                self_cap="can_refund",
            )
        self.assertIsNone(out)
        caps_mock.assert_not_called()

    def test_no_self_cap_does_not_read_caps(self):
        """self_cap 为空(非退货/作废动作)→ 不读 caps → 其它受闸写行为不变。"""
        with (
            mock.patch.object(
                approval_svc.feature_flags, "pos_cashier_caps_enabled_for", return_value=True
            ),
            mock.patch.object(
                approval_svc.caps_svc, "operator_caps", return_value={"can_refund": True}
            ),
        ):
            self.assertFalse(
                approval_svc._actor_self_cap_grants(
                    _Cur(),
                    user=self._CASHIER,
                    tenant_id="t",
                    workspace_client_id=1,
                    cap_key=None,
                )
            )

    def test_action_to_cap_mapping_only_refund_and_void(self):
        """动作→cap 映射只覆盖退货/作废两动作,其它动作无映射(不读 caps)。"""
        self.assertEqual(approval_svc._ACTION_SELF_CAP.get("pos.refund.approved"), "can_refund")
        self.assertEqual(approval_svc._ACTION_SELF_CAP.get("pos.void.approved"), "can_void")
        self.assertIsNone(approval_svc._ACTION_SELF_CAP.get("pos.discount.approved"))
        self.assertEqual(len(approval_svc._ACTION_SELF_CAP), 2)


class SelfCapActionWiringTests(unittest.TestCase):
    """execute_gated_write 把 action 正确译成 self_cap:退货读 can_refund、作废读 can_void。

    坐实防内盗关键 —— 退货/作废共用 RBAC 码,若按 code 选 cap 会「可退货」误开成「可作废」。"""

    _CASHIER = {
        "tenant_id": "t",
        "id": "c",
        "cashier_id": "c",
        "workspace_client_id": 7,
        "role": "cashier",
        "is_super_admin": False,
        "entry": "pos",  # 收银员 token 天然 entry=pos(pos_auth 合成)· 入口作用域闸恒开下须匹配
    }

    def _run(self, *, action, caps, write_fn):
        import core.db as coredb
        import core.pos_api as pos_api

        with (
            mock.patch.object(pos_api, "pos_auth", return_value=self._CASHIER),
            mock.patch.object(coredb, "get_cursor_rls", return_value=_CursorCtx()),
            mock.patch.object(pos_api, "assert_module_enabled"),
            mock.patch.object(pos_api, "require_workspace"),
            mock.patch("core.feature_flags.pos_refund_approval_enabled_for", return_value=True),
            mock.patch("core.feature_flags.pos_cashier_caps_enabled_for", return_value=True),
            mock.patch.object(approval_svc.caps_svc, "operator_caps", return_value=caps),
        ):
            return approval_svc.execute_gated_write(
                None,
                ws_override=7,
                approval=None,
                write_fn=write_fn,
                action=action,
                sale_id_of=lambda r: r.get("id", "x"),
            )

    def test_void_uses_can_void_not_can_refund(self):
        """can_refund=True/can_void=False 的收银员发起作废(action=pos.void.approved)→ 仍被拦。"""
        calls = []
        with self.assertRaises(PosError) as ctx:
            self._run(
                action="pos.void.approved",
                caps={"can_refund": True, "can_void": False},
                write_fn=lambda *a: calls.append(1) or {"id": "s1"},
            )
        self.assertEqual(ctx.exception.code, "pos.approval_required")
        self.assertEqual(calls, [])

    def test_refund_uses_can_refund(self):
        """can_refund=True 的收银员发起退货(action=pos.refund.approved)→ 直接放行落库。"""
        calls = []
        body = self._run(
            action="pos.refund.approved",
            caps={"can_refund": True, "can_void": False},
            write_fn=lambda cur, tid, ws, user: calls.append(1) or {"id": "r1"},
        )
        self.assertTrue(body["ok"])
        self.assertEqual(len(calls), 1)


class GateDefaultTests(unittest.TestCase):
    """POS 权限/审批已验收上线 → 代码层全店恒开(测完就全开·不灰度),不依赖 platform_settings。"""

    def test_refund_approval_on_for_all_tenants(self):
        from core import feature_flags

        # 即便 platform_settings 无记录 / 答否,已上线功能对所有租户恒开(去 allowlist 灰度)。
        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertTrue(feature_flags.pos_refund_approval_enabled_for("t-metta"))
            self.assertTrue(feature_flags.pos_refund_approval_enabled_for("t-any"))

    def test_cashier_caps_on_for_all_tenants(self):
        from core import feature_flags

        with mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False):
            self.assertTrue(feature_flags.pos_cashier_caps_enabled_for("t-metta"))
            self.assertTrue(feature_flags.pos_cashier_caps_enabled_for(None))


class RouteWiringTests(unittest.TestCase):
    """退货/作废路由把授权闸 + 审计接线进去(防回归被摘掉)。"""

    def test_refund_route_wires_gate_and_audit(self):
        import routes.pos_sales_routes as mod

        src = inspect.getsource(mod.api_refund)
        self.assertIn("approval_svc.execute_gated_write", src)
        self.assertIn('"pos.refund.approved"', src)

    def test_void_route_wires_gate_and_audit(self):
        import routes.pos_sales_routes as mod

        src = inspect.getsource(mod.api_void)
        self.assertIn("approval_svc.execute_gated_write", src)
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
        "entry": "pos",  # 收银员 token 天然 entry=pos(pos_auth 合成)· 入口作用域闸恒开下须匹配
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
            # caps 闸已恒开(去灰度)→ 授权会真读操作者 caps;本套用例的收银员无 can_refund 自权,
            # 直接短其 self-cap 授权(无权),验证"无权收银员即便审批闸开也被拦、须店长覆盖"。
            mock.patch.object(approval_svc, "_actor_self_cap_grants", return_value=False),
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

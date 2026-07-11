# -*- coding: utf-8 -*-
"""收银前台 caps 闸测试(PC-1a):建单折扣超限/改价的授权判定 + approval.py 泛化。

锁:① flag 关 → 完全跳过(不算 caps、不拦);② 纯收银员折扣超限无授权块 → pos.approval_required;
③ 带正确店长 PIN → 放行 + 审计事件;④ 全权操作者(老板)→ 无上限直放行;⑤ approval.authorize
接受 code 参数、退货默认码零改动;⑥ 改价(手工价低于挂牌)按 can_override_price 判。"""

import os
import unittest
from decimal import Decimal
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from core.pos_api import PosError
from services.authz.resolver import Authz
from services.pos import approval as approval_svc
from services.pos import caps as caps_svc
from services.pos import sale_caps


def _totals(subtotal, discount_total, header=0):
    return {
        "subtotal": Decimal(str(subtotal)),
        "discount_total": Decimal(str(discount_total)),
        "header_discount_amount": Decimal(str(header)),
    }


class DiscountPctTests(unittest.TestCase):
    def test_pct_of_line_and_header(self):
        # 折前毛额 = 80 + 20 = 100;总折扣 = 20 + 10 = 30 → 30%
        self.assertEqual(sale_caps._discount_pct(_totals(80, 20, 10)), Decimal("30.00"))

    def test_zero_discount(self):
        self.assertEqual(sale_caps._discount_pct(_totals(100, 0)), Decimal("0.00"))


class PriceOverrideTests(unittest.TestCase):
    def test_below_list_is_override(self):
        resolved = [{"unit_price": Decimal("8"), "list_price": Decimal("10")}]
        self.assertTrue(sale_caps._has_price_override(resolved))

    def test_at_or_above_list_not_override(self):
        resolved = [{"unit_price": Decimal("10"), "list_price": Decimal("10")}]
        self.assertFalse(sale_caps._has_price_override(resolved))

    def test_no_list_price_not_override(self):
        resolved = [{"unit_price": Decimal("1"), "list_price": None}]
        self.assertFalse(sale_caps._has_price_override(resolved))


class EnforceCapsTests(unittest.TestCase):
    _CASHIER = {"role": "cashier", "cashier_id": "c1"}

    def _run(self, *, flag_on, caps, totals, resolved, approval=None, verify=None):
        default_verify = lambda *a, **k: {"user_id": "m", "cashier_id": "mc", "name": "Mgr"}
        with (
            mock.patch.object(
                sale_caps.feature_flags, "pos_cashier_caps_enabled_for", return_value=flag_on
            ),
            mock.patch.object(sale_caps.caps_svc, "operator_caps", return_value=caps),
            mock.patch.object(
                sale_caps.approval_svc,
                "verify_manager_override",
                side_effect=verify or default_verify,
            ),
        ):
            return sale_caps.enforce(
                object(),
                tenant_id="t",
                workspace_client_id=9,
                operator=self._CASHIER,
                approval=approval,
                totals=totals,
                resolved=resolved,
            )

    def test_flag_off_skips_entirely(self):
        called = {}

        def _op(*a, **k):
            called["yes"] = True
            return {}

        with (
            mock.patch.object(
                sale_caps.feature_flags, "pos_cashier_caps_enabled_for", return_value=False
            ),
            mock.patch.object(sale_caps.caps_svc, "operator_caps", side_effect=_op),
        ):
            events = sale_caps.enforce(
                object(),
                tenant_id="t",
                workspace_client_id=9,
                operator=self._CASHIER,
                approval=None,
                totals=_totals(80, 20),
                resolved=[],
            )
        self.assertEqual(events, [])
        self.assertNotIn("yes", called)  # caps 都不算,逐字节走历史

    def test_operator_none_skips(self):
        events = sale_caps.enforce(
            object(),
            tenant_id="t",
            workspace_client_id=9,
            operator=None,
            approval=None,
            totals=_totals(80, 20),
            resolved=[],
        )
        self.assertEqual(events, [])

    def test_discount_over_limit_without_approval_raises(self):
        caps = dict(caps_svc.CAP_DEFAULTS)  # discount_limit_pct=0
        with self.assertRaises(PosError) as ctx:
            self._run(
                flag_on=True,
                caps=caps,
                totals=_totals(80, 20),  # 20%
                resolved=[],
                verify=lambda *a, **k: (_ for _ in ()).throw(PosError("pos.approval_required", 403)),
            )
        self.assertEqual(ctx.exception.code, "pos.approval_required")

    def test_discount_over_limit_with_manager_returns_event(self):
        caps = {**caps_svc.CAP_DEFAULTS, "discount_limit_pct": 10}
        events = self._run(
            flag_on=True,
            caps=caps,
            totals=_totals(80, 20),  # 20% > 10%
            resolved=[],
            approval={"cashier_id": "mc", "pin": "1234"},
        )
        self.assertEqual(len(events), 1)
        action, approver, details = events[0]
        self.assertEqual(action, "pos.discount.approved")
        self.assertEqual(approver["user_id"], "m")

    def test_within_limit_no_gate(self):
        caps = {**caps_svc.CAP_DEFAULTS, "discount_limit_pct": 50}
        events = self._run(flag_on=True, caps=caps, totals=_totals(80, 20), resolved=[])
        self.assertEqual(events, [])

    def test_full_operator_no_gate(self):
        events = self._run(
            flag_on=True,
            caps=caps_svc.full_caps(),
            totals=_totals(50, 50),  # 50%
            resolved=[{"unit_price": Decimal("1"), "list_price": Decimal("10")}],
        )
        self.assertEqual(events, [])

    def test_price_override_gated(self):
        caps = {**caps_svc.full_caps(), "can_override_price": False, "discount_limit_pct": 100}
        events = self._run(
            flag_on=True,
            caps=caps,
            totals=_totals(100, 0),
            resolved=[{"unit_price": Decimal("8"), "list_price": Decimal("10")}],
            approval={"cashier_id": "mc", "pin": "1234"},
        )
        self.assertEqual([e[0] for e in events], ["pos.price.approved"])


class _Cur:
    def __init__(self, user_row=None):
        self._row = user_row

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._row


class ApprovalGeneralizationTests(unittest.TestCase):
    """approval.authorize/guard/execute_gated_write 接受 code;退货默认码不变。"""

    def test_authorize_defaults_to_refund_code(self):
        owner = {"tenant_id": "t", "id": "u", "role": "owner", "is_super_admin": False}
        seen = {}

        def _holds(request, user, code):
            seen["code"] = code
            return True

        with mock.patch.object(approval_svc.deps, "actor_has_perm", side_effect=_holds):
            out = approval_svc.authorize(
                _Cur(), request=None, user=owner, tenant_id="t", workspace_client_id=1, approval=None
            )
        self.assertIsNone(out)
        self.assertEqual(seen["code"], "pos.refund.approve")

    def test_authorize_custom_code_passed_through(self):
        owner = {"tenant_id": "t", "id": "u", "role": "owner", "is_super_admin": False}
        seen = {}
        with mock.patch.object(
            approval_svc.deps,
            "actor_has_perm",
            side_effect=lambda r, u, c: seen.setdefault("code", c) or True,
        ):
            approval_svc.authorize(
                _Cur(),
                request=None,
                user=owner,
                tenant_id="t",
                workspace_client_id=1,
                approval=None,
                code="pos.admin.manage",
            )
        self.assertEqual(seen["code"], "pos.admin.manage")

    def test_verify_manager_override_needs_approval_block(self):
        with self.assertRaises(PosError) as ctx:
            approval_svc.verify_manager_override(
                _Cur(), tenant_id="t", workspace_client_id=1, approval=None
            )
        self.assertEqual(ctx.exception.code, "pos.approval_required")

    def test_verify_manager_override_accepts_admin_manage(self):
        user_row = {
            "id": "mgr-user",
            "role": "admin",
            "tenant_id": "t",
            "invited_by": "x",
            "is_super_admin": False,
        }
        cashier_row = {
            "id": "mc",
            "pin_hash": "H",
            "user_id": "mgr-user",
            "is_active": True,
            "display_name": "Mgr",
        }
        with (
            mock.patch.object(approval_svc.cashier_dal, "get_cashier", return_value=cashier_row),
            mock.patch.object(approval_svc.pos_auth, "verify_pin", return_value=True),
            mock.patch.object(
                approval_svc, "resolve", return_value=Authz(role_key="admin", permissions=frozenset({"pos.admin.manage"}))
            ),
        ):
            out = approval_svc.verify_manager_override(
                _Cur(user_row),
                tenant_id="t",
                workspace_client_id=1,
                approval={"cashier_id": "mc", "pin": "1234"},
            )
        self.assertEqual(out["user_id"], "mgr-user")


if __name__ == "__main__":
    unittest.main()

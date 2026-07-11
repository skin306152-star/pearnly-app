# -*- coding: utf-8 -*-
"""收银员 caps 语义 + 解析测试(PC-1a)。

锁:① merge_defaults 最严补齐 + 类型规整;② sanitize_caps 白名单/越界拒;③ resolve_caps 单一
事实源(绑主账号走 RBAC、纯收银员读 caps 列、超管全放开、跨租户绑定回落最严)。"""

import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from services.pos import caps as caps_svc


class _Authz:
    def __init__(self, *codes):
        self._codes = frozenset(codes)

    def has(self, code):
        return code in self._codes


class MergeDefaultsTests(unittest.TestCase):
    def test_empty_returns_strictest(self):
        self.assertEqual(caps_svc.merge_defaults(None), caps_svc.CAP_DEFAULTS)
        self.assertEqual(caps_svc.merge_defaults({}), caps_svc.CAP_DEFAULTS)

    def test_json_string_parsed(self):
        out = caps_svc.merge_defaults('{"can_refund": true, "discount_limit_pct": 15}')
        self.assertTrue(out["can_refund"])
        self.assertEqual(out["discount_limit_pct"], 15)
        self.assertFalse(out["can_void"])  # 缺键补最严

    def test_pct_clamped_and_bools_coerced(self):
        out = caps_svc.merge_defaults({"discount_limit_pct": 500, "cost_visible": 1})
        self.assertEqual(out["discount_limit_pct"], 100)
        self.assertTrue(out["cost_visible"])

    def test_unknown_keys_dropped(self):
        out = caps_svc.merge_defaults({"bogus": True, "can_void": True})
        self.assertNotIn("bogus", out)
        self.assertTrue(out["can_void"])


class SanitizeCapsTests(unittest.TestCase):
    def test_unknown_key_rejected(self):
        with self.assertRaises(ValueError):
            caps_svc.sanitize_caps({"can_hack": True})

    def test_pct_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            caps_svc.sanitize_caps({"discount_limit_pct": 101})
        with self.assertRaises(ValueError):
            caps_svc.sanitize_caps({"discount_limit_pct": -1})

    def test_pct_bool_rejected(self):
        with self.assertRaises(ValueError):
            caps_svc.sanitize_caps({"discount_limit_pct": True})

    def test_non_bool_flag_rejected(self):
        with self.assertRaises(ValueError):
            caps_svc.sanitize_caps({"can_refund": "yes"})

    def test_valid_roundtrips_with_defaults(self):
        out = caps_svc.sanitize_caps({"discount_limit_pct": 20, "can_refund": True})
        self.assertEqual(out["discount_limit_pct"], 20)
        self.assertTrue(out["can_refund"])
        self.assertFalse(out["can_override_price"])


class ResolveCapsTests(unittest.TestCase):
    def test_super_admin_full(self):
        out = caps_svc.resolve_caps(object(), "t", {"is_super_admin": True})
        self.assertEqual(out, caps_svc.full_caps())

    def test_pure_cashier_reads_caps_column(self):
        row = {"caps": {"discount_limit_pct": 10}, "user_id": None}
        out = caps_svc.resolve_caps(object(), "t", row)
        self.assertEqual(out["discount_limit_pct"], 10)
        self.assertFalse(out["can_refund"])

    def test_bound_manager_full_via_rbac(self):
        row = {"caps": {}, "user_id": "mgr-user"}
        u = {"id": "mgr-user", "is_super_admin": False}
        with (
            mock.patch.object(caps_svc, "load_user_min", return_value=u),
            mock.patch.object(caps_svc, "resolve", return_value=_Authz("pos.refund.approve")),
        ):
            out = caps_svc.resolve_caps(object(), "t", row)
        self.assertEqual(out, caps_svc.full_caps())

    def test_bound_clerk_no_full_codes_min_but_cost_from_field(self):
        row = {"caps": {"discount_limit_pct": 99}, "user_id": "clerk-user"}
        u = {"id": "clerk-user", "is_super_admin": False}
        with (
            mock.patch.object(caps_svc, "load_user_min", return_value=u),
            mock.patch.object(caps_svc, "resolve", return_value=_Authz("field.cost.view")),
        ):
            out = caps_svc.resolve_caps(object(), "t", row)
        # 绑主账号 → 忽略 caps 列(99 不生效),按 RBAC 换算
        self.assertEqual(out["discount_limit_pct"], 0)
        self.assertTrue(out["cost_visible"])
        self.assertFalse(out["can_override_price"])

    def test_bound_but_cross_tenant_user_falls_back_strict(self):
        row = {"caps": {"can_refund": True}, "user_id": "gone"}
        with mock.patch.object(caps_svc, "load_user_min", return_value=None):
            out = caps_svc.resolve_caps(object(), "t", row)
        self.assertEqual(out, caps_svc.CAP_DEFAULTS)

    def test_main_account_owner_full(self):
        owner = {"id": "u", "role": "owner", "tenant_id": "t"}
        with mock.patch.object(caps_svc, "resolve", return_value=_Authz("pos.admin.manage")):
            out = caps_svc.resolve_caps(object(), "t", owner)
        self.assertEqual(out, caps_svc.full_caps())


class OperatorCapsTests(unittest.TestCase):
    def test_cashier_loads_row(self):
        row = {"caps": {"discount_limit_pct": 5}, "user_id": None}
        user = {"role": "cashier", "cashier_id": "c1"}
        with mock.patch("services.pos.cashier.get_cashier", return_value=row):
            out = caps_svc.operator_caps(object(), user=user, tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["discount_limit_pct"], 5)

    def test_cashier_without_id_strict(self):
        user = {"role": "cashier"}
        out = caps_svc.operator_caps(object(), user=user, tenant_id="t", workspace_client_id=9)
        self.assertEqual(out, caps_svc.CAP_DEFAULTS)

    def test_main_account_uses_rbac(self):
        user = {"role": "owner", "id": "u", "tenant_id": "t"}
        with mock.patch.object(caps_svc, "resolve", return_value=_Authz("pos.refund.approve")):
            out = caps_svc.operator_caps(object(), user=user, tenant_id="t", workspace_client_id=9)
        self.assertEqual(out, caps_svc.full_caps())


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""6 角色 × 全部权限码逐格断言(docs/permissions/02 矩阵的可执行版)。

期望值按矩阵行规则独立重新编码(不抄 registry 实现),registry 改动偏离图纸即红。
"""

import unittest

from services.authz import registry

ALL = registry.ALL_CODES
CROSS = set(registry.CROSS_CODES)
FIELD = set(registry.FIELD_CODES)
BUSINESS = ALL - CROSS - FIELD
POS = set(registry.POS_CODES)


def _verb(code):
    return code.rsplit(".", 1)[-1]


def _expected(role, code):
    """02 矩阵逐行规则 → 单元格期望。"""
    if code in FIELD:
        # G4:成本/工资可见性预设全开,唯收银员(POS 令牌)无(它根本进不了报表)
        return role != "cashier"
    if role == "owner":
        return True
    if role == "admin":
        return code not in {"billing.manage", "ownership.transfer"}
    if role == "cashier":
        return code in {"pos.sale.operate", "pos.shift.operate"}
    if role == "viewer":
        return (
            code in BUSINESS
            and _verb(code) in {"view", "export"}
            and code
            not in {
                "pos.sale.operate",
            }
        )
    if role == "clerk":
        if code in {"kb.ask", "intake.upload"}:
            return True
        return code in BUSINESS - POS and _verb(code) in {"view", "create", "edit", "delete"}
    if role == "accountant":
        if _expected("clerk", code):
            return True
        if code in {"pos.report.view", "acct.entry.review", "tax.filing.review", "tax.filing.file"}:
            return True
        if code in {"acct.coa.manage", "sales.product.manage", "purchase.supplier.manage"}:
            return True
        return code in BUSINESS - POS and _verb(code) in {"approve", "export"}
    raise AssertionError(f"unknown role {role}")


class MatrixGridTests(unittest.TestCase):
    def test_six_roles_present(self):
        self.assertEqual(
            set(registry.ROLE_KEYS),
            {"owner", "admin", "accountant", "clerk", "viewer", "cashier"},
        )

    def test_full_grid(self):
        for role in registry.ROLE_KEYS:
            granted = registry.ROLE_PERMISSIONS[role]
            for code in sorted(ALL):
                self.assertEqual(
                    code in granted,
                    _expected(role, code),
                    f"矩阵偏离图纸: role={role} code={code}",
                )


class MatrixInvariantTests(unittest.TestCase):
    def test_owner_short_circuit_covers_all(self):
        self.assertEqual(registry.ROLE_PERMISSIONS["owner"], ALL)

    def test_admin_lacks_exactly_billing_and_ownership(self):
        missing = ALL - registry.ROLE_PERMISSIONS["admin"]
        self.assertEqual(missing, {"billing.manage", "ownership.transfer"})

    def test_clerk_never_irreversible(self):
        for code in registry.ROLE_PERMISSIONS["clerk"]:
            self.assertNotEqual(_verb(code), "approve", f"录入员不可有不可逆动作: {code}")
            self.assertNotEqual(_verb(code), "export", f"录入员不可导出: {code}")

    def test_viewer_read_only_plus_export(self):
        for code in registry.ROLE_PERMISSIONS["viewer"]:
            self.assertIn(_verb(code), {"view", "export"}, code)

    def test_cashier_only_pos_operations(self):
        self.assertEqual(
            registry.ROLE_PERMISSIONS["cashier"],
            {"pos.sale.operate", "pos.shift.operate"},
        )

    def test_no_role_touches_team_below_admin(self):
        for role in ("accountant", "clerk", "viewer", "cashier"):
            for code in registry.ROLE_PERMISSIONS[role]:
                self.assertFalse(code.startswith("team."), f"{role} 不可管团队: {code}")
                self.assertFalse(code.startswith("billing."), f"{role} 不可碰计费: {code}")
                self.assertFalse(code.startswith("settings."), f"{role} 不可碰设置: {code}")

    def test_assignable_roles_exclude_owner_and_cashier(self):
        self.assertEqual(
            set(registry.ASSIGNABLE_ROLE_KEYS), {"admin", "accountant", "clerk", "viewer"}
        )
        self.assertEqual(set(registry.SCOPABLE_ROLE_KEYS), {"accountant", "clerk", "viewer"})

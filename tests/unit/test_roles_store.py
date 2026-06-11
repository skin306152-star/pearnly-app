# -*- coding: utf-8 -*-
"""自定义角色 DAL 守门(G3):码集净化(提权码禁入)、slug 唯一化、分配边界。

库相关 CRUD 由真库 E2E 覆盖;此处锁纯逻辑与入口校验(不触库的分支)。
"""

import unittest

from services.authz import roles_store


class SanitizeCodesTests(unittest.TestCase):
    def test_unknown_codes_dropped(self):
        self.assertEqual(
            roles_store._sanitize_codes(["sales.doc.view", "made.up.code"]),
            ["sales.doc.view"],
        )

    def test_escalation_codes_forbidden(self):
        codes = roles_store._sanitize_codes(
            ["sales.doc.view", "ownership.transfer", "billing.manage"]
        )
        self.assertNotIn("ownership.transfer", codes)
        self.assertNotIn("billing.manage", codes)
        self.assertIn("sales.doc.view", codes)

    def test_field_cost_code_allowed(self):
        # 成本可见码本身是自定义角色要勾/不勾的对象,必须允许
        self.assertIn("field.cost.view", roles_store._sanitize_codes(["field.cost.view"]))

    def test_dedup_and_sorted(self):
        out = roles_store._sanitize_codes(["sales.doc.view", "sales.doc.view", "acct.entry.view"])
        self.assertEqual(out, ["acct.entry.view", "sales.doc.view"])

    def test_non_list_yields_empty(self):
        self.assertEqual(roles_store._sanitize_codes(None), [])
        self.assertEqual(roles_store._sanitize_codes("sales.doc.view"), [])


class SlugifyTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(roles_store._slugify("Floor Manager"), "floor-manager")

    def test_non_latin_falls_back(self):
        self.assertEqual(roles_store._slugify("店长"), "role")

    def test_empty_falls_back(self):
        self.assertEqual(roles_store._slugify("  "), "role")


class _SlugCursor:
    def __init__(self, used_keys):
        self._used = [{"key": k} for k in used_keys]

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._used


class UniqueSlugTests(unittest.TestCase):
    def test_free_slug_returned_as_is(self):
        self.assertEqual(roles_store._unique_slug(_SlugCursor([]), "t", "manager"), "manager")

    def test_collision_suffixed(self):
        cur = _SlugCursor(["custom:manager", "custom:manager-2"])
        self.assertEqual(roles_store._unique_slug(cur, "t", "manager"), "manager-3")


class CreateValidationTests(unittest.TestCase):
    def test_blank_name_rejected(self):
        out = roles_store.create_custom_role(
            tenant_id="t", actor_id="a", display_name="  ", permission_codes=["sales.doc.view"]
        )
        self.assertEqual(out["error"], "team.role_name_invalid")

    def test_empty_permissions_rejected(self):
        out = roles_store.create_custom_role(
            tenant_id="t", actor_id="a", display_name="X", permission_codes=["not.a.code"]
        )
        self.assertEqual(out["error"], "team.role_permissions_empty")


class AssignGuardTests(unittest.TestCase):
    def test_cannot_assign_to_self(self):
        out = roles_store.assign_role(
            tenant_id="t", actor_id="u1", target_user_id="u1", role_key="custom:x"
        )
        self.assertEqual(out["error"], "team.cannot_modify_self")

    def test_cannot_assign_owner_key(self):
        # owner 走转移流:系统键委托 change_role,owner 不在 ASSIGNABLE → role_not_assignable
        # (在 ASSIGNABLE 校验处即返回,不触库)
        out = roles_store.assign_role(
            tenant_id="t", actor_id="a", target_user_id="u2", role_key="owner"
        )
        self.assertEqual(out["error"], "team.role_not_assignable")

    def test_cannot_target_owner(self):
        orig = roles_store.console_store.get_member
        roles_store.console_store.get_member = lambda t, u: {
            "role_key": "owner",
            "username": "boss",
        }
        try:
            out = roles_store.assign_role(
                tenant_id="t", actor_id="a", target_user_id="u2", role_key="custom:x"
            )
        finally:
            roles_store.console_store.get_member = orig
        self.assertEqual(out["error"], "team.target_is_owner")


if __name__ == "__main__":
    unittest.main()

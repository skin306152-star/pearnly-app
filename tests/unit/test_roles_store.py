# -*- coding: utf-8 -*-
"""自定义角色 DAL 守门(G3):码集净化(提权码禁入)、slug 唯一化、分配边界。

库相关 CRUD 由真库 E2E 覆盖;此处锁纯逻辑与入口校验(不触库的分支)。
"""

import unittest
from datetime import datetime, timezone
from unittest import mock

from services.authz import roles_store


class SanitizeCodesTests(unittest.TestCase):
    def test_unknown_codes_dropped(self):
        self.assertEqual(
            roles_store._sanitize_codes(["sales.doc.view", "made.up.code"]),
            ["sales.doc.view"],
        )

    def test_escalation_codes_forbidden(self):
        codes = roles_store._sanitize_codes(
            [
                "sales.doc.view",
                "ownership.transfer",
                "billing.manage",
                "erp.endpoint.manage",
            ]
        )
        self.assertNotIn("ownership.transfer", codes)
        self.assertNotIn("billing.manage", codes)
        self.assertNotIn("erp.endpoint.manage", codes)
        self.assertIn("sales.doc.view", codes)

    def test_non_manage_erp_codes_allowed(self):
        codes = ["erp.endpoint.view", "erp.push.operate", "erp.log.view"]
        self.assertEqual(roles_store._sanitize_codes(codes), sorted(codes))

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


class ActiveCustomRoleLookupTests(unittest.TestCase):
    class _Cursor:
        def __init__(self, row):
            self.row = row
            self.sql = ""
            self.params = None

        def execute(self, sql, params=None):
            self.sql = sql
            self.params = params

        def fetchone(self):
            return self.row

    def test_lookup_is_tenant_and_active_scoped(self):
        cur = self._Cursor({"id": "r1", "key": "custom:buyer", "role_name": "Buyer"})
        out = roles_store.get_active_custom_role_by_key(cur, "tenant-a", "custom:buyer")
        self.assertEqual(out["role_name"], "Buyer")
        self.assertEqual(cur.params, ("tenant-a", "custom:buyer"))
        self.assertIn("tenant_id = %s", cur.sql)
        self.assertIn("COALESCE(is_active, TRUE)", cur.sql)
        self.assertIn("FOR SHARE", cur.sql)

    def test_missing_cross_tenant_or_inactive_role_is_rejected(self):
        cur = self._Cursor(None)
        self.assertIsNone(
            roles_store.get_active_custom_role_by_key(cur, "tenant-a", "custom:buyer")
        )

    def test_system_role_does_not_query_custom_store(self):
        cur = self._Cursor({"id": "unexpected"})
        self.assertIsNone(roles_store.get_active_custom_role_by_key(cur, "tenant-a", "viewer"))
        self.assertEqual(cur.sql, "")


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


class DeleteRoleInvitationIntegrityTests(unittest.TestCase):
    class _Cursor:
        def __init__(self, *, member_count=0):
            self.member_count = member_count
            self.calls = []
            self.current = None
            self.rowcount = 0
            self.pending_invitation = {"revoked_at": None}

        def execute(self, sql, params=None):
            compact = " ".join(sql.split())
            self.calls.append((compact, params))
            self.rowcount = 0
            if compact.startswith("SELECT r.key"):
                self.current = {
                    "key": "custom:buyer",
                    "role_name": "Buyer",
                }
            elif compact.startswith("SELECT COUNT(*) AS c FROM memberships"):
                self.current = {"c": self.member_count}
            elif compact.startswith("UPDATE invitations SET revoked_at"):
                self.pending_invitation["revoked_at"] = datetime.now(timezone.utc)
                self.current = None
                self.rowcount = 1
            elif compact.startswith("DELETE FROM roles"):
                self.current = None
                self.rowcount = 1
            else:
                self.current = None

        def fetchone(self):
            return self.current

    class _CM:
        def __init__(self, cur):
            self.cur = cur

        def __enter__(self):
            return self.cur

        def __exit__(self, *args):
            return False

    def test_delete_locks_role_then_revokes_pending_invites_before_delete(self):
        cur = self._Cursor()
        with mock.patch.object(roles_store.db, "get_cursor", return_value=self._CM(cur)):
            out = roles_store.delete_custom_role(tenant_id="tenant-a", role_id="role-1")
        self.assertTrue(out["ok"])
        self.assertEqual(out["revoked_invitations"], 1)
        self.assertIsNotNone(cur.pending_invitation["revoked_at"])
        statements = [sql for sql, _ in cur.calls]
        self.assertIn("FOR UPDATE", statements[0])
        self.assertTrue(statements[1].startswith("SELECT COUNT(*) AS c FROM memberships"))
        self.assertTrue(statements[2].startswith("UPDATE invitations SET revoked_at"))
        self.assertTrue(statements[3].startswith("DELETE FROM roles"))
        self.assertIn("accepted_at IS NULL", statements[2])
        self.assertIn("revoked_at IS NULL", statements[2])
        self.assertIn("expires_at > NOW()", statements[2])

    def test_any_membership_reference_blocks_delete_before_invitation_revoke(self):
        cur = self._Cursor(member_count=2)
        with mock.patch.object(roles_store.db, "get_cursor", return_value=self._CM(cur)):
            out = roles_store.delete_custom_role(tenant_id="tenant-a", role_id="role-1")
        self.assertEqual(out, {"error": "team.role_in_use", "member_count": 2})
        self.assertEqual(len(cur.calls), 2)
        self.assertNotIn("status = 'active'", cur.calls[1][0])
        self.assertIsNone(cur.pending_invitation["revoked_at"])


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
        cur = mock.Mock()
        cm = mock.MagicMock()
        cm.__enter__.return_value = cur
        cm.__exit__.return_value = False
        member = {"membership_id": "m1", "role_key": "owner", "username": "boss"}
        with (
            mock.patch.object(roles_store.db, "get_cursor", return_value=cm),
            mock.patch.object(
                roles_store,
                "get_active_custom_role_by_key",
                return_value={"id": "role-1", "key": "custom:x"},
            ),
            mock.patch.object(
                roles_store.console_store,
                "_get_member_with_cursor",
                return_value=member,
            ) as get_member,
            mock.patch.object(roles_store, "set_membership_role_resolved") as set_role,
        ):
            out = roles_store.assign_role(
                tenant_id="t", actor_id="a", target_user_id="u2", role_key="custom:x"
            )
        self.assertEqual(out["error"], "team.target_is_owner")
        get_member.assert_called_once_with(cur, "t", "u2", for_update=True)
        set_role.assert_not_called()

    def test_custom_assignment_checks_and_updates_on_same_locked_cursor(self):
        cur = mock.Mock()
        cm = mock.MagicMock()
        cm.__enter__.return_value = cur
        cm.__exit__.return_value = False
        member = {"membership_id": "m1", "role_key": "viewer", "username": "staff"}
        order = mock.Mock()
        with (
            mock.patch.object(roles_store.db, "get_cursor", return_value=cm),
            mock.patch.object(
                roles_store,
                "get_active_custom_role_by_key",
                return_value={"id": "role-custom", "key": "custom:buyer"},
            ) as get_role,
            mock.patch.object(
                roles_store.console_store,
                "_get_member_with_cursor",
                return_value=member,
            ) as get_member,
            mock.patch.object(
                roles_store, "set_membership_role_resolved", return_value=True
            ) as set_role,
        ):
            order.attach_mock(get_role, "role")
            order.attach_mock(get_member, "member")
            order.attach_mock(set_role, "update")
            out = roles_store.assign_role(
                tenant_id="tenant-a",
                actor_id="owner-1",
                target_user_id="user-1",
                role_key="custom:buyer",
            )
        self.assertTrue(out["ok"])
        self.assertEqual(
            [call[0] for call in order.mock_calls],
            ["role", "member", "update"],
        )
        get_member.assert_called_once_with(cur, "tenant-a", "user-1", for_update=True)
        self.assertIs(set_role.call_args.args[0], cur)
        self.assertEqual(set_role.call_args.kwargs["role_id"], "role-custom")


class UpdateRoleVersionTests(unittest.TestCase):
    def test_expected_version_is_part_of_the_update_compare_and_swap(self):
        cur = mock.Mock(rowcount=1)
        cm = mock.MagicMock()
        cm.__enter__.return_value = cur
        cm.__exit__.return_value = False
        current = {"id": "role-1", "version": 7}
        updated = {"id": "role-1", "version": 8}
        with (
            mock.patch.object(roles_store, "get_custom_role", side_effect=[current, updated]),
            mock.patch.object(roles_store.db, "get_cursor", return_value=cm),
        ):
            out = roles_store.update_custom_role(
                tenant_id="tenant-a",
                role_id="role-1",
                display_name="Buyer",
                expected_version=7,
            )
        self.assertTrue(out["ok"])
        sql, params = cur.execute.call_args.args
        self.assertIn("AND version = %s", sql)
        self.assertEqual(params[-1], 7)

    def test_lost_compare_and_swap_reports_conflict_when_role_still_exists(self):
        cur = mock.Mock(rowcount=0)
        cur.fetchone.return_value = {"?column?": 1}
        cm = mock.MagicMock()
        cm.__enter__.return_value = cur
        cm.__exit__.return_value = False
        with (
            mock.patch.object(
                roles_store, "get_custom_role", return_value={"id": "role-1", "version": 7}
            ),
            mock.patch.object(roles_store.db, "get_cursor", return_value=cm),
        ):
            out = roles_store.update_custom_role(
                tenant_id="tenant-a",
                role_id="role-1",
                is_active=False,
                expected_version=7,
            )
        self.assertEqual(out, {"error": "team.role_version_conflict"})


if __name__ == "__main__":
    unittest.main()

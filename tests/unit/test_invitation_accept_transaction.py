# -*- coding: utf-8 -*-
"""Invitation acceptance transaction, role, and workspace isolation contracts."""

import unittest
from unittest import mock

from services.team import invitations


class _CursorContext:
    def __init__(self, cur):
        self.cur = cur
        self.exc_type = None

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc, traceback):
        self.exc_type = exc_type
        return False


class _AcceptCursor:
    def __init__(self, *, active_workspace_ids=(), consume_rowcount=1):
        self.active_workspace_ids = list(active_workspace_ids)
        self.consume_rowcount = consume_rowcount
        self.calls = []
        self.current = None
        self.rowcount = 0

    def execute(self, sql, params=None):
        compact = " ".join(sql.split())
        self.calls.append((compact, params))
        self.rowcount = 0
        if compact.startswith("SELECT id FROM workspace_clients"):
            self.current = "workspace"
        elif compact.startswith("SELECT 1 FROM users WHERE username"):
            self.current = None
        elif compact.startswith("SELECT tenant_id FROM users WHERE LOWER(email)"):
            self.current = None
        elif compact.startswith("SELECT name FROM tenants"):
            self.current = {"name": "Tenant A"}
        elif compact.startswith("INSERT INTO users"):
            self.current = {"id": "user-new"}
        elif compact.startswith("SELECT id FROM memberships"):
            self.current = {"id": "membership-new"}
        elif compact.startswith("UPDATE invitations SET accepted_at"):
            self.current = None
            self.rowcount = self.consume_rowcount
        else:
            self.current = None

    def fetchone(self):
        return self.current if self.current != "workspace" else None

    def fetchall(self):
        if self.current == "workspace":
            return [{"id": workspace_id} for workspace_id in self.active_workspace_ids]
        return []


def _pending_custom_invitation(*, workspace_ids=None, scope_mode="assigned"):
    return {
        "id": "invite-1",
        "status": "pending",
        "tenant_id": "tenant-a",
        "invited_by": "owner-1",
        "role_key": "custom:buyer",
        "role_name": "Purchasing Clerk",
        "scope_mode": scope_mode,
        "workspace_ids": workspace_ids if workspace_ids is not None else [11, 12],
        "email": None,
    }


class AcceptTransactionTests(unittest.TestCase):
    def _patch_accept(self, cur, invitation, *, membership_ok, inviter_authz=mock.DEFAULT):
        cm = _CursorContext(cur)
        if inviter_authz is mock.DEFAULT:
            inviter_authz = invitations.Authz(
                role_key="owner",
                permissions=invitations.ROLE_PERMISSIONS["owner"],
                membership_id="membership-owner",
            )
        patches = (
            mock.patch.object(invitations.db, "get_cursor", return_value=cm),
            mock.patch.object(invitations, "_find_by_token_with_cursor", return_value=invitation),
            mock.patch.object(
                invitations, "erp_shared_express_endpoint_enabled_for", return_value=True
            ),
            mock.patch.object(invitations, "create_membership", return_value=membership_ok),
            mock.patch.object(invitations.bcrypt, "gensalt", return_value=b"salt"),
            mock.patch.object(invitations.bcrypt, "hashpw", return_value=b"hashed"),
            mock.patch.object(
                invitations.roles_store,
                "get_active_custom_role_by_key",
                return_value={
                    "id": "role-custom",
                    "key": "custom:buyer",
                    "role_name": "Purchasing Clerk",
                    "permissions": ["purchase.doc.create"],
                },
            ),
            mock.patch.object(invitations, "_current_inviter_authz", return_value=inviter_authz),
        )
        return cm, patches

    def test_membership_failure_rolls_back_user_and_does_not_consume_invite(self):
        cur = _AcceptCursor(active_workspace_ids=[11, 12])
        invitation = _pending_custom_invitation()
        cm, patches = self._patch_accept(cur, invitation, membership_ok=False)
        with (
            patches[0],
            patches[1] as locked,
            patches[2],
            patches[3],
            patches[4],
            patches[5],
            patches[6],
            patches[7],
        ):
            out = invitations.accept("token", username="new-user", password="Zz12345678")
        self.assertEqual(out, {"error": "invite.role_not_allowed"})
        self.assertIs(cm.exc_type, invitations._RoleNotAssignable)
        self.assertEqual(
            locked.call_args_list,
            [mock.call(cur, "token"), mock.call(cur, "token", lock=True)],
        )
        self.assertTrue(any(sql.startswith("INSERT INTO users") for sql, _ in cur.calls))
        self.assertFalse(
            any(sql.startswith("UPDATE invitations SET accepted_at") for sql, _ in cur.calls)
        )
        self.assertFalse(any(sql.startswith("INSERT INTO member_scopes") for sql, _ in cur.calls))

    def test_success_preserves_scope_and_consumes_invite_conditionally(self):
        cur = _AcceptCursor(active_workspace_ids=[11, 12])
        invitation = _pending_custom_invitation()
        cm, patches = self._patch_accept(cur, invitation, membership_ok=True)
        with (
            patches[0],
            patches[1] as locked,
            patches[2],
            patches[3] as create_membership,
            patches[4],
            patches[5],
            patches[6],
            patches[7],
        ):
            out = invitations.accept("token", username="new-user", password="Zz12345678")
        self.assertTrue(out["ok"])
        self.assertEqual(out["role_name"], "Purchasing Clerk")
        self.assertIsNone(cm.exc_type)
        self.assertEqual(
            locked.call_args_list,
            [mock.call(cur, "token"), mock.call(cur, "token", lock=True)],
        )
        self.assertTrue(create_membership.call_args.kwargs["allow_custom"])
        self.assertFalse(create_membership.call_args.kwargs["allow_owner"])
        self.assertEqual(create_membership.call_args.kwargs["scope_mode"], "assigned")
        scope_params = [
            params for sql, params in cur.calls if sql.startswith("INSERT INTO member_scopes")
        ]
        self.assertEqual(
            scope_params,
            [
                ("tenant-a", "membership-new", 11, "owner-1"),
                ("tenant-a", "membership-new", 12, "owner-1"),
            ],
        )
        consume_sql = next(
            sql for sql, _ in cur.calls if sql.startswith("UPDATE invitations SET accepted_at")
        )
        self.assertIn("accepted_at IS NULL", consume_sql)
        self.assertIn("revoked_at IS NULL", consume_sql)
        self.assertIn("expires_at > NOW()", consume_sql)

    def test_stale_or_cross_tenant_workspace_rolls_back_before_user_creation(self):
        cur = _AcceptCursor(active_workspace_ids=[11])
        invitation = _pending_custom_invitation(workspace_ids=[11, 22])
        cm, patches = self._patch_accept(cur, invitation, membership_ok=True)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3] as create_membership,
            patches[4],
            patches[5],
            patches[6],
            patches[7],
        ):
            out = invitations.accept("token", username="new-user", password="Zz12345678")
        self.assertEqual(out, {"error": "team.scope_invalid"})
        self.assertIs(cm.exc_type, invitations._WorkspaceScopeNotAssignable)
        create_membership.assert_not_called()
        self.assertFalse(any(sql.startswith("INSERT INTO users") for sql, _ in cur.calls))

    def test_conditional_consume_race_rolls_back_membership_and_user(self):
        cur = _AcceptCursor(consume_rowcount=0)
        invitation = _pending_custom_invitation(workspace_ids=[], scope_mode="all")
        cm, patches = self._patch_accept(cur, invitation, membership_ok=True)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
            patches[6],
            patches[7],
        ):
            out = invitations.accept("token", username="new-user", password="Zz12345678")
        self.assertEqual(out, {"error": "invite.expired"})
        self.assertIs(cm.exc_type, invitations._InvitationNotConsumable)

    def test_flag_off_custom_invite_cannot_create_user(self):
        cur = _AcceptCursor(active_workspace_ids=[11, 12])
        invitation = _pending_custom_invitation()
        cm = _CursorContext(cur)
        with (
            mock.patch.object(invitations.db, "get_cursor", return_value=cm),
            mock.patch.object(invitations, "_find_by_token_with_cursor", return_value=invitation),
            mock.patch.object(
                invitations, "erp_shared_express_endpoint_enabled_for", return_value=False
            ),
        ):
            out = invitations.accept("token", username="new-user", password="Zz12345678")
        self.assertEqual(out, {"error": "invite.role_not_allowed"})
        self.assertFalse(any(sql.startswith("INSERT INTO users") for sql, _ in cur.calls))

    def test_forged_owner_invite_cannot_create_user_or_membership(self):
        cur = _AcceptCursor()
        invitation = _pending_custom_invitation(workspace_ids=[], scope_mode="all")
        invitation.update({"role_key": "owner", "role_name": "Owner"})
        cm, patches = self._patch_accept(cur, invitation, membership_ok=True)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3] as create_membership,
            patches[4],
            patches[5],
            patches[6] as active_role,
            patches[7],
        ):
            out = invitations.accept("token", username="new-user", password="Zz12345678")
        self.assertEqual(out, {"error": "invite.role_not_allowed"})
        self.assertIs(cm.exc_type, invitations._RoleNotAssignable)
        create_membership.assert_not_called()
        active_role.assert_not_called()
        self.assertFalse(any(sql.startswith("INSERT INTO users") for sql, _ in cur.calls))

    def test_admin_invite_remains_assignable_without_owner_override(self):
        cur = _AcceptCursor()
        invitation = _pending_custom_invitation(workspace_ids=[], scope_mode="all")
        invitation.update({"role_key": "admin", "role_name": "Admin"})
        cm, patches = self._patch_accept(cur, invitation, membership_ok=True)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3] as create_membership,
            patches[4],
            patches[5],
            patches[6] as active_role,
            patches[7],
        ):
            out = invitations.accept("token", username="new-user", password="Zz12345678")
        self.assertTrue(out["ok"])
        self.assertFalse(create_membership.call_args.kwargs["allow_custom"])
        self.assertFalse(create_membership.call_args.kwargs["allow_owner"])
        active_role.assert_not_called()

    def test_revoked_old_token_cannot_bind_to_recreated_same_key(self):
        cur = _AcceptCursor()
        invitation = _pending_custom_invitation(workspace_ids=[], scope_mode="all")
        invitation["status"] = "revoked"
        cm, patches = self._patch_accept(cur, invitation, membership_ok=True)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3] as create_membership,
            patches[4],
            patches[5],
            patches[6],
            patches[7],
        ):
            out = invitations.accept("old-token", username="new-user", password="Zz12345678")
        self.assertEqual(out, {"error": "invite.revoked"})
        create_membership.assert_not_called()
        self.assertFalse(any(sql.startswith("INSERT INTO users") for sql, _ in cur.calls))

    def test_accept_revalidates_current_inviter_permission_ceiling_and_scope(self):
        invitation = _pending_custom_invitation()
        cases = (
            (
                "removed_or_inactive",
                None,
            ),
            (
                "lost_invite_permission",
                invitations.Authz(
                    role_key="custom:inviter",
                    permissions=frozenset({"purchase.doc.create"}),
                    membership_id="membership-inviter",
                ),
            ),
            (
                "target_now_exceeds_inviter",
                invitations.Authz(
                    role_key="custom:inviter",
                    permissions=frozenset({"team.member.invite"}),
                    membership_id="membership-inviter",
                ),
            ),
            (
                "workspace_scope_shrunk",
                invitations.Authz(
                    role_key="custom:inviter",
                    permissions=frozenset({"team.member.invite", "team.member.edit_role"}),
                    scope_mode="assigned",
                    membership_id="membership-inviter",
                    workspace_ids=frozenset({11}),
                ),
            ),
        )
        for label, inviter_authz in cases:
            with self.subTest(label=label):
                cur = _AcceptCursor(active_workspace_ids=[11, 12])
                cm, patches = self._patch_accept(
                    cur,
                    invitation,
                    membership_ok=True,
                    inviter_authz=inviter_authz,
                )
                with (
                    patches[0],
                    patches[1],
                    patches[2],
                    patches[3] as create_membership,
                    patches[4],
                    patches[5],
                    patches[6],
                    patches[7],
                ):
                    out = invitations.accept("token", username="new-user", password="Zz12345678")
                self.assertEqual(out, {"error": "invite.role_not_allowed"})
                self.assertIs(cm.exc_type, invitations._RoleNotAssignable)
                create_membership.assert_not_called()
                self.assertFalse(any(sql.startswith("INSERT INTO users") for sql, _ in cur.calls))


class CurrentInviterLookupTests(unittest.TestCase):
    class _Cursor:
        def __init__(self, *user_rows, events=None):
            self.user_rows = list(user_rows)
            self.calls = []
            self.events = events

        def execute(self, sql, params=None):
            compact = " ".join(sql.split())
            self.calls.append((compact, params))
            if self.events is not None:
                self.events.append("user_lock" if "FOR SHARE" in compact else "user_read")

        def fetchone(self):
            return self.user_rows.pop(0) if self.user_rows else None

    def test_inactive_or_missing_inviter_is_rejected_before_role_resolution(self):
        cur = self._Cursor(None)
        with mock.patch.object(invitations, "resolve") as resolve:
            out = invitations._current_inviter_authz(
                cur, {"tenant_id": "tenant-a", "invited_by": "owner-1"}
            )
        self.assertIsNone(out)
        resolve.assert_not_called()
        self.assertEqual(len(cur.calls), 1)
        self.assertIn("tenant_id = %s::uuid", cur.calls[0][0])
        self.assertIn("is_active = TRUE", cur.calls[0][0])
        self.assertNotIn("FOR SHARE", cur.calls[0][0])

    def test_removed_membership_cannot_fall_back_to_legacy_role(self):
        user = {
            "id": "owner-1",
            "tenant_id": "tenant-a",
            "role": "owner",
            "invited_by": None,
            "is_active": True,
        }
        cur = self._Cursor(user)
        fallback = invitations.Authz(
            role_key="owner",
            permissions=invitations.ROLE_PERMISSIONS["owner"],
            membership_id=None,
        )
        with mock.patch.object(invitations, "resolve", return_value=fallback) as resolve:
            out = invitations._current_inviter_authz(
                cur, {"tenant_id": "tenant-a", "invited_by": "owner-1"}
            )
        self.assertIsNone(out)
        self.assertEqual(len(cur.calls), 1)
        self.assertNotIn("FOR SHARE", cur.calls[0][0])
        resolve.assert_called_once_with(user, cur=cur, lock=True)

    def test_membership_and_role_lock_precede_final_user_lock(self):
        user = {
            "id": "owner-1",
            "tenant_id": "tenant-a",
            "role": "owner",
            "invited_by": None,
            "is_active": True,
        }
        events = []
        cur = self._Cursor(user, user, events=events)
        current = invitations.Authz(
            role_key="owner",
            permissions=invitations.ROLE_PERMISSIONS["owner"],
            membership_id="membership-owner",
        )

        def resolve_after_user_read(resolved_user, *, cur, lock):
            self.assertEqual(resolved_user, user)
            self.assertTrue(lock)
            events.append("membership_role_lock")
            return current

        with mock.patch.object(
            invitations, "resolve", side_effect=resolve_after_user_read
        ) as resolve:
            out = invitations._current_inviter_authz(
                cur, {"tenant_id": "tenant-a", "invited_by": "owner-1"}
            )

        self.assertIs(out, current)
        self.assertEqual(events, ["user_read", "membership_role_lock", "user_lock"])
        self.assertEqual(len(cur.calls), 2)
        self.assertNotIn("FOR SHARE", cur.calls[0][0])
        self.assertIn("FOR SHARE", cur.calls[1][0])
        resolve.assert_called_once()


if __name__ == "__main__":
    unittest.main()

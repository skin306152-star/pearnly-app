# -*- coding: utf-8 -*-
"""邀请生命周期纯逻辑守门:token 哈希 / 状态派生 / 角色白名单 / 接受拒绝分支
(docs/permissions/01 · 04 接受流四态)。"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from services.team import invitations


def _owner():
    return {"id": "u", "tenant_id": "t", "role": "owner", "invited_by": None}


def _row(**kw):
    base = {
        "revoked_at": None,
        "accepted_at": None,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
    }
    base.update(kw)
    return base


class TokenHashTests(unittest.TestCase):
    def test_sha256_hex_only_no_plaintext(self):
        h = invitations.hash_token("secret-token")
        self.assertEqual(len(h), 64)
        self.assertNotIn("secret", h)

    def test_deterministic(self):
        self.assertEqual(invitations.hash_token("a"), invitations.hash_token("a"))
        self.assertNotEqual(invitations.hash_token("a"), invitations.hash_token("b"))


class StatusDerivationTests(unittest.TestCase):
    def test_pending(self):
        self.assertEqual(invitations._status(_row()), "pending")

    def test_expired(self):
        row = _row(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
        self.assertEqual(invitations._status(row), "expired")

    def test_accepted(self):
        self.assertEqual(
            invitations._status(_row(accepted_at=datetime.now(timezone.utc))), "accepted"
        )

    def test_revoked_wins_over_accepted(self):
        row = _row(revoked_at=datetime.now(timezone.utc), accepted_at=datetime.now(timezone.utc))
        self.assertEqual(invitations._status(row), "revoked")


class CreateGuardTests(unittest.TestCase):
    def test_line_channel_is_rejected_before_db(self):
        out = invitations.create_invitation(
            tenant_id="t",
            invited_by="u",
            channel="line",
            target="LINE contact",
            role_key="viewer",
            inviter=_owner(),
        )
        self.assertEqual(out, {"error": "invite.channel_not_supported"})

    def test_owner_role_rejected_without_db(self):
        out = invitations.create_invitation(
            tenant_id="t",
            invited_by="u",
            channel="email",
            target="a@b.c",
            role_key="owner",
            inviter=_owner(),
        )
        self.assertIsNone(out)

    def test_cashier_role_rejected(self):
        out = invitations.create_invitation(
            tenant_id="t",
            invited_by="u",
            channel="email",
            target="a@b.c",
            role_key="cashier",
            inviter=_owner(),
        )
        self.assertIsNone(out)

    def test_assigned_scope_rejected_for_admin(self):
        out = invitations.create_invitation(
            tenant_id="t",
            invited_by="u",
            channel="email",
            target="a@b.c",
            role_key="admin",
            scope_mode="assigned",
            workspace_ids=[1],
            inviter=_owner(),
        )
        self.assertIsNone(out)


class AcceptEmailGuardTests(unittest.TestCase):
    """邮箱碰撞分支(04 接受流):已注册且归属公司 → 明确码;无租户孤号 → 通用码。"""

    def _accept_with_email_owner_row(self, row):
        class _Cur:
            _email_q = False

            def execute(self, sql, params=None):
                self._email_q = "LOWER(email)" in sql

            def fetchone(self):
                # username 查重未命中(None);email 查重命中 row → 早返,不会走到 INSERT
                return row if self._email_q else None

        class _CM:
            def __enter__(self):
                return _Cur()

            def __exit__(self, *a):
                return False

        inv = {
            "status": "pending",
            "tenant_id": "t1",
            "invited_by": "u0",
            "role_key": "viewer",
            "scope_mode": "all",
            "id": "i1",
            "email": "boss@x.co",
        }
        inv["role_name"] = "Viewer"
        authz = invitations.Authz(
            role_key="owner",
            permissions=invitations.ROLE_PERMISSIONS["owner"],
            membership_id="membership-owner",
        )
        with (
            mock.patch.object(invitations, "_find_by_token_with_cursor", return_value=inv),
            mock.patch.object(invitations, "_current_inviter_authz", return_value=authz),
            mock.patch.object(invitations.db, "get_cursor", lambda *a, **k: _CM()),
        ):
            return invitations.accept("tok", username="newuser", password="Zz12345678")

    def test_account_exists_other_tenant_code(self):
        out = self._accept_with_email_owner_row({"tenant_id": "other-tenant"})
        self.assertEqual(out["error"], "invite.account_exists_other_tenant")

    def test_orphan_account_keeps_generic_code(self):
        out = self._accept_with_email_owner_row({"tenant_id": None})
        self.assertEqual(out["error"], "team.email_exists")


class RoleInvitationGuardTests(unittest.TestCase):
    def test_flag_off_preserves_system_role_only_allowlist(self):
        with mock.patch.object(
            invitations, "erp_shared_express_endpoint_enabled_for", return_value=False
        ):
            for role_key in ("admin", "accountant", "clerk", "viewer"):
                self.assertTrue(invitations.role_key_allowed_for_invitation("tenant-a", role_key))
            for role_key in ("owner", "cashier", "custom:buyer"):
                self.assertFalse(invitations.role_key_allowed_for_invitation("tenant-a", role_key))

    def test_system_roles_do_not_read_f1_flag(self):
        with mock.patch.object(
            invitations,
            "erp_shared_express_endpoint_enabled_for",
            side_effect=AssertionError("system-role path must remain dormant"),
        ):
            self.assertTrue(invitations.role_key_allowed_for_invitation("tenant-a", "viewer"))

    def test_workspace_json_text_is_normalized_for_legacy_rows(self):
        self.assertEqual(invitations._normalized_workspace_ids("[11, 11, 12]"), [11, 12])


class InvitationAuthorityTests(unittest.TestCase):
    def _authz(self, permissions, *, scope_mode="all", workspace_ids=None):
        return invitations.Authz(
            role_key="custom:inviter",
            permissions=frozenset(permissions),
            scope_mode=scope_mode,
            workspace_ids=(frozenset(workspace_ids or []) if scope_mode == "assigned" else None),
        )

    def test_invite_only_actor_cannot_invite_admin_or_higher_custom_role(self):
        actor = self._authz({"team.member.invite", "purchase.doc.view"})
        for target in (
            invitations.ROLE_PERMISSIONS["admin"],
            frozenset({"purchase.doc.view", "purchase.doc.approve"}),
        ):
            with self.subTest(target=target):
                self.assertEqual(
                    invitations._invitation_authority_error(
                        actor,
                        target_permissions=frozenset(target),
                        scope_mode="all",
                        workspace_ids=[],
                    ),
                    "invite.role_not_allowed",
                )

    def test_invite_only_actor_can_invite_equal_or_lower_permissions(self):
        actor = self._authz({"team.member.invite", "purchase.doc.view", "purchase.doc.create"})
        self.assertIsNone(
            invitations._invitation_authority_error(
                actor,
                target_permissions=frozenset({"team.member.invite", "purchase.doc.view"}),
                scope_mode="all",
                workspace_ids=[],
            )
        )

    def test_edit_role_allows_any_non_owner_target_within_actor_scope(self):
        actor = self._authz({"team.member.invite", "team.member.edit_role"})
        self.assertIsNone(
            invitations._invitation_authority_error(
                actor,
                target_permissions=invitations.ROLE_PERMISSIONS["admin"],
                scope_mode="all",
                workspace_ids=[],
            )
        )

    def test_assigned_actor_cannot_expand_to_all_or_outside_workspace_subset(self):
        actor = self._authz(
            {"team.member.invite", "team.member.edit_role"},
            scope_mode="assigned",
            workspace_ids={11, 12},
        )
        self.assertEqual(
            invitations._invitation_authority_error(
                actor,
                target_permissions=invitations.ROLE_PERMISSIONS["admin"],
                scope_mode="all",
                workspace_ids=[],
            ),
            "team.scope_invalid",
        )
        self.assertIsNone(
            invitations._invitation_authority_error(
                actor,
                target_permissions=frozenset({"purchase.doc.create"}),
                scope_mode="assigned",
                workspace_ids=[11],
            )
        )
        self.assertEqual(
            invitations._invitation_authority_error(
                actor,
                target_permissions=frozenset({"purchase.doc.create"}),
                scope_mode="assigned",
                workspace_ids=[11, 22],
            ),
            "team.scope_invalid",
        )

    def test_owner_and_admin_keep_normal_admin_invitation_authority(self):
        for role_key in ("owner", "admin"):
            with self.subTest(role_key=role_key):
                actor = invitations.Authz(
                    role_key=role_key,
                    permissions=invitations.ROLE_PERMISSIONS[role_key],
                )
                self.assertIsNone(
                    invitations._invitation_authority_error(
                        actor,
                        target_permissions=invitations.ROLE_PERMISSIONS["admin"],
                        scope_mode="all",
                        workspace_ids=[],
                    )
                )


class _CreateCursor:
    def __init__(self, active_workspace_ids=()):
        self.active_workspace_ids = list(active_workspace_ids)
        self.calls = []
        self.current = None

    def execute(self, sql, params=None):
        compact = " ".join(sql.split())
        self.calls.append((compact, params))
        if compact.startswith("INSERT INTO invitations"):
            now = datetime.now(timezone.utc)
            self.current = {
                "id": "invite-1",
                "created_at": now,
                "expires_at": now + timedelta(days=7),
            }
        else:
            self.current = None

    def fetchall(self):
        return [{"id": workspace_id} for workspace_id in self.active_workspace_ids]

    def fetchone(self):
        return self.current


class _CursorContext:
    def __init__(self, cur):
        self.cur = cur
        self.exc_type = None

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc, traceback):
        self.exc_type = exc_type
        return False


class CreateCustomInvitationTests(unittest.TestCase):
    def _create(
        self,
        cur,
        *,
        workspace_ids,
        actor_authz=None,
        role_permissions=None,
    ):
        role = {
            "id": "role-1",
            "key": "custom:buyer",
            "role_name": "Purchasing Clerk",
            "permissions": role_permissions or ["purchase.doc.create"],
        }
        owner = invitations.Authz(
            role_key="owner", permissions=invitations.ROLE_PERMISSIONS["owner"]
        )
        with (
            mock.patch.object(
                invitations, "erp_shared_express_endpoint_enabled_for", return_value=True
            ),
            mock.patch.object(
                invitations.roles_store, "get_active_custom_role_by_key", return_value=role
            ),
            mock.patch.object(invitations, "resolve", return_value=actor_authz or owner) as resolve,
            mock.patch.object(invitations.db, "get_cursor", return_value=_CursorContext(cur)),
        ):
            out = invitations.create_invitation(
                tenant_id="tenant-a",
                invited_by="owner-1",
                channel="email",
                target="buyer@example.com",
                role_key="custom:buyer",
                scope_mode="assigned",
                workspace_ids=workspace_ids,
                inviter={
                    "id": "owner-1",
                    "tenant_id": "tenant-a",
                    "role": "owner",
                    "invited_by": None,
                },
            )
        resolve.assert_called_once_with(mock.ANY, cur=cur, lock=True)
        return out

    def test_all_workspaces_are_active_and_tenant_scoped_before_insert(self):
        cur = _CreateCursor(active_workspace_ids=[11])
        out = self._create(cur, workspace_ids=[11, 22])
        self.assertEqual(out, {"error": "team.scope_invalid"})
        self.assertFalse(any(sql.startswith("INSERT INTO invitations") for sql, _ in cur.calls))
        workspace_sql, params = cur.calls[-1]
        self.assertIn("tenant_id = %s", workspace_sql)
        self.assertIn("is_active = TRUE", workspace_sql)
        self.assertIn("FOR SHARE", workspace_sql)
        self.assertEqual(params, ("tenant-a", [11, 22]))

    def test_valid_custom_role_keeps_name_and_assigned_workspaces(self):
        cur = _CreateCursor(active_workspace_ids=[11, 12])
        out = self._create(cur, workspace_ids=[11, 11, 12])
        self.assertEqual(out["role_name"], "Purchasing Clerk")
        self.assertEqual(out["workspace_ids"], [11, 12])
        self.assertTrue(any(sql.startswith("INSERT INTO invitations") for sql, _ in cur.calls))

    def test_inactive_or_cross_tenant_custom_role_cannot_create_invite(self):
        cur = _CreateCursor(active_workspace_ids=[11])
        with (
            mock.patch.object(
                invitations, "erp_shared_express_endpoint_enabled_for", return_value=True
            ),
            mock.patch.object(
                invitations.roles_store, "get_active_custom_role_by_key", return_value=None
            ),
            mock.patch.object(invitations.db, "get_cursor", return_value=_CursorContext(cur)),
        ):
            out = invitations.create_invitation(
                tenant_id="tenant-a",
                invited_by="owner-1",
                channel="email",
                target="buyer@example.com",
                role_key="custom:buyer",
                scope_mode="assigned",
                workspace_ids=[11],
                inviter={
                    "id": "owner-1",
                    "tenant_id": "tenant-a",
                    "role": "owner",
                    "invited_by": None,
                },
            )
        self.assertIsNone(out)
        self.assertFalse(any(sql.startswith("INSERT INTO invitations") for sql, _ in cur.calls))

    def test_invite_only_actor_cannot_persist_higher_custom_role(self):
        cur = _CreateCursor(active_workspace_ids=[11])
        actor = invitations.Authz(
            role_key="custom:inviter",
            permissions=frozenset({"team.member.invite", "purchase.doc.view"}),
        )
        out = self._create(
            cur,
            workspace_ids=[11],
            actor_authz=actor,
            role_permissions=["purchase.doc.view", "purchase.doc.approve"],
        )
        self.assertEqual(out, {"error": "invite.role_not_allowed"})
        self.assertFalse(any(sql.startswith("INSERT INTO invitations") for sql, _ in cur.calls))

    def test_assigned_actor_can_persist_only_workspace_subset(self):
        actor = invitations.Authz(
            role_key="custom:manager",
            permissions=frozenset({"team.member.invite", "team.member.edit_role"}),
            scope_mode="assigned",
            workspace_ids=frozenset({11, 12}),
        )
        allowed_cur = _CreateCursor(active_workspace_ids=[11])
        allowed = self._create(allowed_cur, workspace_ids=[11], actor_authz=actor)
        self.assertTrue(allowed["id"])

        denied_cur = _CreateCursor(active_workspace_ids=[11, 22])
        denied = self._create(denied_cur, workspace_ids=[11, 22], actor_authz=actor)
        self.assertEqual(denied, {"error": "team.scope_invalid"})
        self.assertFalse(
            any(sql.startswith("INSERT INTO invitations") for sql, _ in denied_cur.calls)
        )

    def test_invite_only_actor_cannot_persist_admin_invitation(self):
        cur = _CreateCursor()
        actor = invitations.Authz(
            role_key="custom:inviter",
            permissions=frozenset({"team.member.invite"}),
        )
        inviter = {
            "id": "user-1",
            "tenant_id": "tenant-a",
            "role": "member",
            "invited_by": "owner-1",
        }
        with (
            mock.patch.object(invitations.db, "get_cursor", return_value=_CursorContext(cur)),
            mock.patch.object(invitations, "resolve", return_value=actor),
        ):
            out = invitations.create_invitation(
                tenant_id="tenant-a",
                invited_by="user-1",
                channel="email",
                target="admin@example.com",
                role_key="admin",
                inviter=inviter,
            )
        self.assertEqual(out, {"error": "invite.role_not_allowed"})
        self.assertFalse(any(sql.startswith("INSERT INTO invitations") for sql, _ in cur.calls))


class TokenLookupContractTests(unittest.TestCase):
    def test_locking_lookup_returns_real_custom_role_name(self):
        row = _row(
            id="invite-1",
            tenant_id="tenant-a",
            role_key="custom:buyer",
            role_display_name="Purchasing Clerk",
            role_db_name="custom:tenant-a:buyer",
        )

        class _Cur:
            def execute(self, sql, params=None):
                self.sql = " ".join(sql.split())
                self.params = params

            def fetchone(self):
                return row

        cur = _Cur()
        out = invitations._find_by_token_with_cursor(cur, "token", lock=True)
        self.assertEqual(out["role_name"], "Purchasing Clerk")
        self.assertIn("r.tenant_id = i.tenant_id", cur.sql)
        self.assertIn("FOR UPDATE OF i", cur.sql)

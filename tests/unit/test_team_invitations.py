# -*- coding: utf-8 -*-
"""邀请生命周期纯逻辑守门:token 哈希 / 状态派生 / 角色白名单 / 接受拒绝分支
(docs/permissions/01 · 04 接受流四态)。"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from services.team import invitations


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
    def test_owner_role_rejected_without_db(self):
        out = invitations.create_invitation(
            tenant_id="t",
            invited_by="u",
            channel="email",
            target="a@b.c",
            role_key="owner",
        )
        self.assertIsNone(out)

    def test_cashier_role_rejected(self):
        out = invitations.create_invitation(
            tenant_id="t",
            invited_by="u",
            channel="email",
            target="a@b.c",
            role_key="cashier",
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
        with mock.patch.object(invitations, "find_by_token", return_value=inv):
            with mock.patch.object(invitations.db, "get_cursor", lambda *a, **k: _CM()):
                return invitations.accept("tok", username="newuser", password="Zz12345678")

    def test_account_exists_other_tenant_code(self):
        out = self._accept_with_email_owner_row({"tenant_id": "other-tenant"})
        self.assertEqual(out["error"], "invite.account_exists_other_tenant")

    def test_orphan_account_keeps_generic_code(self):
        out = self._accept_with_email_owner_row({"tenant_id": None})
        self.assertEqual(out["error"], "team.email_exists")

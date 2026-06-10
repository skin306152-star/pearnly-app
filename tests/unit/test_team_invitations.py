# -*- coding: utf-8 -*-
"""邀请生命周期纯逻辑守门:token 哈希 / 状态派生 / 角色白名单(docs/permissions/01)。"""

import unittest
from datetime import datetime, timedelta, timezone

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
        h = invitations._hash("secret-token")
        self.assertEqual(len(h), 64)
        self.assertNotIn("secret", h)

    def test_deterministic(self):
        self.assertEqual(invitations._hash("a"), invitations._hash("a"))
        self.assertNotEqual(invitations._hash("a"), invitations._hash("b"))


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

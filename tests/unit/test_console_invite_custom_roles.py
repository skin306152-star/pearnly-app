# -*- coding: utf-8 -*-
"""Custom-role invitation route contracts: role names, input bounds, and email escaping."""

import asyncio
import unittest
from unittest import mock

from pydantic import ValidationError

from routes import console_invite_routes
from routes.console_invite_routes import InvitationAccept, InvitationCreate
from services.team import invitations


def _pending_custom_invitation():
    return {
        "id": "invite-1",
        "status": "pending",
        "tenant_id": "tenant-a",
        "tenant_name": "Tenant A",
        "invited_by": "owner-1",
        "role_key": "custom:buyer",
        "role_name": "Purchasing Clerk",
        "scope_mode": "all",
        "workspace_ids": [],
        "email": None,
    }


class RouteRoleNameContractTests(unittest.TestCase):
    def test_invitation_model_accepts_existing_custom_role_key_contract(self):
        key = "custom:" + "a" * 40
        self.assertEqual(
            InvitationCreate(channel="email", target="a@b.co", role_key=key).role_key,
            key,
        )
        with self.assertRaises(ValidationError):
            InvitationCreate(channel="email", target="a@b.co", role_key="x" * 65)

    def test_preview_returns_real_role_name(self):
        with mock.patch.object(
            console_invite_routes.inv_store,
            "find_by_token",
            return_value=_pending_custom_invitation(),
        ):
            out = asyncio.run(console_invite_routes.preview_invitation("token"))
        self.assertEqual(out["role_name"], "Purchasing Clerk")

    def test_email_receives_real_role_name(self):
        user = {
            "tenant_id": "tenant-a",
            "id": "owner-1",
            "plan": "credits",
            "company_name": "Tenant A",
        }
        req = InvitationCreate(channel="email", target="buyer@example.com", role_key="custom:buyer")
        request = mock.Mock(headers={"host": "localhost"})
        created = {
            "id": "invite-1",
            "token": "token",
            "expires_at": "2026-09-01T00:00:00+00:00",
            "role_name": "Purchasing Clerk",
        }
        with (
            mock.patch.object(console_invite_routes, "require_perm", return_value=user),
            mock.patch.object(
                console_invite_routes.inv_store,
                "role_key_allowed_for_invitation",
                return_value=True,
            ),
            mock.patch.object(
                console_invite_routes.console_store,
                "seat_usage",
                return_value={"used": 1},
            ),
            mock.patch.object(
                console_invite_routes.inv_store, "create_invitation", return_value=created
            ),
            mock.patch.object(
                console_invite_routes.inv_store, "send_invite_email", return_value=True
            ) as send_email,
            mock.patch.object(console_invite_routes, "_log_op"),
        ):
            out = asyncio.run(console_invite_routes.create_invitation(req, request))
        self.assertEqual(out["role_name"], "Purchasing Clerk")
        self.assertEqual(send_email.call_args.args[-1], "Purchasing Clerk")

    def test_accept_returns_and_audits_real_role_name(self):
        req = InvitationAccept(username="new-user", password="Zz12345678")
        request = mock.Mock()
        accepted = {
            "ok": True,
            "tenant_id": "tenant-a",
            "user_id": "user-new",
            "role_key": "custom:buyer",
            "role_name": "Purchasing Clerk",
        }
        with (
            mock.patch.object(console_invite_routes, "_check_password_strength", return_value=None),
            mock.patch.object(console_invite_routes.inv_store, "accept", return_value=accepted),
            mock.patch("core.db.insert_operation_log") as audit,
        ):
            out = asyncio.run(console_invite_routes.accept_invitation("token", req, request))
        self.assertEqual(out["role_name"], "Purchasing Clerk")
        self.assertEqual(audit.call_args.kwargs["details"]["role_name"], "Purchasing Clerk")


class InviteEmailEscapingTests(unittest.TestCase):
    def test_custom_role_name_is_html_escaped(self):
        malicious = '<img src=x onerror="alert(1)">'
        with mock.patch(
            "routes.auth_email_code_routes._smtp_send_email", return_value=(True, None)
        ) as send:
            ok = invitations.send_invite_email(
                "buyer@example.com",
                "https://pearnly.com/invite/token",
                "Tenant A",
                malicious,
            )
        self.assertTrue(ok)
        body = send.call_args.args[2]
        self.assertNotIn(malicious, body)
        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;", body)


if __name__ == "__main__":
    unittest.main()

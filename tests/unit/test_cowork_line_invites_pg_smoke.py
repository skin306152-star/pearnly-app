"""Real same-tenant provisioning, password hashing and conflict-safe binding."""

import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from core.auth import verify_password
from services.cowork_line import work_invites
from tests.unit import test_work_bridge_pg_smoke as bridge_tests


class WorkInvitesPgTests(unittest.TestCase):
    def setUp(self):
        self.pg = bridge_tests.WorkBridgePgTests()
        self.pg.setUp()
        self.addCleanup(self.pg.tearDown)
        user, _ = self.pg.user()
        self.owner = user
        self.membership = str(uuid4())
        with self.pg.cursor(commit=True) as cur:
            cur.execute("INSERT INTO roles (key) VALUES ('owner') RETURNING id")
            role = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO memberships (id,user_id,tenant_id,role_id,status) VALUES (%s,%s,%s,%s,'active')",
                (self.membership, user["id"], user["tenant_id"], role),
            )
            cur.execute("""CREATE TABLE cowork_line_identities (
                membership_id uuid PRIMARY KEY,user_id uuid,tenant_id uuid,line_user_id text UNIQUE,
                display_name text,picture_url text,friendship_ready boolean,friendship_checked_at timestamptz,
                connected_at timestamptz,last_seen_at timestamptz,revoked_at timestamptz)""")
            cur.execute(
                "INSERT INTO cowork_line_identities (membership_id,user_id,tenant_id,line_user_id) VALUES (%s,%s,%s,'owner-line')",
                (self.membership, user["id"], user["tenant_id"]),
            )
        self.identity = {
            "membership_id": self.membership,
            "user_id": user["id"],
            "tenant_id": user["tenant_id"],
            "line_user_id": "owner-line",
        }
        for target, kwargs in (
            (
                "services.cowork_line.work_invites.claims",
                {"side_effect": lambda token: {"sub": token}},
            ),
            (
                "services.cowork_line.identity_store.resolve_active_identity",
                {"side_effect": lambda token: self.identity if token == "owner-line" else None},
            ),
            ("services.cowork_line.work_invites.line_owner.snapshot", {"return_value": {}}),
            (
                "services.cowork_line.work_invites.line_owner.request",
                {"return_value": {"_id": "native-member"}},
            ),
        ):
            p = patch(target, **kwargs)
            p.start()
            self.addCleanup(p.stop)

    def invite(self, **overrides):
        args = dict(
            token="owner-line",
            request_id="invite-test-operation",
            account="employee.line",
            password="Local-Only-Password-123",
            display_name="พนักงาน",
            board="native-board",
        )
        return work_invites.invite(**{**args, **overrides})

    def test_invite_same_tenant_and_password_retry_conflict(self):
        first = self.invite()
        self.assertEqual(self.invite(), first)
        with self.pg.cursor() as cur:
            cur.execute(
                "SELECT u.*,r.key FROM users u JOIN memberships m ON m.user_id=u.id JOIN roles r ON r.id=m.role_id WHERE u.id=%s",
                (first["user_id"],),
            )
            user = cur.fetchone()
        self.assertEqual(str(user["tenant_id"]), self.owner["tenant_id"])
        self.assertEqual(user["key"], "accountant")
        self.assertTrue(verify_password("Local-Only-Password-123", user["password_hash"]))
        with self.assertRaises(HTTPException):
            self.invite(password="Changed-Password-123")
        with self.assertRaises(HTTPException):
            self.invite(token="employee-line", account="other.employee")

    def test_bind_retry_and_no_silent_replacement(self):
        employee = self.invite()
        args = {"user_id": employee["user_id"], "tenant_id": self.owner["tenant_id"]}
        self.assertTrue(work_invites.connect(**args, token="employee-line")["connected"])
        self.assertTrue(work_invites.connect(**args, token="employee-line")["connected"])
        with self.assertRaises(HTTPException):
            work_invites.connect(**args, token="different-line")
        with self.assertRaises(
            (HTTPException, work_invites.identity_store.CoworkLineIdentityError)
        ):
            work_invites.connect(
                user_id=self.owner["id"], tenant_id=self.owner["tenant_id"], token="employee-line"
            )
        with self.pg.cursor(commit=True) as cur:
            cur.execute(
                "UPDATE memberships SET status='disabled' WHERE user_id=%s", (employee["user_id"],)
            )
        with self.assertRaises(work_invites.identity_store.CoworkLineIdentityError):
            work_invites.connect(**args, token="employee-line")

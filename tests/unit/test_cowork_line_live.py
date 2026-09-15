"""Live sessions stay scoped and snapshots reflect native changes without writes."""

import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from fastapi import HTTPException

from services.cowork_line import work_live as live


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.identity = {
            "user_id": "u",
            "tenant_id": "t",
            "membership_id": "m",
            "line_user_id": "l",
        }
        self.data = {
            "cards": [{"_id": "c", "title": "Task", "listId": "p", "assignees": ["u"]}],
            "lists": [{"_id": "p", "title": "Pending"}],
            "people": [{"_id": "u", "name": "Employee"}],
            "comments": [],
        }
        for name, kwargs in (
            ("work_invites.claims", {"return_value": {"sub": "l"}}),
            ("identity_store.resolve_active_identity", {"return_value": self.identity}),
            (
                "line_owner.service",
                {"return_value": SimpleNamespace(secret="unit-only-secret-12345678901234567890")},
            ),
            ("line_owner.actor", {"return_value": {"work_role": "employee"}}),
            (
                "line_owner.snapshot",
                {
                    "side_effect": lambda identity, board="": (
                        self.data if board else {"boards": [{"_id": "b", "title": "Board"}]}
                    )
                },
            ),
            ("work_store.board_mapping", {"return_value": {"pending": "p", "done": "d"}}),
        ):
            p = patch("services.cowork_line.work_live." + name, **kwargs)
            p.start()
            self.addCleanup(p.stop)
        self.token = live.authenticate("verified-line-token")["token"]

    def test_native_change_updates_version_and_actual_status(self):
        before = live.read(self.token, "b")
        self.data["cards"][0]["listId"] = "d"
        after = live.read(self.token, "b")
        self.assertNotEqual(before["version"], after["version"])
        self.assertEqual(after["tasks"][0]["status"], "done")
        self.assertEqual(after["role"], "employee")

    def test_board_scope_and_revocation_checked_each_read(self):
        with self.assertRaises(HTTPException) as denied:
            live.read(self.token, "other-tenant")
        self.assertEqual(denied.exception.status_code, 403)
        with patch.object(live.line_owner, "actor", side_effect=HTTPException(403)):
            with self.assertRaises(HTTPException):
                live.read(self.token, "b")

    def test_tampered_expired_and_wrong_audience_sessions_denied(self):
        secret = live.line_owner.service().secret
        for token in (
            self.token + "bad",
            jwt.encode(
                {"identity": self.identity, "iat": 0, "exp": 1, "aud": live.AUDIENCE},
                secret,
                algorithm="HS256",
            ),
            jwt.encode(
                {
                    "identity": self.identity,
                    "iat": time.time(),
                    "exp": time.time() + 60,
                    "aud": "other",
                },
                secret,
                algorithm="HS256",
            ),
        ):
            with self.assertRaises(HTTPException) as denied:
                live.read(token)
            self.assertEqual(denied.exception.status_code, 401)

    def test_unbound_line_cannot_get_session(self):
        with patch.object(live.identity_store, "resolve_active_identity", return_value=None):
            with self.assertRaises(HTTPException):
                live.authenticate("valid-but-unbound")

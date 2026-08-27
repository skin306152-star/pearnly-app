"""Cowork 注册入口与 ERP 邀请制契约。"""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException
from starlette.requests import Request

from services.auth import auth_signup
from services.auth.signup_core import _normalize_signup_entry

ROOT = Path(__file__).resolve().parents[2]
LANDING = ROOT / "static" / "landing" / "landing.js"


class CoworkSignupContractTests(unittest.TestCase):
    def test_only_main_cowork_and_erp_are_registration_contexts(self):
        self.assertEqual(_normalize_signup_entry("cowork"), "cowork")
        self.assertEqual(_normalize_signup_entry("erp"), "erp")
        self.assertEqual(_normalize_signup_entry("main"), "main")
        self.assertIsNone(_normalize_signup_entry("dms"))
        self.assertIsNone(_normalize_signup_entry("unknown"))

    def test_erp_signup_is_rejected_before_database_work(self):
        req = auth_signup.SignupRequest(
            email="merchant@example.test",
            password="Password123",
            entry="erp",
        )
        request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 1)})
        with mock.patch.object(auth_signup, "is_signup_globally_disabled", return_value=False):
            with self.assertRaises(HTTPException) as error:
                auth_signup.signup(req, request)
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(error.exception.detail, "erp_invite_only")

    def test_email_signup_issues_token_for_the_requested_entry(self):
        source = inspect.getsource(auth_signup.signup)
        token_call = source.split("token = create_access_token", 1)[1]
        self.assertIn("entry=signup_entry", token_call)

    def test_landing_threads_entry_without_adding_a_second_signup_api(self):
        source = LANDING.read_text(encoding="utf-8")
        self.assertIn("/api/auth/google/start?entry=", source)
        self.assertIn("/api/auth/line/start?entry=", source)
        self.assertIn("entry: _entry", source)
        self.assertEqual(source.count("fetch('/api/auth/signup'"), 1)


if __name__ == "__main__":
    unittest.main()

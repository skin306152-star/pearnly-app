"""HTTP auth boundaries for the universal collaboration entry."""

import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from routes import work_bridge_routes as routes


class WorkBridgeRouteTests(unittest.TestCase):
    def setUp(self):
        self.secret = "test-work-bridge-" + "a" * 32
        self.env = patch.dict(
            os.environ,
            {"WORK_BRIDGE_URL": "https://work.example.test", "WORK_BRIDGE_SECRET": self.secret},
        )
        self.env.start()
        app = FastAPI()
        app.include_router(routes.router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.addCleanup(self.env.stop)

    def test_entry_for_all_cowork_users_without_owner_or_tenant_allowlist(self):
        for entry, tenant in (("cowork", None), ("cowork", str(uuid4())), ("main", str(uuid4()))):
            with patch.object(
                routes,
                "get_current_user_from_request",
                return_value={
                    "id": str(uuid4()),
                    "entry": entry,
                    "tenant_id": tenant,
                    "role": "member",
                },
            ):
                response = self.client.get("/api/work/entry")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["url"], "https://work.example.test/_pearnly/start")

    def test_other_scoped_tokens_and_anonymous_users_cannot_create_handoffs(self):
        for entry in ("erp", "pos", "dms", "ai", "daily"):
            with patch.object(
                routes, "get_current_user_from_request", return_value={"entry": entry}
            ):
                self.assertEqual(self.client.get("/api/work/entry").status_code, 403)
        with patch.object(
            routes, "get_current_user_from_request", side_effect=HTTPException(401, "auth.required")
        ):
            self.assertEqual(self.client.get("/api/work/entry").status_code, 401)

    def test_browser_credentials_cannot_impersonate_the_internal_service(self):
        for auth in ("", "Bearer ordinary-user-jwt", "Bearer " + self.secret[:-1]):
            with patch.object(routes.sessions, "validate") as validate:
                response = self.client.post(
                    "/api/work/service/session",
                    json={"session": "a" * 64},
                    headers={"Authorization": auth},
                )
                self.assertEqual(response.status_code, 401)
                validate.assert_not_called()
        with patch.object(
            routes.sessions, "validate", return_value={"user_id": "test"}
        ) as validate:
            response = self.client.post(
                "/api/work/service/session",
                json={"session": "a" * 64},
                headers={"Authorization": "Bearer " + self.secret},
            )
            self.assertEqual(response.status_code, 200)
            validate.assert_called_once_with("a" * 64)

    def test_ticket_requires_valid_browser_state_before_issuing_credentials(self):
        with patch.object(routes.sessions, "issue") as issue:
            for state in ("", "https://outside.example", "a" * 1000):
                response = self.client.post("/api/work/tickets", json={"state": state})
                self.assertEqual(response.status_code, 422)
            issue.assert_not_called()

    def test_public_shell_form_is_limited_to_the_configured_service(self):
        response = routes.work_page()
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["referrer-policy"], "strict-origin")
        self.assertIn(
            "form-action 'self' https://work.example.test",
            response.headers["content-security-policy"],
        )
        self.assertNotIn(self.secret, str(response.headers))


if __name__ == "__main__":
    unittest.main()

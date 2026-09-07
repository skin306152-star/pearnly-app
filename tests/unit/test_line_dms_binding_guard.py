"""Identity regressions: a fresh binding must never inherit an old browser or job."""

import asyncio
import copy
import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.pos_api import PosError
from routes import line_dms_credentials_routes as credentials
from services.line_dms import binding_guard as guard, query_flow

A = {"id": "epoch-a", "line_user_id": "line-1", "user_id": "user-a", "tenant_id": "tenant"}
B = {**A, "id": "epoch-b", "user_id": "user-b"}


class BindingGuardTests(unittest.TestCase):
    def setUp(self):
        self.live = copy.deepcopy(A)
        self.user = {"id": "user-a", "tenant_id": "tenant", "role": "member", "is_active": True}
        self.profile = {"status": "active", "can_query_dms": True, "dms_role": "admin"}
        for target, replacement in (
            ("services.line_dms.store.get_binding_by_line_user", lambda _: self.live),
            ("core.db.find_user_by_id", lambda _: self.user),
            ("services.dms_roster.store.get_profile", lambda *_: self.profile),
        ):
            self.enterContext(patch(target, side_effect=replacement))

    def test_current_binding_requires_exact_epoch_user_tenant_and_line(self):
        self.assertTrue(guard.current(A))
        for key, value in (("id", "new-epoch"), ("user_id", "other"), ("tenant_id", "other")):
            with self.subTest(key=key):
                self.live = {**A, key: value}
                self.assertFalse(guard.current(A))
        self.live = A
        self.assertFalse(guard.current(A, "other-line"))
        self.assertFalse(guard.current({k: v for k, v in A.items() if k != "id"}))

    def test_disabled_deleted_and_demoted_users_are_rejected(self):
        self.user["is_active"] = False
        self.assertFalse(guard.current(A))
        self.user["is_active"] = True
        self.profile = None
        self.assertFalse(guard.current(A))
        self.profile = {"status": "inactive"}
        self.assertFalse(guard.current(A))
        self.profile = {"status": "active", "can_query_dms": False, "dms_role": "sales"}
        self.assertFalse(guard.current({**A, "_require_query": True}))
        self.assertFalse(guard.current({**A, "_require_admin": True}))

    def test_browser_rejects_legacy_token_and_rebound_identity(self):
        request = Mock(headers={"Authorization": "Bearer signed"})
        claims = {"sub": "user-a", "typ": "access", "entry": "dms"}
        with patch("core.auth.decode_access_token", return_value=claims):
            with self.assertRaises(PosError):
                guard.authorize_browser(request, self.user)
            claims["dms_binding"] = A
            self.assertEqual(guard.authorize_browser(request, self.user)["_dms_binding"], A)
            self.live = B
            with self.assertRaises(PosError):
                guard.authorize_browser(request, self.user)

    def test_rebind_during_background_wait_prevents_the_effect(self):
        effects = []

        @guard.bound_task
        async def operation(binding, line_user_id):
            self.live = B
            await asyncio.to_thread(guard.require_current)
            effects.append("write")

        asyncio.run(operation(A, "line-1"))
        self.assertEqual(effects, [])
        self.assertIsNone(guard.snapshot())

    def test_old_queued_query_never_contacts_dms(self):
        self.live = B
        with patch.object(query_flow.sales_readback, "fetch_sales_records") as fetch:
            asyncio.run(query_flow._run_records(A, "line-1", {}))
        fetch.assert_not_called()

    def test_permission_revoked_before_query_does_not_read(self):
        self.profile["can_query_dms"] = False
        with patch.object(query_flow.sales_readback, "fetch_sales_records") as fetch:
            asyncio.run(query_flow._run_records(A, "line-1", {}))
        fetch.assert_not_called()

    def test_http_old_tab_cannot_update_after_line_rebind(self):
        # The ordinary JWT remains valid for A; the LINE binding check must still deny it.
        app = FastAPI()
        app.include_router(credentials.router)
        claims = {"sub": "user-a", "typ": "access", "entry": "dms", "dms_binding": A}
        self.live = B
        with (
            patch("routes.dms_routes._authorize", return_value=self.user),
            patch.object(credentials, "dms_line_enabled_for", return_value=True),
            patch("core.auth.decode_access_token", return_value=claims),
            patch.object(credentials.self_credentials, "update") as update,
        ):
            # PosError is handled by the application-wide handler in production.
            with self.assertRaises(PosError) as caught:
                TestClient(app).put(
                    "/api/line/dms-credentials",
                    headers={"Authorization": "Bearer signed"},
                    json={"username": "test-sale", "password": "new-test-password"},
                )
        self.assertEqual(caught.exception.http_status, 401)
        update.assert_not_called()

    def test_current_browser_updates_only_its_bound_user(self):
        app = FastAPI()
        app.include_router(credentials.router)
        claims = {"sub": "user-a", "typ": "access", "entry": "dms", "dms_binding": A}
        with (
            patch("routes.dms_routes._authorize", return_value=self.user),
            patch.object(credentials, "dms_line_enabled_for", return_value=True),
            patch("core.auth.decode_access_token", return_value=claims),
            patch.object(
                credentials.self_credentials, "update", return_value={"updated": True}
            ) as update,
        ):
            response = TestClient(app).put(
                "/api/line/dms-credentials",
                headers={"Authorization": "Bearer signed"},
                json={"username": "test-sale", "password": "test-password"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(update.call_args.args[0]["id"], "user-a")

    def test_rebind_during_external_login_prevents_callback(self):
        from services.erp import erp_dms_intake as intake
        from unittest.mock import MagicMock

        adapter = MagicMock()
        adapter.login.side_effect = lambda: setattr(self, "live", B)
        adapter.concurrent_login_detected = False
        effect = Mock()
        with (
            guard.scope(A),
            patch.object(intake, "_build_mrerp_dms_adapter", return_value=(adapter, None)),
        ):
            with self.assertRaises(guard.BindingChanged):
                intake._run_logged_in({"config": {}}, effect)
        effect.assert_not_called()


if __name__ == "__main__":
    unittest.main()

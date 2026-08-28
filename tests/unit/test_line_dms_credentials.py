# -*- coding: utf-8 -*-

import asyncio
import copy
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

from core.pos_api import PosError
from routes import line_dms_credentials_routes as routes
from services.dms_roster import self_credentials
from services.line_dms import mrerp_portal

OPERATOR = {"id": "user-1", "tenant_id": "tenant-1", "role": "member"}
PROFILE = {"user_id": "user-1", "tenant_id": "tenant-1", "status": "active"}
ENDPOINT = {
    "id": "endpoint-1",
    "adapter": "mrerp_dms",
    "enabled": True,
    "config": {
        "system_url": "https://www.mrerp4sme.com/dms/",
        "username_enc": "old-user-enc",
        "password_enc": "old-pass-enc",
        "booking_defaults": {"advisor_id": "42"},
    },
}


class SelfCredentialsTests(unittest.TestCase):
    @mock.patch("services.erp.erp_dms_push._dms_plain_creds", return_value=("sale02", "secret"))
    @mock.patch("core.db.list_erp_endpoints", return_value=[ENDPOINT])
    @mock.patch.object(self_credentials.store, "get_profile", return_value=PROFILE)
    def test_load_returns_username_without_password(self, _profile, _endpoints, _decrypt):
        result = self_credentials.load(OPERATOR)
        self.assertEqual(result, {"username": "sale02"})
        self.assertNotIn("password", result)

    @mock.patch("core.db.update_erp_endpoint", return_value=True)
    @mock.patch("core.db.list_erp_endpoints", return_value=[ENDPOINT])
    @mock.patch.object(self_credentials.store, "get_profile", return_value=PROFILE)
    def test_update_replaces_only_own_pair_and_preserves_endpoint_config(
        self, _profile, _endpoints, update_endpoint
    ):
        fake_kms = SimpleNamespace(encrypt_str=lambda value: f"enc:{value}")
        with mock.patch.dict(sys.modules, {"core.kms_helper": fake_kms}):
            result = self_credentials.update(OPERATOR, username="new-sale", password="new-pass")
        self.assertEqual(result, {"updated": True})
        update_endpoint.assert_called_once()
        user_id, endpoint_id = update_endpoint.call_args.args
        config = update_endpoint.call_args.kwargs["config"]
        self.assertEqual((user_id, endpoint_id), ("user-1", "endpoint-1"))
        self.assertEqual(config["username_enc"], "enc:new-sale")
        self.assertEqual(config["password_enc"], "enc:new-pass")
        self.assertEqual(config["booking_defaults"], {"advisor_id": "42"})
        self.assertEqual(config["system_url"], "https://www.mrerp4sme.com/dms/")

    @mock.patch.object(self_credentials.store, "get_profile")
    def test_owner_cannot_use_operator_self_service(self, get_profile):
        with self.assertRaises(self_credentials.SelfCredentialError) as caught:
            self_credentials.update(
                {"id": "owner-1", "tenant_id": "tenant-1", "role": "owner"},
                username="owner",
                password="secret",
            )
        self.assertEqual(caught.exception.code, "dms_credentials.operator_only")
        get_profile.assert_not_called()

    @mock.patch.object(
        self_credentials.store,
        "get_profile",
        return_value={**PROFILE, "status": "inactive"},
    )
    def test_inactive_operator_cannot_update(self, _profile):
        with self.assertRaises(self_credentials.SelfCredentialError) as caught:
            self_credentials.update(OPERATOR, username="sale02", password="secret")
        self.assertEqual(caught.exception.code, "dms_credentials.operator_inactive")

    @mock.patch("core.db.list_erp_endpoints", return_value=[])
    @mock.patch.object(self_credentials.store, "get_profile", return_value=PROFILE)
    def test_missing_endpoint_is_reported_without_creating_another(self, _profile, _endpoints):
        with self.assertRaises(self_credentials.SelfCredentialError) as caught:
            self_credentials.update(OPERATOR, username="sale02", password="secret")
        self.assertEqual(caught.exception.code, "dms_credentials.endpoint_missing")


class CredentialRouteTests(unittest.TestCase):
    def test_router_contract(self):
        got = {
            (method, route.path)
            for route in routes.router.routes
            for method in (route.methods or set())
            if method in {"GET", "PUT"}
        }
        self.assertEqual(
            got,
            {
                ("GET", "/api/line/dms-credentials"),
                ("PUT", "/api/line/dms-credentials"),
            },
        )

    def test_update_runs_blocking_store_off_event_loop(self):
        def blocking_update(user, *, username, password):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            self.assertEqual((username, password), ("sale02", "new-pass"))
            return {"updated": True}

        with (
            mock.patch.object(routes, "_authorize", new=mock.AsyncMock(return_value=OPERATOR)),
            mock.patch.object(routes.self_credentials, "update", side_effect=blocking_update),
        ):
            result = asyncio.run(
                routes.update_dms_credentials(
                    object(), routes.DmsCredentialsIn(username="sale02", password="new-pass")
                )
            )
        self.assertTrue(result["ok"])

    def test_service_error_preserves_code_and_status(self):
        with (
            mock.patch.object(routes, "_authorize", new=mock.AsyncMock(return_value=OPERATOR)),
            mock.patch.object(
                routes.self_credentials,
                "load",
                side_effect=self_credentials.SelfCredentialError(
                    "dms_credentials.operator_inactive"
                ),
            ),
        ):
            with self.assertRaises(PosError) as caught:
                asyncio.run(routes.get_dms_credentials(object()))
        self.assertEqual(caught.exception.http_status, 403)

    def test_app_registers_credential_routes(self):
        import app

        paths = {route.path for route in app.app.routes if hasattr(route, "path")}
        self.assertIn("/api/line/dms-credentials", paths)

    def test_editor_update_is_used_by_the_next_dms_portal_login(self):
        endpoint = copy.deepcopy(ENDPOINT)

        def persist(_user_id, _endpoint_id, *, config):
            endpoint["config"] = copy.deepcopy(config)
            return True

        def decrypt(value):
            return value.removeprefix("enc:")

        fake_kms = SimpleNamespace(
            encrypt_str=lambda value: f"enc:{value}",
            decrypt_str=decrypt,
        )
        with (
            mock.patch.dict(sys.modules, {"core.kms_helper": fake_kms}),
            mock.patch.object(routes, "_authorize", new=mock.AsyncMock(return_value=OPERATOR)),
            mock.patch.object(self_credentials.store, "get_profile", return_value=PROFILE),
            mock.patch("core.db.list_erp_endpoints", return_value=[endpoint]),
            mock.patch("core.db.update_erp_endpoint", side_effect=persist),
            mock.patch(
                "services.erp.dms_id_ocr.resolve_dms_endpoint",
                return_value=endpoint,
            ),
        ):
            response = asyncio.run(
                routes.update_dms_credentials(
                    object(),
                    routes.DmsCredentialsIn(
                        username="changed-in-dms",
                        password="changed-password",
                    ),
                )
            )
            credentials = mrerp_portal.load_credentials(OPERATOR["id"])
            relay, _nonce = mrerp_portal.render_login_relay(*credentials)

        self.assertTrue(response["ok"])
        self.assertEqual(credentials, ("changed-in-dms", "changed-password"))
        self.assertIn('name="txtusers" value="changed-in-dms"', relay)
        self.assertIn('name="txtpasswords" value="changed-password"', relay)


if __name__ == "__main__":
    unittest.main()

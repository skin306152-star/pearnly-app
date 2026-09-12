# -*- coding: utf-8 -*-
"""Shared LIFF verification and the active DMS editor entry."""

import asyncio
import os
import unittest
from pathlib import Path
from unittest import mock

from routes import line_dms_booking_edit_routes as dms_edit
from services.line_platform import liff


class _Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._p = payload

    def json(self):
        return self._p


class VerifyIdTokenTests(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("LINE_LOGIN_CHANNEL_ID")
        os.environ["LINE_LOGIN_CHANNEL_ID"] = "ch-1"

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("LINE_LOGIN_CHANNEL_ID", None)
        else:
            os.environ["LINE_LOGIN_CHANNEL_ID"] = self._saved

    def test_verify_ok(self):
        with mock.patch.object(liff.requests, "post", return_value=_Resp(200, {"sub": "U123"})):
            self.assertEqual(liff.verify_id_token("tok", "LINE_LIFF_ID")["sub"], "U123")

    def test_verify_non200_none(self):
        with mock.patch.object(liff.requests, "post", return_value=_Resp(400, {})):
            self.assertIsNone(liff.verify_id_token("tok", "LINE_LIFF_ID"))

    def test_verify_no_channel_none(self):
        os.environ.pop("LINE_LOGIN_CHANNEL_ID", None)
        self.assertIsNone(liff.verify_id_token("tok", "LINE_LIFF_ID"))

    def test_non_legacy_env_without_its_liff_never_borrows_login_channel(self):
        with mock.patch.dict(os.environ, {"LINE_LOGIN_CHANNEL_ID": "ch-1"}, clear=True):
            with mock.patch.object(liff.requests, "post") as post:
                self.assertIsNone(liff.verify_id_token("tok", "LINE_DMS_A_LIFF_ID"))
                self.assertIsNone(liff.verify_id_token("tok", "LINE_DMS_B_LIFF_ID"))
        post.assert_not_called()

    def test_non_legacy_env_with_its_own_liff_verifies_that_channel(self):
        with mock.patch.dict(
            os.environ,
            {"LINE_DMS_A_LIFF_ID": "111-abc", "LINE_LOGIN_CHANNEL_ID": "ch-1"},
            clear=True,
        ):
            with mock.patch.object(
                liff.requests, "post", return_value=_Resp(200, {"sub": "U1"})
            ) as post:
                self.assertEqual(liff.verify_id_token("tok", "LINE_DMS_A_LIFF_ID")["sub"], "U1")
        self.assertEqual(post.call_args.kwargs["data"]["client_id"], "111")

    def test_legacy_env_keeps_shared_login_channel_fallback(self):
        with mock.patch.dict(os.environ, {"LINE_LOGIN_CHANNEL_ID": "ch-1"}, clear=True):
            with mock.patch.object(
                liff.requests, "post", return_value=_Resp(200, {"sub": "U1"})
            ) as post:
                self.assertEqual(liff.verify_id_token("tok", "LINE_ERP_LIFF_ID")["sub"], "U1")
        self.assertEqual(post.call_args.kwargs["data"]["client_id"], "ch-1")

    def test_unknown_liff_env_never_borrows_login_channel(self):
        with mock.patch.dict(os.environ, {"LINE_LOGIN_CHANNEL_ID": "ch-1"}, clear=True):
            with mock.patch.object(liff.requests, "post") as post:
                self.assertIsNone(liff.verify_id_token("tok", "LINE_OTHER_LIFF_ID"))
        post.assert_not_called()

    def test_dms_invalid_line_token_requires_line_login_before_binding_lookup(self):
        from core.pos_api import PosError

        for claims in (None, {}):
            with (
                self.subTest(claims=claims),
                mock.patch.object(dms_edit, "verify_id_token", return_value=claims),
                mock.patch("services.line_dms.store.get_binding_by_line_user") as lookup,
                mock.patch.object(dms_edit, "create_access_token") as issue,
            ):
                with self.assertRaises(PosError) as caught:
                    asyncio.run(
                        dms_edit.dms_booking_liff_auth(dms_edit.LiffAuthIn(id_token="expired"))
                    )
                self.assertEqual(caught.exception.http_status, 401)
                self.assertEqual(caught.exception.code, "dms_booking.line_auth_required")
                lookup.assert_not_called()
                issue.assert_not_called()

    def test_dms_bound_user_gets_dms_scoped_token(self):
        binding = {
            "id": "epoch-1",
            "line_user_id": "L1",
            "user_id": "u1",
            "tenant_id": "t1",
            "channel_key": "dms",
        }
        user = {
            "id": "u1",
            "username": "sale02",
            "plan": "free",
            "tenant_id": "t1",
            "role": "member",
            "is_active": True,
        }
        with (
            # Legacy OA has its own LIFF id here, so verification must use that env, not the
            # shared Provider app (an unset own-LIFF deployment is the next test).
            mock.patch.dict(os.environ, {"LINE_DMS_LIFF_ID": "DMS-LIFF"}, clear=True),
            mock.patch.object(dms_edit, "verify_id_token", return_value={"sub": "L1"}) as verify,
            mock.patch("services.line_dms.store.get_binding_by_line_user", return_value=binding),
            mock.patch.object(dms_edit.db, "find_user_by_id", return_value=user),
            mock.patch("services.dms_roster.store.get_profile", return_value={"status": "active"}),
            mock.patch("services.line_dms.account_channel.get_channel", return_value="dms"),
            mock.patch.object(dms_edit, "create_access_token", return_value="DMS-JWT") as issue,
        ):
            res = asyncio.run(dms_edit.dms_booking_liff_auth(dms_edit.LiffAuthIn(id_token="ok")))
        verify.assert_called_once_with("ok", "LINE_DMS_LIFF_ID")
        self.assertEqual(res["data"]["token"], "DMS-JWT")
        self.assertEqual(issue.call_args.kwargs["entry"], "dms")
        self.assertEqual(issue.call_args.kwargs["dms_binding"], binding)

    def test_dms_auth_without_any_liff_env_fails_closed_before_verify(self):
        """没有任何 LIFF 配置 → 不发明 env 名、不发 verify 请求(未知/未声明一律失败关闭)。"""
        from core.pos_api import PosError

        with (
            mock.patch.dict(os.environ, {"LINE_LOGIN_CHANNEL_ID": "ch-1"}, clear=True),
            mock.patch.object(liff.requests, "post") as post,
        ):
            with self.assertRaises(PosError) as caught:
                asyncio.run(dms_edit.dms_booking_liff_auth(dms_edit.LiffAuthIn(id_token="ok")))
        self.assertEqual(caught.exception.http_status, 401)
        self.assertEqual(caught.exception.code, "dms_booking.line_auth_required")
        post.assert_not_called()

    def test_dms_a_auth_verifies_a_liff_and_looks_up_a_binding(self):
        binding = {
            "id": "epoch-a",
            "line_user_id": "L1",
            "user_id": "u1",
            "tenant_id": "t1",
            "channel_key": "dms_a",
        }
        user = {
            "id": "u1",
            "username": "sale02",
            "plan": "free",
            "tenant_id": "t1",
            "role": "member",
            "is_active": True,
        }
        with (
            mock.patch.dict(os.environ, {"LINE_DMS_A_LIFF_ID": "A-LIFF"}, clear=True),
            mock.patch.object(dms_edit, "verify_id_token", return_value={"sub": "L1"}) as verify,
            mock.patch(
                "services.line_dms.store.get_binding_by_line_user", return_value=binding
            ) as lookup,
            mock.patch.object(dms_edit.db, "find_user_by_id", return_value=user),
            mock.patch("services.dms_roster.store.get_profile", return_value={"status": "active"}),
            mock.patch("services.line_dms.account_channel.get_channel", return_value="dms_a"),
            mock.patch.object(dms_edit, "create_access_token", return_value="A-JWT"),
        ):
            res = asyncio.run(
                dms_edit.dms_booking_liff_auth(dms_edit.LiffAuthIn(id_token="ok", channel="dms_a"))
            )
        verify.assert_called_once_with("ok", "LINE_DMS_A_LIFF_ID")
        self.assertEqual(lookup.call_args.args, ("L1", "dms_a"))
        self.assertEqual(res["data"]["token"], "A-JWT")

    def test_dms_a_without_override_uses_provider_liff_and_its_own_binding(self):
        with mock.patch.dict(
            os.environ,
            {"LINE_LIFF_ID": "123-SHARED", "LINE_LOGIN_CHANNEL_ID": "123"},
            clear=True,
        ):
            with (
                mock.patch.object(
                    dms_edit, "verify_id_token", return_value={"sub": "L1"}
                ) as verify,
                mock.patch(
                    "services.line_dms.store.get_binding_by_line_user",
                    return_value={
                        "id": "epoch-a",
                        "line_user_id": "L1",
                        "user_id": "u1",
                        "tenant_id": "t1",
                        "channel_key": "dms_a",
                    },
                ) as lookup,
                mock.patch.object(
                    dms_edit.db,
                    "find_user_by_id",
                    return_value={
                        "id": "u1",
                        "username": "sale02",
                        "tenant_id": "t1",
                        "role": "member",
                        "is_active": True,
                    },
                ),
                mock.patch(
                    "services.dms_roster.store.get_profile", return_value={"status": "active"}
                ),
                mock.patch("services.line_dms.account_channel.get_channel", return_value="dms_a"),
                mock.patch.object(dms_edit, "create_access_token", return_value="A-JWT"),
            ):
                res = asyncio.run(
                    dms_edit.dms_booking_liff_auth(
                        dms_edit.LiffAuthIn(id_token="ok", channel="dms_a")
                    )
                )
        verify.assert_called_once_with("ok", "LINE_LIFF_ID")
        self.assertEqual({call.args for call in lookup.call_args_list}, {("L1", "dms_a")})
        self.assertEqual(res["data"]["token"], "A-JWT")

    def test_unknown_channel_rejected_before_token_verification(self):
        from core.pos_api import PosError

        with mock.patch.object(dms_edit, "verify_id_token") as verify:
            with self.assertRaises(PosError) as caught:
                asyncio.run(
                    dms_edit.dms_booking_liff_auth(
                        dms_edit.LiffAuthIn(id_token="ok", channel="nope")
                    )
                )
        self.assertEqual(caught.exception.http_status, 403)
        verify.assert_not_called()


class DmsBookingConfigTests(unittest.TestCase):
    def test_config_defaults_to_legacy_liff(self):
        with mock.patch.dict(
            os.environ,
            {"LINE_DMS_LIFF_ID": "DMS-LIFF", "LINE_LIFF_ID": "SHARED-LIFF"},
            clear=True,
        ):
            res = asyncio.run(dms_edit.dms_booking_liff_config())
        self.assertEqual(
            res["data"], {"liff_id": "DMS-LIFF", "channel_key": "dms", "available": True}
        )

    def test_config_for_a_reuses_provider_liff(self):
        with mock.patch.dict(os.environ, {"LINE_LIFF_ID": "SHARED-LIFF"}, clear=True):
            res = asyncio.run(dms_edit.dms_booking_liff_config(channel="dms_a"))
        self.assertEqual(res["data"]["liff_id"], "SHARED-LIFF")
        self.assertEqual(res["data"]["channel_key"], "dms_a")
        self.assertTrue(res["data"]["available"])

    def test_config_unknown_channel_rejected(self):
        from core.pos_api import PosError

        with self.assertRaises(PosError) as caught:
            asyncio.run(dms_edit.dms_booking_liff_config(channel="nope"))
        self.assertEqual(caught.exception.http_status, 404)


class LiffEntryTests(unittest.TestCase):
    def test_dms_booking_entry_serves_built_shell_without_cache(self):
        res = asyncio.run(dms_edit.liff_dms_booking_entry())
        self.assertTrue(Path(res.path).as_posix().endswith("static/dist/dms-booking-edit.html"))
        self.assertIn("no-store", res.headers["cache-control"])

    def test_dms_booking_editor_has_registered_liff_path_alias(self):
        paths = {route.path for route in dms_edit.router.routes}
        self.assertIn("/liff/dms-booking", paths)
        self.assertIn("/login/dms-booking", paths)
        self.assertIn("/home/dms-booking", paths)


class DmsBookingAsyncTripwireTests(unittest.TestCase):
    def test_draft_loader_runs_off_event_loop(self):
        def blocking_load(user, nonce):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            return {"form": {}, "masters": {}}

        with (
            mock.patch.object(
                dms_edit, "_authorize", new=mock.AsyncMock(return_value={"id": "U1"})
            ),
            mock.patch("services.line_dms.booking_edit.load", side_effect=blocking_load),
        ):
            response = asyncio.run(dms_edit.dms_booking_draft(mock.Mock(), "N1"))
        self.assertTrue(response["ok"])


if __name__ == "__main__":
    unittest.main()

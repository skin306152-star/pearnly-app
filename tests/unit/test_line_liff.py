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

    def test_dms_bound_user_gets_dms_scoped_token(self):
        binding = {"line_user_id": "L1", "user_id": "u1", "tenant_id": "t1"}
        user = {
            "id": "u1",
            "username": "sale02",
            "plan": "free",
            "tenant_id": "t1",
            "role": "member",
            "is_active": True,
        }
        with (
            mock.patch.object(dms_edit, "verify_id_token", return_value={"sub": "L1"}) as verify,
            mock.patch("services.line_dms.store.get_binding_by_line_user", return_value=binding),
            mock.patch.object(dms_edit.db, "find_user_by_id", return_value=user),
            mock.patch.object(dms_edit, "create_access_token", return_value="DMS-JWT") as issue,
        ):
            res = asyncio.run(dms_edit.dms_booking_liff_auth(dms_edit.LiffAuthIn(id_token="ok")))
        verify.assert_called_once_with("ok", "LINE_DMS_LIFF_ID")
        self.assertEqual(res["data"]["token"], "DMS-JWT")
        self.assertEqual(issue.call_args.kwargs["entry"], "dms")


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

# -*- coding: utf-8 -*-
"""操作员花名册路由守卫契约(波3 · DL-8)· owner-only + C1 通用无码守卫继承。

覆盖:非 owner 403 owner_only、entry!=dms 403、闸关 404(经真实 dms._authorize 链)、
service 错误码 → HTTP 状态映射(not_found→404)。无 DATABASE_URL(mock 鉴权/service)。
"""

import asyncio
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

import routes.dms_routes as dms  # noqa: E402
import routes.dms_roster_routes as rr  # noqa: E402

OWNER = {"id": "owner-1", "tenant_id": "t1", "role": "owner", "entry": "dms"}


class _FakeReq:
    def __init__(self, body=None):
        self._body = body or {}

    async def json(self):
        return self._body


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class RosterGuardTest(unittest.TestCase):
    def test_non_owner_forbidden(self):
        member = {"id": "op-1", "tenant_id": "t1", "role": "member", "entry": "dms"}
        with mock.patch.object(rr, "_dms_authorize", return_value=member):
            with self.assertRaises(rr.HTTPException) as ctx:
                _run(rr.list_operators(object()))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "dms_roster.owner_only")

    def test_gate_closed_404_through_chain(self):
        with (
            mock.patch.object(dms, "get_current_user_from_request", return_value=OWNER),
            mock.patch.object(dms, "dms_portal_enabled_for", return_value=False),
            mock.patch.object(dms, "entrance_api_scope_enabled_for", return_value=True),
        ):
            with self.assertRaises(rr.HTTPException) as ctx:
                _run(rr.list_operators(object()))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_non_dms_entry_403_through_chain(self):
        main_owner = {"id": "owner-1", "tenant_id": "t1", "role": "owner", "entry": "main"}
        with (
            mock.patch.object(dms, "get_current_user_from_request", return_value=main_owner),
            mock.patch.object(dms, "dms_portal_enabled_for", return_value=True),
            mock.patch.object(dms, "entrance_api_scope_enabled_for", return_value=True),
        ):
            with self.assertRaises(rr.HTTPException) as ctx:
                _run(rr.list_operators(object()))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "authz.forbidden")

    def test_owner_list_ok(self):
        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(rr.roster, "list_operators", return_value={"ok": True, "items": []}),
        ):
            res = _run(rr.list_operators(object()))
        self.assertTrue(res["ok"])

    def test_not_found_maps_to_404(self):
        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(
                rr.roster, "set_status", return_value={"error": "dms_roster.not_found"}
            ),
        ):
            with self.assertRaises(rr.HTTPException) as ctx:
                _run(rr.set_operator_status("foreign", _FakeReq({"status": "inactive"})))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_advisors_requires_owner(self):
        member = {"id": "op-1", "tenant_id": "t1", "role": "member", "entry": "dms"}
        with mock.patch.object(rr, "_dms_authorize", return_value=member):
            with self.assertRaises(rr.HTTPException) as ctx:
                _run(rr.list_roster_advisors(object()))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_advisors_pass_through_without_endpoint(self):
        # 下拉的失败不走 4xx:前端要按 code 分别指路,统一 4xx 会被吞成一句「加载失败」。
        payload = {"ok": False, "code": "no_endpoint", "advisors": []}
        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(rr.roster, "list_advisors", return_value=payload),
        ):
            res = _run(rr.list_roster_advisors(object()))
        self.assertEqual(res, payload)

    def test_advisors_ok_list(self):
        payload = {"ok": True, "advisors": [{"id": "9", "code": "S09", "name": "阿明"}]}
        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(rr.roster, "list_advisors", return_value=payload),
        ):
            res = _run(rr.list_roster_advisors(object()))
        self.assertEqual(res["advisors"][0]["id"], "9")

    def test_advisors_runs_blocking_dms_fetch_off_event_loop(self):
        payload = {"ok": True, "advisors": [{"id": "9", "name": "阿明"}]}

        async def fake_to_thread(fn, *args):
            self.assertIs(fn, rr.roster.list_advisors)
            self.assertEqual(args, (OWNER,))
            return payload

        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(rr.asyncio, "to_thread", side_effect=fake_to_thread) as to_thread,
        ):
            res = _run(rr.list_roster_advisors(object()))

        self.assertEqual(res, payload)
        to_thread.assert_awaited_once()

    def test_create_passes_body_through(self):
        captured = {}

        def _cap(owner, **kw):
            captured.update(kw)
            return {"ok": True, "user_id": "op-9"}

        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(rr.roster, "create_operator", side_effect=_cap),
        ):
            body = {
                "display_name": "สมชาย",
                "dms_username": "u",
                "dms_password": "p",
                "dms_role": "sales",
                "dms_advisor_id": "9",
                "can_query_dms": True,
            }
            res = _run(rr.create_operator(_FakeReq(body)))
        self.assertTrue(res["ok"])
        self.assertEqual(captured["dms_role"], "sales")
        self.assertEqual(captured["display_name"], "สมชาย")
        self.assertEqual(captured["dms_advisor_id"], "9")
        self.assertTrue(captured["can_query_dms"])

    def test_update_advisor_field_reaches_service(self):
        captured = {}

        def _cap(owner, user_id, **kw):
            captured.update(kw)
            return {"ok": True}

        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(rr.roster, "update_operator", side_effect=_cap),
        ):
            _run(rr.update_operator("op-1", _FakeReq({"dms_advisor_id": ""})))
        # 空串必须原样穿到 service(那是「清除钉死」,不是「没传」)。
        self.assertEqual(captured["dms_advisor_id"], "")
        self.assertIsNone(captured["dms_username"])

    def test_update_false_query_permission_reaches_service(self):
        captured = {}

        def _cap(owner, user_id, **kw):
            captured.update(kw)
            return {"ok": True}

        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(rr.roster, "update_operator", side_effect=_cap),
        ):
            _run(rr.update_operator("op-1", _FakeReq({"can_query_dms": False})))
        self.assertIs(captured["can_query_dms"], False)

    def test_invalid_advisor_maps_to_400(self):
        with (
            mock.patch.object(rr, "_dms_authorize", return_value=OWNER),
            mock.patch.object(
                rr.roster, "update_operator", return_value={"error": "dms_roster.invalid_advisor"}
            ),
        ):
            with self.assertRaises(rr.HTTPException) as ctx:
                _run(rr.update_operator("op-1", _FakeReq({"dms_advisor_id": "404"})))
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()

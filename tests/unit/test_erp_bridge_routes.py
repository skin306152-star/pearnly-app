# -*- coding: utf-8 -*-
"""ERP 桥路由契约单测(直调 async handler · store 全 mock)。

钉死:5 条路由注册齐 · 密钥错 401 · 自述 bridge_id 与密钥不符 403 · hello 回生效角色与
轮询窗口 · 写桥被降级时响应里说明 · lease 有活立刻返回 / 没活挂到窗口末返空数组 ·
ack 回填与 409 · 管理端走权限码且永不回明文以外的密钥 · 急停开关一关全 404。
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import HTTPException  # noqa: E402

from routes import erp_bridge_routes as routes  # noqa: E402

TENANT = "11111111-1111-1111-1111-111111111111"
BRIDGE_A = "aaaaaaaa-1111-1111-1111-111111111111"
BRIDGE_B = "bbbbbbbb-2222-2222-2222-222222222222"
JOB_ID = "cccccccc-3333-3333-3333-333333333333"

BRIDGE = {
    "id": BRIDGE_A,
    "tenant_id": TENANT,
    "name": "office-nas",
    "books": [{"book_id": "DATAT"}],
    "effective_role": "read",
}


class FakeRequest:
    def __init__(self, token="brg_token"):
        self.headers = {"authorization": f"Bearer {token}"}


def run(coro):
    return asyncio.run(coro)


class AuthTests(unittest.TestCase):
    def test_bad_secret_is_401(self):
        with mock.patch.object(routes.store, "authenticate", return_value=None):
            with self.assertRaises(HTTPException) as ctx:
                run(routes.erp_bridge_hello(routes.HelloRequest(), FakeRequest()))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_missing_header_is_401(self):
        req = FakeRequest()
        req.headers = {}
        with mock.patch.object(routes.store, "authenticate", return_value=None) as auth:
            with self.assertRaises(HTTPException):
                run(routes.erp_bridge_hello(routes.HelloRequest(), req))
        auth.assert_called_once_with("")

    def test_claimed_bridge_id_must_match_the_secret(self):
        # 身份只认密钥;体里的 bridge_id 是自述,不符即拒(防拿 A 的密钥冒充 B)。
        with mock.patch.object(routes.store, "authenticate", return_value=BRIDGE):
            with self.assertRaises(HTTPException) as ctx:
                run(routes.erp_bridge_hello(routes.HelloRequest(bridge_id=BRIDGE_B), FakeRequest()))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_kill_switch_closes_every_bridge_endpoint(self):
        with mock.patch.object(routes, "bridge_enabled", return_value=False):
            for coro in (
                routes.erp_bridge_hello(routes.HelloRequest(), FakeRequest()),
                routes.erp_bridge_lease(routes.LeaseRequest(), FakeRequest()),
                routes.erp_bridge_ack(routes.AckRequest(job_id=JOB_ID), FakeRequest()),
            ):
                with self.subTest(coro=coro), self.assertRaises(HTTPException) as ctx:
                    run(coro)
                self.assertEqual(ctx.exception.status_code, 404)


class HelloTests(unittest.TestCase):
    def _hello(self, hello_result, **body):
        with (
            mock.patch.object(routes.store, "authenticate", return_value=BRIDGE),
            mock.patch.object(
                routes.store, "register_hello", return_value=hello_result
            ) as register,
        ):
            res = run(routes.erp_bridge_hello(routes.HelloRequest(**body), FakeRequest()))
        return res, register

    def test_registers_books_and_returns_poll_window(self):
        res, register = self._hello(
            {"effective_role": "read", "books": 1, "held_by": None},
            role="read",
            bridge_version="1.0.0",
            host="nas01",
            books=[{"book_id": "DATAT", "dir": r"\\acc\DATAT"}],
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["effective_role"], "read")
        self.assertEqual(res["books_registered"], 1)
        self.assertEqual(res["poll_hold_seconds"], routes.poll_hold_seconds())
        self.assertNotIn("note", res)
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["books"][0]["book_id"], "DATAT")
        self.assertEqual(kwargs["bridge_version"], "1.0.0")

    def test_downgraded_write_bridge_is_told_why(self):
        res, _ = self._hello(
            {"effective_role": "read", "books": 1, "held_by": {"id": BRIDGE_B, "name": "first"}},
            role="write",
        )
        self.assertEqual(res["effective_role"], "read")
        self.assertIn("first", res["note"])

    def test_lone_write_bridge_keeps_write(self):
        res, _ = self._hello({"effective_role": "write", "books": 2, "held_by": None}, role="write")
        self.assertEqual(res["effective_role"], "write")


class LeaseTests(unittest.TestCase):
    def test_returns_jobs_immediately_when_queue_has_work(self):
        job = {"id": JOB_ID, "kind": "query", "book_id": "DATAT", "payload": {"op": "tables"}}
        with (
            mock.patch.object(routes.store, "authenticate", return_value=BRIDGE),
            mock.patch.object(routes.store, "lease_jobs", return_value=[job]) as lease,
        ):
            res = run(routes.erp_bridge_lease(routes.LeaseRequest(max=1), FakeRequest()))
        self.assertEqual(res["jobs"][0]["job_id"], JOB_ID)
        self.assertEqual(res["jobs"][0]["payload"], {"op": "tables"})
        self.assertEqual(res["lease_seconds"], routes.store.LEASE_SECONDS)
        # 只领本桥的活:交给 store 的永远是密钥解出来的那座桥。
        self.assertIs(lease.call_args.args[0], BRIDGE)

    def test_empty_queue_holds_then_returns_empty_array(self):
        with (
            mock.patch.object(routes.store, "authenticate", return_value=BRIDGE),
            mock.patch.object(routes.store, "lease_jobs", return_value=[]) as lease,
            mock.patch.object(routes, "poll_hold_seconds", return_value=1),
            mock.patch.object(routes, "_TICK_SECONDS", 0.01),
        ):
            res = run(routes.erp_bridge_lease(routes.LeaseRequest(), FakeRequest()))
        self.assertEqual(res["jobs"], [])
        self.assertGreater(lease.call_count, 1)  # 挂起期间反复探,不是问一次就走

    def test_zero_window_still_polls_once(self):
        with (
            mock.patch.object(routes.store, "authenticate", return_value=BRIDGE),
            mock.patch.object(routes.store, "lease_jobs", return_value=[]) as lease,
            mock.patch.object(routes, "poll_hold_seconds", return_value=0),
        ):
            res = run(routes.erp_bridge_lease(routes.LeaseRequest(), FakeRequest()))
        self.assertEqual(res["jobs"], [])
        self.assertEqual(lease.call_count, 1)

    def test_max_is_capped_by_the_model(self):
        with self.assertRaises(Exception):
            routes.LeaseRequest(max=99)


class AckTests(unittest.TestCase):
    def test_ack_forwards_result_to_store(self):
        with (
            mock.patch.object(routes.store, "authenticate", return_value=BRIDGE),
            mock.patch.object(
                routes.store, "finish_job", return_value={"ok": True, "status": "done"}
            ) as finish,
        ):
            res = run(
                routes.erp_bridge_ack(
                    routes.AckRequest(job_id=JOB_ID, ok=True, result={"rows": []}), FakeRequest()
                )
            )
        self.assertEqual(res["status"], "done")
        args = finish.call_args.args
        self.assertEqual(args[1], JOB_ID)
        self.assertTrue(args[2])
        self.assertEqual(args[3], {"rows": []})

    def test_unknown_job_is_409(self):
        with (
            mock.patch.object(routes.store, "authenticate", return_value=BRIDGE),
            mock.patch.object(
                routes.store, "finish_job", return_value={"ok": False, "reason": "job_not_found"}
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                run(routes.erp_bridge_ack(routes.AckRequest(job_id=JOB_ID, ok=True), FakeRequest()))
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("job_not_found", ctx.exception.detail)


class AdminTests(unittest.TestCase):
    def test_mint_requires_org_edit_and_returns_plaintext_once(self):
        minted = {"bridge_id": BRIDGE_A, "token": "brg_x_y", "tail": "x_y", "role": "read"}
        with (
            mock.patch.object(
                routes, "require_perm", return_value={"id": "u1", "tenant_id": TENANT}
            ) as perm,
            mock.patch.object(routes.store, "mint_bridge", return_value=minted),
        ):
            res = run(routes.erp_bridge_mint(routes.MintRequest(name="所里那台NAS"), FakeRequest()))
        self.assertEqual(perm.call_args.args[1], "settings.org.edit")
        self.assertEqual(res["token"], "brg_x_y")
        self.assertIn("once", res["note"])

    def test_mint_without_tenant_is_403(self):
        with mock.patch.object(routes, "require_perm", return_value={"id": "u1"}):
            with self.assertRaises(HTTPException) as ctx:
                run(routes.erp_bridge_mint(routes.MintRequest(name="x"), FakeRequest()))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_list_uses_view_code_and_never_leaks_secret(self):
        status = {
            "configured": True,
            "online": True,
            "writer": None,
            "bridges": [{"bridge_id": BRIDGE_A, "name": "nas", "online": True}],
        }
        from services.erp.bridge import client as bridge_client

        with (
            mock.patch.object(
                routes, "require_perm", return_value={"id": "u1", "tenant_id": TENANT}
            ) as perm,
            mock.patch.object(bridge_client, "bridge_status", return_value=status),
        ):
            res = run(routes.erp_bridge_list(FakeRequest()))
        self.assertEqual(perm.call_args.args[1], "settings.org.view")
        self.assertTrue(res["ok"])
        self.assertNotIn("secret_hash", str(res))


class RegistrationTests(unittest.TestCase):
    def test_all_five_routes_registered(self):
        paths = {(r.path, tuple(sorted(r.methods))) for r in routes.router.routes}
        for path, method in (
            ("/api/erp/bridge/hello", "POST"),
            ("/api/erp/bridge/lease", "POST"),
            ("/api/erp/bridge/ack", "POST"),
            ("/api/erp/bridges", "POST"),
            ("/api/erp/bridges", "GET"),
        ):
            self.assertIn((path, (method,)), paths)

    def test_bridge_endpoints_are_whitelisted_in_authz_gate(self):
        # 桥没有网页会话(Bearer 密钥即凭证)→ 覆盖闸必须显式认得它们,不能靠"忘了登记"混过。
        from scripts.check_authz_coverage import PUBLIC_ROUTES

        for path in ("hello", "lease", "ack"):
            self.assertIn(("POST", f"/api/erp/bridge/{path}"), PUBLIC_ROUTES)

    def test_router_is_mounted_on_the_app(self):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        os.environ.setdefault("JWT_SECRET", "bridge-dummy-secret-16chars")
        from app import app

        self.assertIn("/api/erp/bridge/lease", {r.path for r in app.routes})


if __name__ == "__main__":
    unittest.main(verbosity=2)

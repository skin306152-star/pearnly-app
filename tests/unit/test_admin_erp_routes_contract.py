# -*- coding: utf-8 -*-
"""admin_erp_routes 契约(erp_portal 闸发放侧 · 照 admin_dms_routes 范式)。

锁定:3 路由 path+method 契约;app include_router 挂上;全路由复用
route_helpers._require_super_admin 单一来源(非超管一律 403)。业务层重点钉死
tenant-first 判据(core/feature_flags.erp_portal_enabled_for 同一口径:有 tenant_id 写
tenant_id,没有才退回 user_id——写反了闸永远判不中且查不出根因)、名单的 invited 状态、
重复邀请幂等、建号后自动进名单、一次性密码只在响应回显一次(不进 _log_op details)。
"""

import contextlib
import unittest
from unittest import mock


from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_erp_routes
from routes.admin_erp_routes import router


class _SeqCursor:
    """按调用顺序吐出预置的 fetchall 结果 · 记录每次 execute 的 SQL/参数便于断言。"""

    def __init__(self, fetchall_results=None):
        self._fetchall = list(fetchall_results or [])
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchall(self):
        return self._fetchall.pop(0) if self._fetchall else []


@contextlib.contextmanager
def _cursor_cm(cur):
    yield cur


class RoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(
            got,
            {
                ("GET", "/api/admin/erp/overview"),
                ("POST", "/api/admin/erp/invite"),
                ("POST", "/api/admin/erp/revoke"),
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/erp/overview", paths)
        self.assertIn("/api/admin/erp/invite", paths)
        self.assertIn("/api/admin/erp/revoke", paths)

    def test_super_admin_guard_single_source(self):
        self.assertIs(
            admin_erp_routes._require_super_admin,
            route_helpers._require_super_admin,
        )

    def test_gate_key_is_erp_portal(self):
        from core.feature_flags import ERP_PORTAL_KEY

        self.assertEqual(admin_erp_routes.ERP_PORTAL_KEY, ERP_PORTAL_KEY)
        self.assertEqual(ERP_PORTAL_KEY, "erp_portal")


class GuardEnforcedTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def _as_non_super(self):
        return mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"is_super_admin": False},
        )

    def test_overview_non_super_403(self):
        with self._as_non_super():
            r = self.client.get("/api/admin/erp/overview")
        self.assertEqual(r.status_code, 403)

    def test_invite_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/erp/invite", json={"username_or_email": "x@y.com"})
        self.assertEqual(r.status_code, 403)

    def test_revoke_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/erp/revoke", json={"subject_id": "t1"})
        self.assertEqual(r.status_code, 403)


class OverviewTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._su = mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "earn", "is_super_admin": True},
        )
        self._su.start()
        self.addCleanup(self._su.stop)

    def test_overview_shape_empty(self):
        with (
            mock.patch.object(
                admin_erp_routes.platform_settings_store, "get_setting", return_value=None
            ),
            mock.patch.object(
                admin_erp_routes.db,
                "get_cursor",
                lambda *a, **k: _cursor_cm(_SeqCursor([[]])),
            ),
        ):
            r = self.client.get("/api/admin/erp/overview")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["flag"]["enabled"])
        self.assertEqual(body["flag"]["rollout"], "allowlist")
        self.assertEqual(body["allowlist"], [])

    def test_overview_enriches_tenant_subject_and_reports_invited(self):
        cur = _SeqCursor(
            [
                [{"subject_id": "tenant-1", "created_at": None}],  # allowlist rows
                [
                    {
                        "subject_id": "tenant-1",
                        "company_name": "Acme",
                        "username": "boss",
                        "email": "boss@acme.com",
                    }
                ],  # tenant join
                [],  # user fallback (unused, tenant already matched)
            ]
        )
        with (
            mock.patch.object(
                admin_erp_routes.platform_settings_store,
                "get_setting",
                return_value={"enabled": True, "value": {"rollout": "all"}, "updated_at": None},
            ),
            mock.patch.object(admin_erp_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)),
        ):
            r = self.client.get("/api/admin/erp/overview")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["flag"]["enabled"])
        self.assertEqual(body["flag"]["rollout"], "all")
        self.assertEqual(len(body["allowlist"]), 1)
        row = body["allowlist"][0]
        self.assertTrue(row["invited"])
        self.assertEqual(row["subject_id"], "tenant-1")
        self.assertEqual(row["subject_type"], "tenant")
        self.assertEqual(row["company_name"], "Acme")
        self.assertEqual(row["username"], "boss")


class InviteExistingUserTests(unittest.TestCase):
    """tenant-first 判据钉死:有 tenant_id 必须写 tenant_id,没有才退回 user_id。"""

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._su = mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "earn", "is_super_admin": True},
        )
        self._su.start()
        self.addCleanup(self._su.stop)

    def test_invite_existing_user_with_tenant_writes_tenant_id(self):
        existing = {"id": "user-1", "tenant_id": "tenant-9", "username": "member1"}
        with (
            mock.patch.object(admin_erp_routes.db, "find_user_by_username", return_value=existing),
            mock.patch.object(
                admin_erp_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_erp_routes, "grant_entrance_safe") as m_grant,
            mock.patch.object(admin_erp_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/erp/invite", json={"username_or_email": "member1"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["created_account"])
        self.assertEqual(body["subject_id"], "tenant-9")
        m_add.assert_called_once_with("erp_portal", "tenant-9")
        # 授权入口发的是 erp 门(不是 ai/dms)· tenant_id 透传。
        self.assertEqual(m_grant.call_args.args[0], admin_erp_routes.ERP)
        self.assertEqual(m_grant.call_args.args[1], "tenant-9")
        self.assertEqual(m_log.call_args.kwargs.get("target_type"), "tenant")
        self.assertEqual(m_log.call_args.kwargs.get("target_id"), "tenant-9")

    def test_invite_existing_user_only_adds_allowlist_not_credit(self):
        """存量号只加名单,不动余额(别给已有号乱加钱)。"""
        existing = {"id": "user-1", "tenant_id": "tenant-9", "username": "member1"}
        with (
            mock.patch.object(admin_erp_routes.db, "find_user_by_username", return_value=existing),
            mock.patch.object(admin_erp_routes.platform_settings_store, "add_to_allowlist"),
            mock.patch.object(admin_erp_routes, "grant_entrance_safe"),
            mock.patch.object(admin_erp_routes, "_log_op"),
            mock.patch.object(admin_erp_routes.db, "grant_credits") as m_grant,
        ):
            r = self.client.post("/api/admin/erp/invite", json={"username_or_email": "member1"})
        self.assertEqual(r.status_code, 200)
        m_grant.assert_not_called()

    def test_invite_existing_user_without_tenant_falls_back_to_user_id(self):
        existing = {"id": "user-orphan", "tenant_id": None, "username": "solo"}
        with (
            mock.patch.object(admin_erp_routes.db, "find_user_by_username", return_value=existing),
            mock.patch.object(
                admin_erp_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_erp_routes, "grant_entrance_safe"),
            mock.patch.object(admin_erp_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/erp/invite", json={"username_or_email": "solo"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["subject_id"], "user-orphan")
        m_add.assert_called_once_with("erp_portal", "user-orphan")
        self.assertEqual(m_log.call_args.kwargs.get("target_type"), "user")

    def test_repeated_invite_is_idempotent(self):
        """重复邀请同一主体不炸、不重复记账:两趟都 200,add_to_allowlist 同一 key+subject。"""
        existing = {"id": "user-1", "tenant_id": "tenant-9", "username": "member1"}
        with (
            mock.patch.object(admin_erp_routes.db, "find_user_by_username", return_value=existing),
            mock.patch.object(
                admin_erp_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_erp_routes, "grant_entrance_safe") as m_grant,
            mock.patch.object(admin_erp_routes, "_log_op"),
        ):
            r1 = self.client.post("/api/admin/erp/invite", json={"username_or_email": "member1"})
            r2 = self.client.post("/api/admin/erp/invite", json={"username_or_email": "member1"})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        # store.add_to_allowlist 内部 ON CONFLICT DO NOTHING 幂等;路由层每趟各调一次。
        self.assertEqual(m_add.call_count, 2)
        for call in m_add.call_args_list:
            self.assertEqual(call.args, ("erp_portal", "tenant-9"))
        # grant_entrance_safe 幂等 upsert,同样每趟各调一次。
        self.assertEqual(m_grant.call_count, 2)


class InviteCreateAccountTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._su = mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "earn", "is_super_admin": True},
        )
        self._su.start()
        self.addCleanup(self._su.stop)

    def test_invite_unknown_email_creates_account_then_invites(self):
        with (
            mock.patch.object(admin_erp_routes.db, "find_user_by_username", return_value=None),
            mock.patch.object(
                admin_erp_routes,
                "create_owner_user",
                return_value={"ok": True, "user_id": "new-user", "tenant_id": "new-tenant"},
            ) as m_create,
            mock.patch.object(
                admin_erp_routes.db,
                "get_cursor",
                lambda *a, **k: _cursor_cm(_SeqCursor([[]])),
            ),
            mock.patch.object(
                admin_erp_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_erp_routes, "grant_entrance_safe") as m_grant,
            mock.patch.object(admin_erp_routes, "_log_op") as m_log,
        ):
            r = self.client.post(
                "/api/admin/erp/invite",
                json={"username_or_email": "newclient@example.com"},
            )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["created_account"])
        self.assertEqual(body["subject_id"], "new-tenant")
        # 一次性密码在响应里 · 长度/字符集过站内强度尺子
        pwd = body["initial_password"]
        self.assertGreaterEqual(len(pwd), 8)
        self.assertTrue(any(c.isalpha() for c in pwd))
        self.assertTrue(any(c.isdigit() for c in pwd))
        m_create.assert_called_once()
        self.assertEqual(m_create.call_args.kwargs["username"], "newclient@example.com")
        self.assertEqual(m_create.call_args.kwargs["notes"], "erp_portal invite")
        # 建完自动进名单(tenant_id 写入)。
        m_add.assert_called_once_with("erp_portal", "new-tenant")
        self.assertEqual(m_grant.call_args.args[0], admin_erp_routes.ERP)
        # 密码绝不进审计 details(硬禁区)
        log_kwargs = m_log.call_args.kwargs
        details_str = str(log_kwargs.get("details") or "")
        self.assertNotIn(pwd, details_str)
        self.assertNotIn(pwd, str(m_log.call_args))

    def test_invite_username_exists_race_returns_409(self):
        with (
            mock.patch.object(admin_erp_routes.db, "find_user_by_username", return_value=None),
            mock.patch.object(
                admin_erp_routes,
                "create_owner_user",
                return_value={"ok": False, "error": "username_exists"},
            ),
        ):
            r = self.client.post(
                "/api/admin/erp/invite", json={"username_or_email": "race@example.com"}
            )
        self.assertEqual(r.status_code, 409)

    def test_invite_username_with_whitespace_422(self):
        r = self.client.post("/api/admin/erp/invite", json={"username_or_email": "has space"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["detail"], "admin.erp_username_invalid")


class RevokeTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._su = mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "earn", "is_super_admin": True},
        )
        self._su.start()
        self.addCleanup(self._su.stop)

    def test_revoke_removes_allowlist_and_entrance_row(self):
        """与 /ai 不同(照 /dms):名单 + tenant_entrances 表行一起摘(revoke_entrance 发 erp 门)。"""
        with (
            mock.patch.object(
                admin_erp_routes,
                "_enrich_subjects",
                return_value={
                    "tenant-1": {
                        "subject_type": "tenant",
                        "username": "boss",
                        "company_name": "Acme",
                    }
                },
            ),
            mock.patch.object(
                admin_erp_routes.platform_settings_store, "remove_from_allowlist"
            ) as m_remove,
            mock.patch.object(admin_erp_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(None)),
            mock.patch.object(admin_erp_routes, "revoke_entrance") as m_rev_ent,
            mock.patch.object(admin_erp_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/erp/revoke", json={"subject_id": "tenant-1"})
        self.assertEqual(r.status_code, 200)
        m_remove.assert_called_once_with("erp_portal", "tenant-1")
        m_rev_ent.assert_called_once()
        self.assertEqual(m_rev_ent.call_args.args[1], "tenant-1")
        self.assertEqual(m_rev_ent.call_args.args[2], admin_erp_routes.ERP)
        self.assertEqual(m_log.call_args.kwargs.get("action"), "erp.revoke")

    def test_revoke_entrance_failure_is_fail_open(self):
        """tenant_entrances 表未建(prod 过渡期)→ revoke_entrance 抛错也不阻断收回主流程。"""
        with (
            mock.patch.object(admin_erp_routes, "_enrich_subjects", return_value={}),
            mock.patch.object(
                admin_erp_routes.platform_settings_store, "remove_from_allowlist"
            ) as m_remove,
            mock.patch.object(admin_erp_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(None)),
            mock.patch.object(
                admin_erp_routes, "revoke_entrance", side_effect=RuntimeError("no table")
            ),
            mock.patch.object(admin_erp_routes, "_log_op"),
        ):
            r = self.client.post("/api/admin/erp/revoke", json={"subject_id": "tenant-1"})
        self.assertEqual(r.status_code, 200)
        m_remove.assert_called_once_with("erp_portal", "tenant-1")

    def test_revoke_missing_subject_400(self):
        r = self.client.post("/api/admin/erp/revoke", json={"subject_id": "  "})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()

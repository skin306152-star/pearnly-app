# -*- coding: utf-8 -*-
"""admin_dms_routes 契约(dms_portal 闸发放侧 · 照 admin_pearnly_ai_routes 范式)。

锁定:4 路由 path+method 契约;app include_router 挂上;全路由复用
route_helpers._require_super_admin 单一来源(非超管一律 403)。业务层重点钉死
tenant-first 判据(core/feature_flags.dms_portal_enabled_for 同一口径:有 tenant_id 写
tenant_id,没有才退回 user_id——写反了闸永远判不中且查不出根因)、一次性密码只在响应回显
一次(不进 _log_op details)。

与 /ai 邀请刻意不同处也钉死:① 闸键 dms_portal;② revoke 除摘名单外还调 revoke_entrance
摘 tenant_entrances 表行(名单外账号不能再从表侧登 /dms 门);③ reset 仅限 allowlist 名单内。
"""

import contextlib
import unittest
from unittest import mock


from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_dms_routes
from routes.admin_dms_routes import router


class _SeqCursor:
    """按调用顺序吐出预置的 fetchall 结果 · 记录每次 execute 的 SQL/参数便于断言。"""

    def __init__(self, fetchall_results=None):
        self._fetchall = list(fetchall_results or [])
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchall(self):
        return self._fetchall.pop(0) if self._fetchall else []


class _OneRowCursor:
    """支持 fetchone 的游标 · 用于 _resolve_target_user 的 tenant 反查 + 密码 UPDATE。"""

    def __init__(self, row=None):
        self._row = row
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchone(self):
        return self._row


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
                ("GET", "/api/admin/dms/overview"),
                ("POST", "/api/admin/dms/invite"),
                ("POST", "/api/admin/dms/revoke"),
                ("POST", "/api/admin/dms/reset-password"),
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/dms/overview", paths)
        self.assertIn("/api/admin/dms/invite", paths)
        self.assertIn("/api/admin/dms/revoke", paths)
        self.assertIn("/api/admin/dms/reset-password", paths)

    def test_super_admin_guard_single_source(self):
        self.assertIs(
            admin_dms_routes._require_super_admin,
            route_helpers._require_super_admin,
        )

    def test_gate_key_is_dms_portal(self):
        from core.feature_flags import DMS_PORTAL_KEY

        self.assertEqual(admin_dms_routes.DMS_PORTAL_KEY, DMS_PORTAL_KEY)
        self.assertEqual(DMS_PORTAL_KEY, "dms_portal")


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
            r = self.client.get("/api/admin/dms/overview")
        self.assertEqual(r.status_code, 403)

    def test_invite_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/dms/invite", json={"username_or_email": "x@y.com"})
        self.assertEqual(r.status_code, 403)

    def test_revoke_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/dms/revoke", json={"subject_id": "t1"})
        self.assertEqual(r.status_code, 403)

    def test_reset_password_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/dms/reset-password", json={"subject_id": "t1"})
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
                admin_dms_routes.platform_settings_store, "get_setting", return_value=None
            ),
            mock.patch.object(
                admin_dms_routes.db,
                "get_cursor",
                lambda *a, **k: _cursor_cm(_SeqCursor([[]])),
            ),
        ):
            r = self.client.get("/api/admin/dms/overview")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["flag"]["enabled"])
        self.assertEqual(body["flag"]["rollout"], "allowlist")
        self.assertEqual(body["allowlist"], [])

    def test_overview_enriches_tenant_subject(self):
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
                admin_dms_routes.platform_settings_store,
                "get_setting",
                return_value={"enabled": True, "value": {"rollout": "all"}, "updated_at": None},
            ),
            mock.patch.object(admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)),
        ):
            r = self.client.get("/api/admin/dms/overview")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["flag"]["enabled"])
        self.assertEqual(body["flag"]["rollout"], "all")
        self.assertEqual(len(body["allowlist"]), 1)
        row = body["allowlist"][0]
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
            mock.patch.object(admin_dms_routes.db, "find_user_by_username", return_value=existing),
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_dms_routes, "grant_entrance_safe") as m_grant,
            mock.patch.object(admin_dms_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/dms/invite", json={"username_or_email": "member1"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["created_account"])
        self.assertEqual(body["subject_id"], "tenant-9")
        m_add.assert_called_once_with("dms_portal", "tenant-9")
        # 授权入口发的是 DMS 门(不是 AI)· tenant_id 透传。
        self.assertEqual(m_grant.call_args.args[0], admin_dms_routes.DMS)
        self.assertEqual(m_grant.call_args.args[1], "tenant-9")
        self.assertEqual(m_log.call_args.kwargs.get("target_type"), "tenant")
        self.assertEqual(m_log.call_args.kwargs.get("target_id"), "tenant-9")

    def test_invite_existing_user_does_not_grant_credit(self):
        """H:存量号只加名单,不动余额(别给已有号乱加钱)。"""
        existing = {"id": "user-1", "tenant_id": "tenant-9", "username": "member1"}
        with (
            mock.patch.object(admin_dms_routes.db, "find_user_by_username", return_value=existing),
            mock.patch.object(admin_dms_routes.platform_settings_store, "add_to_allowlist"),
            mock.patch.object(admin_dms_routes, "grant_entrance_safe"),
            mock.patch.object(admin_dms_routes, "_log_op"),
            mock.patch.object(admin_dms_routes.db, "grant_credits") as m_grant,
        ):
            r = self.client.post("/api/admin/dms/invite", json={"username_or_email": "member1"})
        self.assertEqual(r.status_code, 200)
        m_grant.assert_not_called()

    def test_invite_existing_user_without_tenant_falls_back_to_user_id(self):
        existing = {"id": "user-orphan", "tenant_id": None, "username": "solo"}
        with (
            mock.patch.object(admin_dms_routes.db, "find_user_by_username", return_value=existing),
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_dms_routes, "grant_entrance_safe"),
            mock.patch.object(admin_dms_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/dms/invite", json={"username_or_email": "solo"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["subject_id"], "user-orphan")
        m_add.assert_called_once_with("dms_portal", "user-orphan")
        self.assertEqual(m_log.call_args.kwargs.get("target_type"), "user")


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

    def test_invite_unknown_email_creates_account_and_reveals_password_once(self):
        with (
            mock.patch.object(admin_dms_routes.db, "find_user_by_username", return_value=None),
            mock.patch.object(
                admin_dms_routes,
                "create_owner_user",
                return_value={"ok": True, "user_id": "new-user", "tenant_id": "new-tenant"},
            ) as m_create,
            mock.patch.object(
                admin_dms_routes.db,
                "get_cursor",
                lambda *a, **k: _cursor_cm(_SeqCursor([[]])),
            ),
            mock.patch.object(admin_dms_routes.db, "grant_credits"),
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_dms_routes, "grant_entrance_safe"),
            mock.patch.object(admin_dms_routes, "_log_op") as m_log,
        ):
            r = self.client.post(
                "/api/admin/dms/invite",
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
        self.assertEqual(m_create.call_args.kwargs["notes"], "dms_portal invite")
        m_add.assert_called_once_with("dms_portal", "new-tenant")
        # 密码绝不进审计 details(硬禁区)
        log_kwargs = m_log.call_args.kwargs
        details_str = str(log_kwargs.get("details") or "")
        self.assertNotIn(pwd, details_str)
        self.assertNotIn(pwd, str(m_log.call_args))

    def test_invite_unknown_plain_username_creates_account(self):
        """自由邀请制:任意用户名直接建号,不强制邮箱;非邮箱不写 users.email(不跑 email UPDATE)。"""
        rec = _SeqCursor([[]])
        with (
            mock.patch.object(admin_dms_routes.db, "find_user_by_username", return_value=None),
            mock.patch.object(
                admin_dms_routes,
                "create_owner_user",
                return_value={"ok": True, "user_id": "new-user", "tenant_id": "new-tenant"},
            ) as m_create,
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(rec)),
            mock.patch.object(admin_dms_routes.db, "grant_credits") as m_grant_credits,
            mock.patch.object(admin_dms_routes, "grant_entrance_safe"),
            mock.patch.object(admin_dms_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/dms/invite", json={"username_or_email": "plainusername"}
            )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["created_account"])
        self.assertEqual(body["username"], "plainusername")
        self.assertEqual(m_create.call_args.kwargs["username"], "plainusername")
        m_add.assert_called_once_with("dms_portal", "new-tenant")
        # 非邮箱:不跑 users.email UPDATE(录到的 SQL 里不该有 email 更新)。
        self.assertFalse(
            any("UPDATE users SET email" in (sql or "") for sql, _ in rec.queries),
            "非邮箱用户名不该更新 users.email",
        )
        # 但初始额度照发(开箱即能识别)。
        m_grant_credits.assert_called_once()

    def test_invite_creates_account_grants_initial_credit(self):
        """H:新号开箱发初始额度(否则余额 0 被身份证识别余额闸 402 恒拦)。
        走 canonical 记账口 db.grant_credits · 正额 adjustment(不计 topup 收入 KPI)。"""
        with (
            mock.patch.object(admin_dms_routes.db, "find_user_by_username", return_value=None),
            mock.patch.object(
                admin_dms_routes,
                "create_owner_user",
                return_value={"ok": True, "user_id": "new-user", "tenant_id": "new-tenant"},
            ),
            mock.patch.object(
                admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(_SeqCursor([[]]))
            ),
            mock.patch.object(admin_dms_routes.db, "grant_credits") as m_grant,
            mock.patch.object(admin_dms_routes.platform_settings_store, "add_to_allowlist"),
            mock.patch.object(admin_dms_routes, "grant_entrance_safe"),
            mock.patch.object(admin_dms_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/dms/invite", json={"username_or_email": "fresh@example.com"}
            )
        self.assertEqual(r.status_code, 200)
        m_grant.assert_called_once()
        kw = m_grant.call_args.kwargs
        self.assertEqual(kw["tenant_id"], "new-tenant")
        self.assertEqual(kw["txn_type"], "adjustment")
        self.assertEqual(kw["amount_thb"], admin_dms_routes._DMS_INITIAL_CREDIT_THB)
        self.assertGreater(kw["amount_thb"], 0)  # 正额 → 余额闸能过

    def test_invite_username_exists_race_returns_409(self):
        with (
            mock.patch.object(admin_dms_routes.db, "find_user_by_username", return_value=None),
            mock.patch.object(
                admin_dms_routes,
                "create_owner_user",
                return_value={"ok": False, "error": "username_exists"},
            ),
        ):
            r = self.client.post(
                "/api/admin/dms/invite", json={"username_or_email": "race@example.com"}
            )
        self.assertEqual(r.status_code, 409)

    def test_invite_username_with_whitespace_422(self):
        r = self.client.post("/api/admin/dms/invite", json={"username_or_email": "has space"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["detail"], "admin.dms_username_invalid")


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
        """/ai 之上多摘一步:名单 + tenant_entrances 表行一起摘(revoke_entrance 发 DMS 门)。"""
        with (
            mock.patch.object(
                admin_dms_routes,
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
                admin_dms_routes.platform_settings_store, "remove_from_allowlist"
            ) as m_remove,
            mock.patch.object(
                admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(_OneRowCursor())
            ),
            mock.patch.object(admin_dms_routes, "revoke_entrance") as m_rev_ent,
            mock.patch.object(admin_dms_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/dms/revoke", json={"subject_id": "tenant-1"})
        self.assertEqual(r.status_code, 200)
        m_remove.assert_called_once_with("dms_portal", "tenant-1")
        m_rev_ent.assert_called_once()
        self.assertEqual(m_rev_ent.call_args.args[1], "tenant-1")
        self.assertEqual(m_rev_ent.call_args.args[2], admin_dms_routes.DMS)
        self.assertEqual(m_log.call_args.kwargs.get("action"), "dms.revoke")

    def test_revoke_entrance_failure_is_fail_open(self):
        """tenant_entrances 表未建(prod 过渡期)→ revoke_entrance 抛错也不阻断收回主流程。"""
        with (
            mock.patch.object(admin_dms_routes, "_enrich_subjects", return_value={}),
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "remove_from_allowlist"
            ) as m_remove,
            mock.patch.object(
                admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(_OneRowCursor())
            ),
            mock.patch.object(
                admin_dms_routes, "revoke_entrance", side_effect=RuntimeError("no table")
            ),
            mock.patch.object(admin_dms_routes, "_log_op"),
        ):
            r = self.client.post("/api/admin/dms/revoke", json={"subject_id": "tenant-1"})
        self.assertEqual(r.status_code, 200)
        m_remove.assert_called_once_with("dms_portal", "tenant-1")

    def test_revoke_missing_subject_400(self):
        r = self.client.post("/api/admin/dms/revoke", json={"subject_id": "  "})
        self.assertEqual(r.status_code, 400)


class ResetPasswordTests(unittest.TestCase):
    """DMS 邀请账号密码重置 —— 严格闸在 allowlist 名单内,不是通用改密能力复活。"""

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

    def test_reset_password_subject_not_in_allowlist_404(self):
        with mock.patch.object(
            admin_dms_routes.platform_settings_store, "is_allowlisted", return_value=False
        ):
            r = self.client.post("/api/admin/dms/reset-password", json={"subject_id": "tenant-9"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "admin.dms_not_invited")

    def test_reset_password_tenant_subject_returns_password_not_logged(self):
        cur = _OneRowCursor({"owner_user_id": "user-9"})
        with (
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "is_allowlisted", return_value=True
            ),
            mock.patch.object(admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)),
            mock.patch.object(
                admin_dms_routes.db,
                "find_user_by_id",
                return_value={"id": "user-9", "username": "boss", "tenant_id": "tenant-9"},
            ),
            mock.patch.object(
                admin_dms_routes.db, "reset_user_password", return_value=True
            ) as m_reset,
            mock.patch.object(admin_dms_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/dms/reset-password", json={"subject_id": "tenant-9"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["username"], "boss")
        pwd = body["initial_password"]
        self.assertGreaterEqual(len(pwd), 8)
        m_reset.assert_called_once_with("user-9", pwd)
        self.assertNotIn(pwd, str(m_log.call_args))

    def test_reset_password_subject_unknown_404(self):
        cur = _OneRowCursor(None)
        with (
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "is_allowlisted", return_value=True
            ),
            mock.patch.object(admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)),
            mock.patch.object(admin_dms_routes.db, "find_user_by_id", return_value=None),
        ):
            r = self.client.post("/api/admin/dms/reset-password", json={"subject_id": "ghost-id"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "admin.dms_subject_unknown")

    def test_reset_password_custom_password_passed_through(self):
        cur = _OneRowCursor(None)
        with (
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "is_allowlisted", return_value=True
            ),
            mock.patch.object(admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)),
            mock.patch.object(
                admin_dms_routes.db,
                "find_user_by_id",
                return_value={"id": "user-orphan", "username": "solo", "tenant_id": None},
            ),
            mock.patch.object(
                admin_dms_routes.db, "reset_user_password", return_value=True
            ) as m_reset,
            mock.patch.object(admin_dms_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/dms/reset-password",
                json={"subject_id": "user-orphan", "password": "Zihao2026x"},
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["initial_password"], "Zihao2026x")
        m_reset.assert_called_once_with("user-orphan", "Zihao2026x")

    def test_reset_password_blank_falls_back_to_random_strong_password(self):
        cur = _OneRowCursor(None)
        with (
            mock.patch.object(
                admin_dms_routes.platform_settings_store, "is_allowlisted", return_value=True
            ),
            mock.patch.object(admin_dms_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)),
            mock.patch.object(
                admin_dms_routes.db,
                "find_user_by_id",
                return_value={"id": "user-orphan", "username": "solo", "tenant_id": None},
            ),
            mock.patch.object(admin_dms_routes.db, "reset_user_password", return_value=True),
            mock.patch.object(admin_dms_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/dms/reset-password", json={"subject_id": "user-orphan"}
            )
        self.assertEqual(r.status_code, 200)
        pwd = r.json()["initial_password"]
        self.assertIsNone(route_helpers._check_password_strength(pwd))


if __name__ == "__main__":
    unittest.main()

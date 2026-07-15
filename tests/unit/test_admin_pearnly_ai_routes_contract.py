# -*- coding: utf-8 -*-
"""admin_pearnly_ai_routes 契约(Z1-b/Z1-c · pearnly_ai_m1 闸发放侧)。

锁定:4 路由 path+method 契约;app include_router 挂上;全路由复用
route_helpers._require_super_admin 单一来源(非超管一律 403)。业务层重点钉死
tenant-first 判据(core/feature_flags.pearnly_ai_m1_enabled_for 同一口径:有
tenant_id 写 tenant_id,没有才退回 user_id——写反了闸永远判不中且查不出根因)、
一次性密码只在响应回显一次(不进 _log_op details)。

reset-password(Z1-c)额外钉死:仅限 allowlist 名单内 subject(不复活已被砍掉的
通用超管改密 /api/admin/users/{id}/reset-password);自定义密码走
_check_password_strength 同一把尺子,弱密码 422、留空落回随机一次性密码。
"""

import contextlib
import unittest
from unittest import mock


from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_pearnly_ai_routes
from routes.admin_pearnly_ai_routes import router


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
    """支持 fetchone 的游标 · 用于 _resolve_target_user 的 tenant 反查 + 密码 UPDATE。

    reset-password 一次请求里 db.get_cursor() 被调用两次(反查 owner_user_id、
    写 password_hash),两次都拿同一个游标实例——fetchone 只有第一次查询用得上,
    UPDATE 那次只调 execute,互不干扰。
    """

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
                ("GET", "/api/admin/pearnly-ai/overview"),
                ("POST", "/api/admin/pearnly-ai/invite"),
                ("POST", "/api/admin/pearnly-ai/revoke"),
                ("POST", "/api/admin/pearnly-ai/reset-password"),
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/pearnly-ai/overview", paths)
        self.assertIn("/api/admin/pearnly-ai/invite", paths)
        self.assertIn("/api/admin/pearnly-ai/revoke", paths)
        self.assertIn("/api/admin/pearnly-ai/reset-password", paths)

    def test_super_admin_guard_single_source(self):
        self.assertIs(
            admin_pearnly_ai_routes._require_super_admin,
            route_helpers._require_super_admin,
        )


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
            r = self.client.get("/api/admin/pearnly-ai/overview")
        self.assertEqual(r.status_code, 403)

    def test_invite_non_super_403(self):
        with self._as_non_super():
            r = self.client.post(
                "/api/admin/pearnly-ai/invite", json={"username_or_email": "x@y.com"}
            )
        self.assertEqual(r.status_code, 403)

    def test_revoke_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/pearnly-ai/revoke", json={"subject_id": "t1"})
        self.assertEqual(r.status_code, 403)

    def test_reset_password_non_super_403(self):
        with self._as_non_super():
            r = self.client.post("/api/admin/pearnly-ai/reset-password", json={"subject_id": "t1"})
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
                admin_pearnly_ai_routes.platform_settings_store, "get_setting", return_value=None
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db,
                "get_cursor",
                lambda *a, **k: _cursor_cm(_SeqCursor([[]])),
            ),
        ):
            r = self.client.get("/api/admin/pearnly-ai/overview")
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
                admin_pearnly_ai_routes.platform_settings_store,
                "get_setting",
                return_value={"enabled": True, "value": {"rollout": "all"}, "updated_at": None},
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)
            ),
        ):
            r = self.client.get("/api/admin/pearnly-ai/overview")
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
            mock.patch.object(
                admin_pearnly_ai_routes.db, "find_user_by_username", return_value=existing
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_pearnly_ai_routes, "_grant_ai_entrance"),
            mock.patch.object(admin_pearnly_ai_routes, "_log_op") as m_log,
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/invite", json={"username_or_email": "member1"}
            )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["created_account"])
        self.assertEqual(body["subject_id"], "tenant-9")
        m_add.assert_called_once_with("pearnly_ai_m1", "tenant-9")
        self.assertEqual(m_log.call_args.kwargs.get("target_type"), "tenant")
        self.assertEqual(m_log.call_args.kwargs.get("target_id"), "tenant-9")

    def test_invite_existing_user_without_tenant_falls_back_to_user_id(self):
        existing = {"id": "user-orphan", "tenant_id": None, "username": "solo"}
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.db, "find_user_by_username", return_value=existing
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_pearnly_ai_routes, "_grant_ai_entrance"),
            mock.patch.object(admin_pearnly_ai_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/pearnly-ai/invite", json={"username_or_email": "solo"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["subject_id"], "user-orphan")
        m_add.assert_called_once_with("pearnly_ai_m1", "user-orphan")
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
            mock.patch.object(
                admin_pearnly_ai_routes.db, "find_user_by_username", return_value=None
            ),
            mock.patch.object(
                admin_pearnly_ai_routes,
                "create_owner_user",
                return_value={"ok": True, "user_id": "new-user", "tenant_id": "new-tenant"},
            ) as m_create,
            mock.patch.object(
                admin_pearnly_ai_routes.db,
                "get_cursor",
                lambda *a, **k: _cursor_cm(_SeqCursor([[]])),
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_pearnly_ai_routes, "_log_op") as m_log,
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/invite",
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
        m_add.assert_called_once_with("pearnly_ai_m1", "new-tenant")
        # 密码绝不进审计 details(硬禁区)
        log_kwargs = m_log.call_args.kwargs
        details_str = str(log_kwargs.get("details") or "")
        self.assertNotIn(pwd, details_str)
        all_call_text = str(m_log.call_args)
        self.assertNotIn(pwd, all_call_text)

    def test_invite_unknown_plain_username_creates_account(self):
        """自由邀请制(2026-07-10 拍板):任意用户名直接建号,不强制邮箱;
        非邮箱用户名不写 users.email(不跑 UPDATE 游标)。"""
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.db, "find_user_by_username", return_value=None
            ),
            mock.patch.object(
                admin_pearnly_ai_routes,
                "create_owner_user",
                return_value={"ok": True, "user_id": "new-user", "tenant_id": "new-tenant"},
            ) as m_create,
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store, "add_to_allowlist"
            ) as m_add,
            mock.patch.object(admin_pearnly_ai_routes.db, "get_cursor") as m_cur,
            # 授权入口集写钩子(Phase2)自开游标,有独立测试;此处屏蔽以纯验「非邮箱不落 users.email」。
            mock.patch.object(admin_pearnly_ai_routes, "_grant_ai_entrance"),
            mock.patch.object(admin_pearnly_ai_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/invite", json={"username_or_email": "plainusername"}
            )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["created_account"])
        self.assertEqual(body["username"], "plainusername")
        self.assertEqual(m_create.call_args.kwargs["username"], "plainusername")
        m_add.assert_called_once_with("pearnly_ai_m1", "new-tenant")
        m_cur.assert_not_called()  # 非邮箱不落 users.email

    def test_invite_username_exists_race_returns_409(self):
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.db, "find_user_by_username", return_value=None
            ),
            mock.patch.object(
                admin_pearnly_ai_routes,
                "create_owner_user",
                return_value={"ok": False, "error": "username_exists"},
            ),
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/invite", json={"username_or_email": "race@example.com"}
            )
        self.assertEqual(r.status_code, 409)

    def test_invite_username_with_whitespace_422(self):
        """非法用户名(含空白)在打 DB 之前就该被拒——校验复用 account_provision
        单一事实源,与 /pos 开通同口径(2026-07-10 批次 B item 4)。"""
        r = self.client.post(
            "/api/admin/pearnly-ai/invite", json={"username_or_email": "has space"}
        )
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["detail"], "admin.pearnly_ai_username_invalid")

    def test_invite_mixed_case_username_normalized_before_lookup(self):
        """用户名统一 lower 归一后再查重(与 6ab310b8 大小写不敏感登录同口径)。"""
        with mock.patch.object(
            admin_pearnly_ai_routes.db, "find_user_by_username", return_value=None
        ) as m_find:
            with (
                mock.patch.object(
                    admin_pearnly_ai_routes,
                    "create_owner_user",
                    return_value={"ok": True, "user_id": "new-user", "tenant_id": "new-tenant"},
                ),
                mock.patch.object(admin_pearnly_ai_routes, "_log_op"),
                mock.patch.object(
                    admin_pearnly_ai_routes.platform_settings_store, "add_to_allowlist"
                ),
            ):
                r = self.client.post(
                    "/api/admin/pearnly-ai/invite", json={"username_or_email": "MemberOne"}
                )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["username"], "memberone")
        m_find.assert_called_once_with("memberone")


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

    def test_revoke_removes_from_allowlist_not_account(self):
        with (
            mock.patch.object(
                admin_pearnly_ai_routes,
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
                admin_pearnly_ai_routes.platform_settings_store, "remove_from_allowlist"
            ) as m_remove,
            mock.patch.object(admin_pearnly_ai_routes, "_log_op") as m_log,
        ):
            r = self.client.post("/api/admin/pearnly-ai/revoke", json={"subject_id": "tenant-1"})
        self.assertEqual(r.status_code, 200)
        m_remove.assert_called_once_with("pearnly_ai_m1", "tenant-1")
        self.assertEqual(m_log.call_args.kwargs.get("action"), "pearnly_ai.revoke")

    def test_revoke_missing_subject_400(self):
        r = self.client.post("/api/admin/pearnly-ai/revoke", json={"subject_id": "  "})
        self.assertEqual(r.status_code, 400)


class ResetPasswordTests(unittest.TestCase):
    """/ai 邀请账号密码重置 —— 严格闸在 allowlist 名单内,不是通用改密能力复活。"""

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
            admin_pearnly_ai_routes.platform_settings_store, "is_allowlisted", return_value=False
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/reset-password", json={"subject_id": "tenant-9"}
            )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "admin.pearnly_ai_not_invited")

    def test_reset_password_tenant_subject_returns_password_not_logged(self):
        # allowlist 存的是 tenant_id · _resolve_target_user 先查 tenants.owner_user_id
        # 再反查 user 行;写库必须走 db.reset_user_password(同步刷 password_changed_at
        # → 旧 JWT 全失效 · 铁律 v118.28.9),不许路由层手写 bcrypt+UPDATE 绕过。
        cur = _OneRowCursor({"owner_user_id": "user-9"})
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store,
                "is_allowlisted",
                return_value=True,
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db,
                "find_user_by_id",
                return_value={"id": "user-9", "username": "boss", "tenant_id": "tenant-9"},
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "reset_user_password", return_value=True
            ) as m_reset,
            mock.patch.object(admin_pearnly_ai_routes, "_log_op") as m_log,
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/reset-password", json={"subject_id": "tenant-9"}
            )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["username"], "boss")
        pwd = body["initial_password"]
        self.assertGreaterEqual(len(pwd), 8)
        m_reset.assert_called_once_with("user-9", pwd)
        # 密码绝不进审计 details/日志(硬禁区,跟 invite 建号一样)
        self.assertNotIn(pwd, str(m_log.call_args))

    def test_reset_password_user_subject_without_tenant_200(self):
        cur = _OneRowCursor(None)  # tenant 反查落空 → 落回当 user_id 直查
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store,
                "is_allowlisted",
                return_value=True,
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db,
                "find_user_by_id",
                return_value={"id": "user-orphan", "username": "solo", "tenant_id": None},
            ),
            mock.patch.object(admin_pearnly_ai_routes.db, "reset_user_password", return_value=True),
            mock.patch.object(admin_pearnly_ai_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/reset-password", json={"subject_id": "user-orphan"}
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["username"], "solo")

    def test_reset_password_subject_unknown_404(self):
        cur = _OneRowCursor(None)
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store,
                "is_allowlisted",
                return_value=True,
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)
            ),
            mock.patch.object(admin_pearnly_ai_routes.db, "find_user_by_id", return_value=None),
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/reset-password", json={"subject_id": "ghost-id"}
            )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "admin.pearnly_ai_subject_unknown")

    def test_reset_password_custom_strong_password_passed_through(self):
        """Zihao 追加拍板:超管自定义密码 → 原样交给 db.reset_user_password 落库
        (bcrypt 哈希/password_changed_at 刷新是该 helper 自己的契约,不在路由层重验)。"""
        cur = _OneRowCursor(None)
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store,
                "is_allowlisted",
                return_value=True,
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db,
                "find_user_by_id",
                return_value={"id": "user-orphan", "username": "solo", "tenant_id": None},
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "reset_user_password", return_value=True
            ) as m_reset,
            mock.patch.object(admin_pearnly_ai_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/reset-password",
                json={"subject_id": "user-orphan", "password": "Zihao2026x"},
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["initial_password"], "Zihao2026x")
        m_reset.assert_called_once_with("user-orphan", "Zihao2026x")

    def test_reset_password_weak_custom_password_422(self):
        """弱密码在反解目标用户之前就该被拒 —— 不合格直接 422,不用打 DB。"""
        with mock.patch.object(
            admin_pearnly_ai_routes.platform_settings_store,
            "is_allowlisted",
            return_value=True,
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/reset-password",
                json={"subject_id": "user-orphan", "password": "12345678"},
            )
        self.assertEqual(r.status_code, 422)

    def test_reset_password_blank_falls_back_to_random_strong_password(self):
        cur = _OneRowCursor(None)
        with (
            mock.patch.object(
                admin_pearnly_ai_routes.platform_settings_store,
                "is_allowlisted",
                return_value=True,
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db, "get_cursor", lambda *a, **k: _cursor_cm(cur)
            ),
            mock.patch.object(
                admin_pearnly_ai_routes.db,
                "find_user_by_id",
                return_value={"id": "user-orphan", "username": "solo", "tenant_id": None},
            ),
            mock.patch.object(admin_pearnly_ai_routes.db, "reset_user_password", return_value=True),
            mock.patch.object(admin_pearnly_ai_routes, "_log_op"),
        ):
            r = self.client.post(
                "/api/admin/pearnly-ai/reset-password", json={"subject_id": "user-orphan"}
            )
        self.assertEqual(r.status_code, 200)
        pwd = r.json()["initial_password"]
        self.assertIsNone(route_helpers._check_password_strength(pwd))


if __name__ == "__main__":
    unittest.main()

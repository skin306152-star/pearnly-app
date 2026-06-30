# -*- coding: utf-8 -*-
"""WP2 守门 · 平台钥匙闸 4 路由契约 + 超管闸(非超管 403)。

锁定:
  1. router path+method 契约(防丢路由 / 改 URL)
  2. app.py include_router 真挂上
  3. 全路由复用 route_helpers._require_super_admin 单一来源
  4. 非超管访问 → 403;超管 → 200(store 被 mock,不连真库)
"""

import contextlib
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_settings_routes
from routes.admin_settings_routes import router


@contextlib.contextmanager
def _fake_cursor(fetchone_result):
    cur = mock.Mock()
    cur.fetchone.return_value = fetchone_result
    cur.fetchall.return_value = []
    yield cur


class AdminSettingsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/admin/platform-settings"),
            ("POST", "/api/admin/platform-settings"),
            ("POST", "/api/admin/platform-settings/allowlist/add"),
            ("POST", "/api/admin/platform-settings/allowlist/remove"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/platform-settings", paths)

    def test_super_admin_guard_single_source(self):
        self.assertIs(
            admin_settings_routes._require_super_admin,
            route_helpers._require_super_admin,
        )


class AdminSettingsGuardTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_non_super_admin_403(self):
        with mock.patch.object(
            route_helpers, "get_current_user_from_request", return_value={"is_super_admin": False}
        ):
            r = self.client.get("/api/admin/platform-settings")
        self.assertEqual(r.status_code, 403)

    def test_super_admin_reads_settings(self):
        with (
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                return_value={"id": "earn", "is_super_admin": True},
            ),
            mock.patch.object(admin_settings_routes.store, "get_setting", return_value=None),
            mock.patch.object(admin_settings_routes.store, "list_allowlist", return_value=[]),
        ):
            r = self.client.get("/api/admin/platform-settings")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["agent_enabled"]["enabled"])
        self.assertEqual(body["agent_enabled"]["rollout"], "allowlist")
        self.assertEqual(body["allowlist"], [])

    def test_super_admin_sets_toggle(self):
        with (
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                return_value={"id": "earn", "is_super_admin": True},
            ),
            mock.patch.object(admin_settings_routes.store, "set_setting") as m_set,
        ):
            r = self.client.post(
                "/api/admin/platform-settings", json={"enabled": True, "rollout": "all"}
            )
        self.assertEqual(r.status_code, 200)
        m_set.assert_called_once()
        # value 携带 rollout · enabled True · by=操作超管
        args, kwargs = m_set.call_args
        self.assertEqual(args[0], "agent_enabled")
        self.assertEqual(args[1], {"rollout": "all"})
        self.assertTrue(args[2])

    def test_bad_rollout_rejected(self):
        with mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "earn", "is_super_admin": True},
        ):
            r = self.client.post(
                "/api/admin/platform-settings", json={"enabled": True, "rollout": "bogus"}
            )
        self.assertEqual(r.status_code, 400)


class AllowlistResolveTests(unittest.TestCase):
    """灰度名单加人:支持邮箱(查 users 换 id)、UUID 直通,坏值不再 500。"""

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
        # list_allowlist 返空 → _enrich_users 不碰库,隔离出 resolver 的那次 DB 调用
        self._ll = mock.patch.object(admin_settings_routes.store, "list_allowlist", return_value=[])
        self._ll.start()
        self.addCleanup(self._ll.stop)

    def test_email_resolved_to_user_id(self):
        with (
            mock.patch.object(
                admin_settings_routes.db,
                "get_cursor",
                lambda *a, **k: _fake_cursor({"id": "uuid-skin"}),
            ),
            mock.patch.object(admin_settings_routes.store, "add_to_allowlist") as m_add,
        ):
            r = self.client.post(
                "/api/admin/platform-settings/allowlist/add",
                json={"user_id": "skin306152@gmail.com"},
            )
        self.assertEqual(r.status_code, 200)
        m_add.assert_called_once_with("agent_enabled", "uuid-skin")

    def test_email_not_found_404(self):
        with (
            mock.patch.object(
                admin_settings_routes.db, "get_cursor", lambda *a, **k: _fake_cursor(None)
            ),
            mock.patch.object(admin_settings_routes.store, "add_to_allowlist") as m_add,
        ):
            r = self.client.post(
                "/api/admin/platform-settings/allowlist/add",
                json={"user_id": "ghost@nowhere.com"},
            )
        self.assertEqual(r.status_code, 404)
        m_add.assert_not_called()

    def test_bad_uuid_400_not_500(self):
        with mock.patch.object(admin_settings_routes.store, "add_to_allowlist") as m_add:
            r = self.client.post(
                "/api/admin/platform-settings/allowlist/add",
                json={"user_id": "not-a-uuid"},
            )
        self.assertEqual(r.status_code, 400)
        m_add.assert_not_called()

    def test_valid_uuid_passthrough(self):
        uid = "550e8400-e29b-41d4-a716-446655440000"
        with mock.patch.object(admin_settings_routes.store, "add_to_allowlist") as m_add:
            r = self.client.post(
                "/api/admin/platform-settings/allowlist/add", json={"user_id": uid}
            )
        self.assertEqual(r.status_code, 200)
        m_add.assert_called_once_with("agent_enabled", uid)


if __name__ == "__main__":
    unittest.main()

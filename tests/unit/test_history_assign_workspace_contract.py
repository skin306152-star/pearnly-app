# -*- coding: utf-8 -*-
"""识别记录改归属套账路由守门(POST /api/history/{id}/assign_workspace)。

锁定:
  1. 路由存在且挂在 history router 上
  2. 只许挪到本租户套账(assert_workspace_in_tenant 403 透传)
  3. 必须指定具体套账(缺/空 body → 422,不许清空归属)
  4. 成功路径调 update_history_workspace_client_id 且带租户隔离参数
"""

import contextlib
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import routes.history_routes as hr
from routes.history_routes import router

_USER = {"id": "u-1", "tenant_id": "t-1", "is_super_admin": False, "role": "owner"}


@contextlib.contextmanager
def _cursor_found(found=True):
    cur = mock.Mock()
    cur.fetchone.return_value = {"ok": 1} if found else None
    yield cur


class AssignWorkspaceRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._auth = mock.patch.object(hr, "get_current_user_from_request", return_value=_USER)
        self._auth.start()
        self.addCleanup(self._auth.stop)

    def test_route_registered(self):
        paths = {r.path for r in router.routes if hasattr(r, "path")}
        self.assertIn("/api/history/{history_id}/assign_workspace", paths)

    def test_missing_workspace_id_422(self):
        r = self.client.post("/api/history/h-1/assign_workspace", json={})
        self.assertEqual(r.status_code, 422)

    def test_cross_tenant_workspace_403(self):
        with mock.patch.object(hr.db, "get_cursor", lambda *a, **k: _cursor_found(False)):
            r = self.client.post(
                "/api/history/h-1/assign_workspace", json={"workspace_client_id": 99}
            )
        self.assertEqual(r.status_code, 403)

    def test_success_updates_with_tenant_isolation(self):
        with (
            mock.patch.object(hr.db, "get_cursor", lambda *a, **k: _cursor_found(True)),
            mock.patch.object(
                hr.db, "update_history_workspace_client_id", return_value=True
            ) as m_upd,
        ):
            r = self.client.post(
                "/api/history/h-1/assign_workspace", json={"workspace_client_id": 7}
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True, "workspace_client_id": 7})
        m_upd.assert_called_once_with("h-1", 7, "u-1", tenant_id="t-1")

    def test_update_failure_400(self):
        with (
            mock.patch.object(hr.db, "get_cursor", lambda *a, **k: _cursor_found(True)),
            mock.patch.object(hr.db, "update_history_workspace_client_id", return_value=False),
        ):
            r = self.client.post(
                "/api/history/h-1/assign_workspace", json={"workspace_client_id": 7}
            )
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()

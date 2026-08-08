# -*- coding: utf-8 -*-
"""workspace rebind-history 路由契约(TestClient 打真路由,不直调 handler)。

复核屏「套账不符 → 一键归入」后端地基:POST /api/workspace/rebind-history 把一批
ocr_history 的账套归属重绑到指定套账。锁定:
  1. 目标套账越权(查无)/已归档 → 404 workspace.not_found 且 update 一次不调;
  2. 逐条调 seller_routing.update_history_workspace_client_id,返回 False 的进
     skipped 仍 200(四态诚实,不吞失败);
  3. update 幂等,同参二连调结果一致;
  4. 契约:缺 workspace_client_id / history_ids 空数组 → 422;
  5. 成功路径审计恰好一条,details 数字对。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from routes import workspace_routes as wr  # noqa: E402

_USER = {"id": "u1", "tenant_id": "t-1", "username": "alice", "is_super_admin": False}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(wr.router)
    return TestClient(app)


def _patches(client_row=None, update_result=True):
    return (
        mock.patch.object(wr, "require_perm", return_value=_USER),
        mock.patch.object(wr.db, "get_workspace_client", return_value=client_row),
        mock.patch.object(
            wr.seller_routing, "update_history_workspace_client_id", return_value=update_result
        ),
        mock.patch.object(wr.audit_store, "insert_operation_log", return_value=True),
    )


class RebindHistoryRouteTests(unittest.TestCase):
    def setUp(self):
        self._active = [p.start() for p in _patches()]
        self.addCleanup(mock.patch.stopall)
        self.client = _client()

    def _rebind(self, payload):
        return self.client.post("/api/workspace/rebind-history", json=payload)

    def test_all_success_returns_counts_and_calls_update_per_id(self):
        self._active[1].return_value = {"id": 5, "is_active": True}
        upd = self._active[2]
        r = self._rebind({"history_ids": ["h1", "h2"], "workspace_client_id": 5})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {"ok": True, "rebound": 2, "skipped": []})
        self.assertEqual(
            upd.call_args_list,
            [
                mock.call("h1", 5, "u1", tenant_id="t-1"),
                mock.call("h2", 5, "u1", tenant_id="t-1"),
            ],
        )

    def test_target_workspace_out_of_scope_404_and_update_never_called(self):
        self._active[1].return_value = None
        upd = self._active[2]
        r = self._rebind({"history_ids": ["h1"], "workspace_client_id": 999})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "workspace.not_found")
        upd.assert_not_called()

    def test_archived_target_workspace_404(self):
        self._active[1].return_value = {"id": 5, "is_active": False}
        upd = self._active[2]
        r = self._rebind({"history_ids": ["h1"], "workspace_client_id": 5})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"], "workspace.not_found")
        upd.assert_not_called()

    def test_partial_failure_goes_to_skipped_still_200(self):
        self._active[1].return_value = {"id": 5, "is_active": True}
        self._active[2].side_effect = lambda hid, ws, uid, tenant_id=None: hid != "h2"
        r = self._rebind({"history_ids": ["h1", "h2", "h3"], "workspace_client_id": 5})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {"ok": True, "rebound": 2, "skipped": ["h2"]})

    def test_idempotent_repeat_same_payload_same_result(self):
        self._active[1].return_value = {"id": 5, "is_active": True}
        payload = {"history_ids": ["h1", "h2"], "workspace_client_id": 5}
        r1 = self._rebind(payload)
        r2 = self._rebind(payload)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json(), r2.json())
        self.assertEqual(r2.json(), {"ok": True, "rebound": 2, "skipped": []})

    def test_missing_workspace_client_id_422(self):
        r = self._rebind({"history_ids": ["h1"]})
        self.assertEqual(r.status_code, 422)

    def test_empty_history_ids_422(self):
        r = self._rebind({"history_ids": [], "workspace_client_id": 5})
        self.assertEqual(r.status_code, 422)

    def test_audit_logged_exactly_once_with_counts(self):
        self._active[1].return_value = {"id": 5, "is_active": True}
        self._active[2].side_effect = lambda hid, ws, uid, tenant_id=None: hid == "h1"
        audit = self._active[3]
        r = self._rebind({"history_ids": ["h1", "h2"], "workspace_client_id": 5})
        self.assertEqual(r.status_code, 200, r.text)
        audit.assert_called_once()
        args, kwargs = audit.call_args
        self.assertEqual(args[4], "workspace.rebind_history")
        self.assertEqual(kwargs["target_type"], "workspace_client")
        self.assertEqual(kwargs["target_id"], "5")
        self.assertEqual(
            kwargs["details"],
            {"history_count": 2, "rebound": 1, "skipped": 1},
        )


if __name__ == "__main__":
    unittest.main()

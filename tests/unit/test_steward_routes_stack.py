# -*- coding: utf-8 -*-
"""管家十端点走真 ASGI 栈(routes/steward_routes.py · B3 + 万能口 F1)。

直调 handler 跑绿不等于路由真接上 —— 模型/依赖/注册任一断都只在这层看得出来
(照 test_erp_bridge_routes.AsgiSmokeTests 先例)。锁:①匿名一律不给 200;②消息体
校验在框架层生效(空 text 422,不是等进业务层才发现);③闸关时经全栈仍是 404;
④授权卡「铸卡 → 批准/拒绝」经真路由 + 真 authz 状态机走通(DB 是按真 SQL 分支语义
仿真的 FakeCur —— CI 无 Postgres,SQL 面已在 test_steward_authz 逐分支锁定)。
"""

from __future__ import annotations

import unittest
from unittest import mock

# 第三项是 requests 的关键字参数(json / files / 空)—— 上传口收的是 multipart,拿 json 打
# 它会先吃框架层 422,那样「匿名一律不给 200」就是靠形状校验蒙出来的假绿。
_ENDPOINTS = (
    ("get", "/api/ai/steward/status", {}),
    ("post", "/api/ai/steward/sessions", {"json": {}}),
    ("get", "/api/ai/steward/sessions/s-1", {}),
    ("post", "/api/ai/steward/sessions/s-1/messages", {"json": {"text": "本期谁缺料"}}),
    # 全组里唯一会写磁盘的与唯一会吐文件字节的两条,偏偏最初没进这张表。
    (
        "post",
        "/api/ai/steward/sessions/s-1/attachments",
        {"files": {"files": ("gl.pdf", b"%PDF-1.4", "application/pdf")}},
    ),
    ("get", "/api/ai/steward/attachments/a-1/download", {}),
    ("get", "/api/ai/steward/tasks/t-1", {}),
    ("post", "/api/ai/steward/tasks/t-1/cancel", {"json": {}}),
    ("post", "/api/ai/steward/authorizations/approve", {"json": {"token": "tok-12345678"}}),
    ("post", "/api/ai/steward/authorizations/reject", {"json": {"token": "tok-12345678"}}),
)


def _app():
    import os

    os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
    os.environ.setdefault("JWT_SECRET", "steward-dummy-secret-16chars")
    from app import app

    return app


class AsgiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        cls.client = TestClient(_app())

    def _call(self, method, path, kwargs):
        return getattr(self.client, method)(path, **kwargs)

    def test_no_endpoint_serves_anonymous(self):
        for method, path, kwargs in _ENDPOINTS:
            with self.subTest(path=path, method=method):
                res = self._call(method, path, kwargs)
                self.assertIn(res.status_code, (401, 403, 404))

    def test_empty_message_still_needs_login_before_anything_else(self):
        """F1 起 text 允许为空(纯文件送出是万能口的核心手势),空轮的 422 判在鉴权【之后】
        —— 匿名请求必须先吃 401,绝不能靠形状校验把未登录者挡出一个 422 的假象。"""
        res = self.client.post("/api/ai/steward/sessions/s-1/messages", json={"text": ""})
        self.assertIn(res.status_code, (401, 403, 404))

    def test_gate_closed_is_404_for_a_logged_in_user(self):
        """闸关 = 对存量用户等于不存在。登录态由鉴权 helper 注入,闸判定走真请求路径。"""
        from routes import steward_common as sc
        from routes import steward_routes as sr

        with (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=({"id": "u1"}, "t-1")),
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=({"id": "u1"}, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=False
            ),
        ):
            res = self.client.get("/api/ai/steward/tasks/t-1")
            probe = self.client.get("/api/ai/steward/status")
        self.assertEqual(res.status_code, 404)
        self.assertIs(probe.json()["enabled"], False)  # 探针不跟着 404


class AuthzDecisionStackTests(unittest.TestCase):
    """铸卡 → 决断经真路由:open_request 铸的卡,POST approve/reject 真消费真流转。
    只桩鉴权(登录态)、闸(开)与 DB 游标 —— 路由编排/authz 状态机/错误信封全走真码。"""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        cls.client = TestClient(_app())

    def setUp(self):
        from tests.unit.test_steward_authz import _WRITE_TOOL, FakeCur, _World, _task_row
        from services.steward import registry, tools
        from services.steward.registry import StewardTool
        from services.agent.contracts import ToolResult

        self.world = _World(_task_row())
        cur = FakeCur(self.world)

        class _CurCM:
            def __enter__(self):
                return cur

            def __exit__(self, *a):
                return False

        spec = StewardTool(
            name=_WRITE_TOOL, desc="d", slots=(), handler=_WRITE_TOOL, risk=registry.RISK_WRITE
        )
        registry.TOOLS_BY_NAME[_WRITE_TOOL] = spec
        tools._HANDLERS[_WRITE_TOOL] = lambda _ctx, _args: ToolResult(ok=True, data={})
        self.addCleanup(registry.TOOLS_BY_NAME.pop, _WRITE_TOOL, None)
        self.addCleanup(tools._HANDLERS.pop, _WRITE_TOOL, None)

        from routes import steward_routes as sr
        from services.steward import store

        from routes import steward_common as sc

        actor = ({"id": "boss", "username": "boss"}, "t-1")
        patches = (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=actor),
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=actor),
            mock.patch.object(sr.feature_flags, "pearnly_ai_steward_enabled_for", lambda t: True),
            mock.patch.object(store, "ensure_once", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch("services.audit.store.insert_operation_log", mock.Mock()),
        )
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.cur = cur

    def _mint(self):
        from tests.unit.test_steward_authz import _ARGS, _WRITE_TOOL
        from services.steward import authz

        return authz.open_request(
            self.cur,
            tenant_id="t-1",
            task_id="task-1",
            tool=_WRITE_TOOL,
            args=dict(_ARGS),
            requested_by="u1",
        )

    def test_minted_card_approves_once_over_the_wire_then_409_used(self):
        from services.steward import store

        auth = self._mint()
        res = self.client.post(
            "/api/ai/steward/authorizations/approve", json={"token": auth["token"]}
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["task_id"], "task-1")
        self.assertEqual(body["authorization"]["status"], store.AUTH_APPROVED)
        self.assertNotIn("args_fp", body["authorization"])  # 指纹不外泄
        self.assertEqual(self.world.task["status"], store.TASK_RUNNING)  # 复跑待认领

        replay = self.client.post(
            "/api/ai/steward/authorizations/approve", json={"token": auth["token"]}
        )
        self.assertEqual(replay.status_code, 409)
        self.assertEqual(replay.json()["detail"], "steward.authz_used")

    def test_minted_card_rejects_over_the_wire_and_cancels_the_task(self):
        from services.steward import store

        auth = self._mint()
        res = self.client.post(
            "/api/ai/steward/authorizations/reject", json={"token": auth["token"]}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["authorization"]["status"], store.AUTH_REJECTED)
        self.assertEqual(self.world.task["status"], store.TASK_CANCELLED)
        self.assertEqual(self.world.task["error_code"], "steward.authz_rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)

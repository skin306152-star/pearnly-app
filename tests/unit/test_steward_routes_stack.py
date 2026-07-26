# -*- coding: utf-8 -*-
"""管家五端点走真 ASGI 栈(routes/steward_routes.py · B2-M1)。

直调 handler 跑绿不等于路由真接上 —— 模型/依赖/注册任一断都只在这层看得出来
(照 test_erp_bridge_routes.AsgiSmokeTests 先例)。锁:①匿名一律不给 200;②消息体
校验在框架层生效(空 text 422,不是等进业务层才发现);③闸关时经全栈仍是 404。
"""

from __future__ import annotations

import unittest
from unittest import mock

_ENDPOINTS = (
    ("get", "/api/ai/steward/status", None),
    ("post", "/api/ai/steward/sessions", {}),
    ("get", "/api/ai/steward/sessions/s-1", None),
    ("post", "/api/ai/steward/sessions/s-1/messages", {"text": "本期谁缺料"}),
    ("get", "/api/ai/steward/tasks/t-1", None),
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

    def _call(self, method, path, body):
        call = getattr(self.client, method)
        return call(path, json=body) if body is not None else call(path)

    def test_no_endpoint_serves_anonymous(self):
        for method, path, body in _ENDPOINTS:
            with self.subTest(path=path, method=method):
                res = self._call(method, path, body)
                self.assertIn(res.status_code, (401, 403, 404))

    def test_empty_message_rejected_by_request_model(self):
        res = self.client.post("/api/ai/steward/sessions/s-1/messages", json={"text": ""})
        self.assertEqual(res.status_code, 422)

    def test_gate_closed_is_404_for_a_logged_in_user(self):
        """闸关 = 对存量用户等于不存在。登录态由鉴权 helper 注入,闸判定走真请求路径。"""
        from routes import steward_routes as sr

        with (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=({"id": "u1"}, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=False
            ),
        ):
            res = self.client.get("/api/ai/steward/tasks/t-1")
            probe = self.client.get("/api/ai/steward/status")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(probe.json(), {"enabled": False})  # 探针不跟着 404


if __name__ == "__main__":
    unittest.main(verbosity=2)

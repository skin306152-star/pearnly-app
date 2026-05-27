# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 客户管理路由从 app.py 抽到 clients_routes.py。

锁定三件事(防搬迁回归):
  1. router 注册的路由 path+method 契约不变(防丢路由 / 改 URL · 含 P3 批量删除)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. _serialize_client 序列化契约不变(字段名 / 默认色 / datetime → isoformat)
"""

import datetime
import unittest

from clients_routes import _serialize_client, router


class ClientsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/clients"),
            ("POST", "/api/clients"),
            ("PATCH", "/api/clients/{client_id}"),
            ("DELETE", "/api/clients/{client_id}"),
            ("GET", "/api/clients/{client_id}/export"),
            # P3(2026-05-27)· 客户管理页横条多选批量删除
            ("POST", "/api/clients/batch-delete"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_clients_router(self):
        """防 include_router 漏挂 · app 必须能路由到 clients"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/clients", paths)
        self.assertIn("/api/clients/{client_id}/export", paths)

    def test_assign_client_route_stays_in_app(self):
        """assign_client 属 history 组 · 仍由 app.py 提供(未误删)"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/history/{history_id}/assign_client", paths)

    def test_serialize_client_defaults_and_isoformat(self):
        """默认色 #3b82f6 · None datetime → None · 数值兜底"""
        out = _serialize_client(
            {
                "id": 7,
                "name": "ACME",
                "color": None,
                "is_active": 1,
                "invoice_count": None,
                "total_amount": None,
                "last_invoice_at": None,
                "created_at": None,
            }
        )
        self.assertEqual(out["id"], 7)
        self.assertEqual(out["color"], "#3b82f6")
        self.assertEqual(out["invoice_count"], 0)
        self.assertEqual(out["total_amount"], 0.0)
        self.assertTrue(out["is_active"])
        self.assertIsNone(out["created_at"])

    def test_serialize_client_datetime_to_isoformat(self):
        """datetime 字段 → isoformat 字符串"""
        dt = datetime.datetime(2026, 5, 24, 9, 30, 0)
        out = _serialize_client({"id": 1, "created_at": dt, "last_invoice_at": dt})
        self.assertEqual(out["created_at"], dt.isoformat())
        self.assertEqual(out["last_invoice_at"], dt.isoformat())


if __name__ == "__main__":
    unittest.main()

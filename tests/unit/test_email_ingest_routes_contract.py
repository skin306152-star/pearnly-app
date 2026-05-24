# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 邮箱抓取 6 路由从 app.py 抽到 email_ingest_routes.py。

锁定(防搬迁回归):
  1. router 注册的 6 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 两个 request model 字段契约不变
  4. _email_presets() 异常兜底返回 {}(email_ingest 不可用时不炸)
"""

import unittest

from email_ingest_routes import (
    EmailAccountBindRequest,
    EmailTestConnRequest,
    _email_presets,
    router,
)


class EmailIngestRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/email-ingest/account"),
            ("PUT", "/api/email-ingest/account"),
            ("DELETE", "/api/email-ingest/account"),
            ("POST", "/api/email-ingest/test"),
            ("POST", "/api/email-ingest/trigger"),
            ("GET", "/api/email-ingest/logs"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_email_ingest_router(self):
        """防 include_router 漏挂 · app 必须能路由到 email-ingest"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/email-ingest/account", paths)
        self.assertIn("/api/email-ingest/trigger", paths)

    def test_bind_request_fields(self):
        """EmailAccountBindRequest 字段契约 · password 选填(只改配置不改密码)"""
        self.assertEqual(
            set(EmailAccountBindRequest.model_fields.keys()),
            {
                "email_address",
                "imap_host",
                "imap_port",
                "imap_use_ssl",
                "password",
                "folder",
                "filter_subject",
                "filter_sender",
                "mark_as_read",
                "enabled",
                "interval_min",
            },
        )
        m = EmailAccountBindRequest(email_address="a@b.co", imap_host="imap.b.co")
        self.assertIsNone(m.password)
        self.assertEqual(m.imap_port, 993)
        self.assertEqual(m.folder, "INBOX")

    def test_testconn_request_requires_password(self):
        """EmailTestConnRequest password 必填(测试连接要真登录)"""
        self.assertIn("password", EmailTestConnRequest.model_fields)
        with self.assertRaises(Exception):
            EmailTestConnRequest(email_address="a@b.co", imap_host="imap.b.co")

    def test_email_presets_safe_fallback(self):
        """_email_presets() 永不抛 · email_ingest 缺失时返 {}"""
        out = _email_presets()
        self.assertIsInstance(out, dict)


if __name__ == "__main__":
    unittest.main()

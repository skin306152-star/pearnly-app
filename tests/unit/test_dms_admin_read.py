# -*- coding: utf-8 -*-
"""DMS 权威只读(services/erp/dms_admin_read.py):凭据来源、只读闸、fail closed。

锁产品契约:配了独立管理员凭据组 → 读取借管理员会话(一个读取块只解析一次);未配 → 原
销售会话逐字节不变;配了但管理员登录失败 → 明确失败关闭,绝不静默退回销售的不完整视图;
权威会话只读,写路径一律被拒;退出后 client 不留管理员 transport 态。
"""

import unittest
from types import SimpleNamespace
from unittest import mock

from services.erp import dms_admin_read as ar
from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError

_BASE = "https://tenant.example/dms/"


def _resp(text="", status=200):
    return SimpleNamespace(text=text, status_code=status, content=str(text).encode())


class _SpyTransport:
    """记录全部取数;posts 回调按 URL 造假响应(零网络)。"""

    def __init__(self, name, posts=None, posts_status=200):
        self.name = name
        self.calls = []
        self._posts = posts or (lambda url, data: _resp(""))
        self.posts_status = posts_status

    def get(self, url, timeout_ms=None):
        self.calls.append(("GET", url, None))
        return _resp("")

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.calls.append(("POST", url, dict(data or {})))
        if self.posts_status != 200:
            return _resp("denied", self.posts_status)
        return self._posts(url, data or {})

    def paths(self):
        return [url for _method, url, _data in self.calls]


class _Factory:
    """管理员 transport 的惰性工厂:计数调用(1 次 = 一次管理员登录/transport 解析)。"""

    def __init__(self, transport=None, error=None):
        self.calls = 0
        self._transport = transport
        self._error = error

    def __call__(self):
        self.calls += 1
        if self._error:
            raise self._error
        return self._transport


class AuthoritativeReadClientTests(unittest.TestCase):
    def test_without_admin_keeps_the_original_client(self):
        client = DMSClient(_SpyTransport("sales"), _BASE)
        self.assertIs(ar.authoritative_read_client(client), client)
        self.assertFalse(ar.admin_read_available(client))

    def test_configured_but_unresolved_admin_does_not_open_a_session(self):
        """配了管理员只作「要不要走管理员」的判据:判据本身绝不触发登录。"""
        factory = _Factory()
        client = DMSClient(_SpyTransport("sales"), _BASE, admin_transport=factory)
        self.assertTrue(ar.admin_read_available(client))
        self.assertEqual(factory.calls, 0)

    def test_reader_is_a_distinct_client_on_the_admin_transport(self):
        admin = _SpyTransport("admin")
        factory = _Factory(admin)
        sales = _SpyTransport("sales")
        client = DMSClient(sales, _BASE, admin_transport=factory)
        reader = ar.authoritative_read_client(client)
        self.assertIsNot(reader, client)
        self.assertEqual(factory.calls, 1)  # 只解析一次
        self.assertEqual(reader.base_url, client.base_url)
        reader.transport.post(f"{_BASE}cus/form.php", data={"status": "e", "id": "95"})
        self.assertEqual(admin.paths(), [f"{_BASE}cus/form.php"])
        self.assertEqual(sales.calls, [])  # 权威读不碰销售会话

    def test_second_reader_reuses_the_same_admin_transport(self):
        """同一读取块内多次取 reader 不重复登录(工厂缓存)。"""
        admin = _SpyTransport("admin")
        factory = _Factory(admin)
        client = DMSClient(_SpyTransport("sales"), _BASE, admin_transport=factory)
        first = ar.authoritative_read_client(client)
        second = ar.authoritative_read_client(client)
        # 只读闸每次包一层,但底下是同一条管理员 transport(不重开会话)。
        self.assertIs(first.transport._transport, second.transport._transport)  # noqa: SLF001
        self.assertEqual(factory.calls, 1)
        self.assertEqual(len(admin.calls), 0)

    def test_admin_login_failure_propagates_and_is_never_swallowed(self):
        class AdminAuthError(RuntimeError):
            pass

        factory = _Factory(error=AdminAuthError("admin login bounced"))
        client = DMSClient(_SpyTransport("sales"), _BASE, admin_transport=factory)
        with self.assertRaises(AdminAuthError):
            ar.authoritative_read_client(client)
        self.assertEqual(factory.calls, 1)

    def test_require_admin_fails_closed_without_admin_credentials(self):
        client = DMSClient(_SpyTransport("sales"), _BASE)
        with self.assertRaises(DMSClientError) as ctx:
            ar.authoritative_read_client(client, require_admin=True)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_NO_ADMIN_CREDS")

    def test_read_only_gate_allows_only_read_paths(self):
        admin = _SpyTransport("admin")
        client = DMSClient(_SpyTransport("sales"), _BASE, admin_transport=_Factory(admin))
        reader = ar.authoritative_read_client(client)
        reader.transport.post(f"{_BASE}drfcbc/form.php", data={"status": "n"})
        reader.transport.post(f"{_BASE}cus/form.php?id=9", data={"status": "e", "id": "9"})
        self.assertEqual(admin.paths(), [f"{_BASE}drfcbc/form.php", f"{_BASE}cus/form.php?id=9"])
        for write_path in ("cus/new.php", "cus/edit.php", "drfcbc/new.php", "upload.php"):
            with self.subTest(write_path=write_path):
                with self.assertRaises(DMSClientError) as ctx:
                    reader.transport.post(f"{_BASE}{write_path}", data={"a": "1"})
                self.assertEqual(ctx.exception.error_code, "ERR_DMS_TECHNICAL")
        with self.assertRaises(DMSClientError):
            reader.transport.post(
                f"{_BASE}cus/form.php",
                data={"a": "1"},
                files={"f": ("x.jpg", b"bytes", "image/jpeg")},
            )
        self.assertEqual(len(admin.calls), 2)  # 被拒的请求一个都没落到管理员会话上

    def test_unrestricted_reader_has_no_gate_when_explicitly_requested(self):
        admin = _SpyTransport("admin")
        client = DMSClient(_SpyTransport("sales"), _BASE, admin_transport=_Factory(admin))
        reader = ar.authoritative_read_client(client, read_only=False)
        self.assertIs(reader.transport, admin)


class AuthoritativeReadSessionTests(unittest.TestCase):
    def test_session_swaps_to_admin_and_restores_sales_even_on_error(self):
        sales = _SpyTransport("sales")
        admin = _SpyTransport("admin")
        client = DMSClient(sales, _BASE, admin_transport=_Factory(admin))
        with self.assertRaises(ValueError):
            with ar.authoritative_read_session(client) as session:
                self.assertEqual(session.transport.post(f"{_BASE}cus/form.php").text, "")
                self.assertEqual(admin.paths(), [f"{_BASE}cus/form.php"])
                raise ValueError("boom")
        self.assertIs(client.transport, sales)  # 异常路径也必须换回销售 transport

    def test_session_without_admin_yields_the_same_client(self):
        sales = _SpyTransport("sales")
        client = DMSClient(sales, _BASE)
        with ar.authoritative_read_session(client) as session:
            self.assertIs(session, client)
            self.assertIs(session.transport, sales)
        self.assertIs(client.transport, sales)

    def test_writer_session_inside_read_session_does_not_leave_admin_state(self):
        """权威只读块里跑客户建档写(自带 admin 语义)也不能把 client 留在管理员态。"""
        sales = _SpyTransport("sales")
        admin = _SpyTransport("admin")
        client = DMSClient(sales, _BASE, admin_transport=_Factory(admin))
        seen = {}

        def _fake_save(self, **kwargs):
            seen["transport"] = self.transport
            seen["wrote_via_admin_session"] = self.transport._transport is admin  # noqa: SLF001
            return "95", False

        with mock.patch.object(DMSClient, "save_customer", _fake_save):
            with ar.authoritative_read_session(client):
                client.save_customer(fields={"name": "x"}, mode="overwrite", customer_id="95")
        self.assertTrue(seen["wrote_via_admin_session"])  # 写发生在管理员凭据组会话上
        self.assertIs(client.transport, sales)  # 退出后不留管理员态


if __name__ == "__main__":
    unittest.main()

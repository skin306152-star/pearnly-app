# -*- coding: utf-8 -*-
"""A1 守门:MR.ERP 会话串行锁。

根因(实测坐实):老 PHP 单账号单会话 · 2 worker 同推同账号 → 一个被踢 ERR_AUTH。
本测试锁定:
  1. lock key 在不同账号上不同 · 同账号稳定 · 落 signed 64-bit 范围;
  2. 无 DB 时优雅降级(yield False · 不抛)→ 单测/本地天然 no-op;
  3. MRERPAdapter 默认 serialize_sessions=True · 且可显式关掉。
"""

import unittest
import os
from unittest import mock

from services.erp.session_lock import (
    MrerpSessionLockUnavailable,
    _account_lock_key,
    dms_booking_scope_key,
    mrerp_booking_lock,
    mrerp_session_lock,
)


class AccountLockKeyTests(unittest.TestCase):
    def test_deterministic_and_account_scoped(self):
        a = _account_lock_key("https://www.mrerp4sme.com|test01")
        b = _account_lock_key("https://www.mrerp4sme.com|test01")
        c = _account_lock_key("https://www.mrerp4sme.com|other")
        self.assertEqual(a, b)  # 同账号稳定
        self.assertNotEqual(a, c)  # 不同账号不同 → 互不阻塞

    def test_signed_64bit_range(self):
        for acct in ("a|b", "x" * 200, "https://www.mrerp4sme.com|test01"):
            k = _account_lock_key(acct)
            self.assertGreaterEqual(k, -(2**63))
            self.assertLess(k, 2**63)


class GracefulDegradeTests(unittest.TestCase):
    def test_no_db_yields_false_not_raise(self):
        """get_pool 抛(没 DATABASE_URL)→ 锁降级放行 · 不阻断业务。"""
        with mock.patch("core.db.get_pool", side_effect=RuntimeError("no DATABASE_URL")):
            with mrerp_session_lock("acct|x", timeout_sec=1) as got:
                self.assertFalse(got)  # 没拿到真锁 · 但放行

    def test_trylock_exception_yields_false(self):
        fake_conn = mock.MagicMock()
        fake_conn.cursor.side_effect = RuntimeError("conn broke")
        fake_pool = mock.MagicMock()
        fake_pool.getconn.return_value = fake_conn
        with mock.patch("core.db.get_pool", return_value=fake_pool):
            with mrerp_session_lock("acct|x", timeout_sec=1) as got:
                self.assertFalse(got)
        # 连接必须被归还
        fake_pool.putconn.assert_called_once_with(fake_conn)


class CloudFailClosedTests(unittest.TestCase):
    def test_connection_failure_prevents_session_body(self):
        for role in ("web", "worker"):
            with self.subTest(role=role), mock.patch.dict(os.environ, PEARNLY_RUNTIME_ROLE=role):
                with mock.patch("core.db.get_pool", side_effect=RuntimeError("no DB")):
                    with self.assertRaises(MrerpSessionLockUnavailable):
                        with mrerp_session_lock("test-account"):
                            self.fail("browser must not start")

    def test_query_failure_prevents_session_body_and_returns_connection(self):
        pool = mock.MagicMock()
        pool.getconn.return_value.cursor.side_effect = RuntimeError("query failed")
        with (
            mock.patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            mock.patch("core.db.get_pool", return_value=pool),
        ):
            with self.assertRaises(MrerpSessionLockUnavailable):
                with mrerp_session_lock("test-account"):
                    self.fail("browser must not start")
        pool.putconn.assert_called_once_with(pool.getconn.return_value)

    def test_timeout_prevents_session_body(self):
        pool = mock.MagicMock()
        pool.getconn.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            False,
        )
        with (
            mock.patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            mock.patch("core.db.get_pool", return_value=pool),
        ):
            with self.assertRaisesRegex(MrerpSessionLockUnavailable, "timeout"):
                with mrerp_session_lock("test-account", timeout_sec=0):
                    self.fail("browser must not start")


class CloudAdapterLockTests(unittest.TestCase):
    def test_browser_adapter_cannot_swallow_lock_error_or_disable_cloud_lock(self):
        from services.erp.mrerp_adapter import MRERPAdapter

        for serialize in (True, False):
            with (
                self.subTest(serialize=serialize),
                mock.patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            ):
                with (
                    mock.patch("services.erp.mrerp_adapter.mrerp_session_lock") as lock,
                    mock.patch("services.erp.mrerp_adapter.BrowserSession") as browser,
                ):
                    lock.return_value.__enter__.side_effect = MrerpSessionLockUnavailable("blocked")
                    adapter = MRERPAdapter(
                        login_url="https://test.invalid",
                        username="u",
                        password="p",
                        serialize_sessions=serialize,
                    )
                    with self.assertRaises(MrerpSessionLockUnavailable):
                        adapter.__enter__()
                    browser.assert_not_called()

    def test_http_adapter_cannot_swallow_lock_error_or_disable_cloud_lock(self):
        from services.erp.mrerp_http.adapter import MrErpHttpAdapter

        for serialize in (True, False):
            with (
                self.subTest(serialize=serialize),
                mock.patch.dict(os.environ, PEARNLY_RUNTIME_ROLE="worker"),
            ):
                with (
                    mock.patch("services.erp.mrerp_http.adapter.mrerp_session_lock") as lock,
                    mock.patch("services.erp.mrerp_http.adapter.MrErpSession") as session,
                ):
                    lock.return_value.__enter__.side_effect = MrerpSessionLockUnavailable("blocked")
                    adapter = MrErpHttpAdapter(
                        login_url="https://test.invalid",
                        username="u",
                        password="p",
                        serialize_sessions=serialize,
                    )
                    with self.assertRaises(MrerpSessionLockUnavailable):
                        adapter.__enter__()
                    session.assert_not_called()


class DmsBookingScopeKeyTests(unittest.TestCase):
    """账套级锁 key:同账套不同账号同 key、不同账套不同 key、URL 归一化、不泄漏密码。"""

    def _ep(self, **over):
        cfg = {
            "system_url": "https://dms.example.com/dms/",
            "comidyear": 6,
            "seldb": 1,
            **over,
        }
        return {"id": "E1", "config": cfg}

    def test_same_account_set_ignores_username(self):
        a = dms_booking_scope_key(self._ep())
        b = dms_booking_scope_key(self._ep(username_enc="user-a", password_enc="pw-a"))
        self.assertEqual(a, b)  # 同账套不同销售账号 → 同一把共享锁

    def test_account_set_hints_do_not_fake_split_dms_scope(self):
        base = dms_booking_scope_key(self._ep())
        self.assertEqual(base, dms_booking_scope_key(self._ep(comidyear=15)))
        self.assertEqual(base, dms_booking_scope_key(self._ep(seldb=2)))

    def test_index_php_and_base_url_normalize_same(self):
        base = dms_booking_scope_key(self._ep(system_url="https://dms.example.com/dms/"))
        full = dms_booking_scope_key(self._ep(system_url="https://dms.example.com/dms/index.php"))
        self.assertEqual(base, full)

    def test_defaults_apply_when_missing(self):
        k = dms_booking_scope_key({"config": {"system_url": "https://dms.example.com/dms"}})
        self.assertEqual(k, "https://dms.example.com/dms")

    def test_missing_url_uses_dms_default(self):
        missing = dms_booking_scope_key({"config": {}})
        explicit = dms_booking_scope_key(
            {"config": {"system_url": "https://www.mrerp4sme.com/dms/index.php"}}
        )
        self.assertEqual(missing, "https://www.mrerp4sme.com/dms")
        self.assertEqual(missing, explicit)

    def test_key_does_not_leak_password(self):
        k = dms_booking_scope_key(self._ep(password_enc="sup3r-secret-pw"))
        self.assertNotIn("sup3r-secret-pw", k)


class DmsBookingLockTests(unittest.TestCase):
    def test_no_db_yields_false_not_raise(self):
        """get_pool 抛(没 DATABASE_URL)→ 账套锁降级放行 · 不阻断建单。"""
        with mock.patch("core.db.get_pool", side_effect=RuntimeError("no DATABASE_URL")):
            with mrerp_booking_lock(
                {"config": {"system_url": "https://dms.example.com/dms/"}}, timeout_sec=1
            ) as got:
                self.assertFalse(got)


class AdapterWiringTests(unittest.TestCase):
    def test_serialize_sessions_default_true(self):
        from services.erp.mrerp_adapter import MRERPAdapter

        ad = MRERPAdapter(login_url="https://x", username="u", password="p")
        self.assertTrue(ad.serialize_sessions)

    def test_serialize_sessions_can_disable(self):
        from services.erp.mrerp_adapter import MRERPAdapter

        ad = MRERPAdapter(
            login_url="https://x", username="u", password="p", serialize_sessions=False
        )
        self.assertFalse(ad.serialize_sessions)


if __name__ == "__main__":
    unittest.main()

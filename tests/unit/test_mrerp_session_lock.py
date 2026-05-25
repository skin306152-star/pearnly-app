# -*- coding: utf-8 -*-
"""A1 守门:MR.ERP 会话串行锁。

根因(实测坐实):老 PHP 单账号单会话 · 2 worker 同推同账号 → 一个被踢 ERR_AUTH。
本测试锁定:
  1. lock key 在不同账号上不同 · 同账号稳定 · 落 signed 64-bit 范围;
  2. 无 DB 时优雅降级(yield False · 不抛)→ 单测/本地天然 no-op;
  3. MRERPAdapter 默认 serialize_sessions=True · 且可显式关掉。
"""

import unittest
from unittest import mock

from services.erp.session_lock import _account_lock_key, mrerp_session_lock


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
        with mock.patch("db.get_pool", side_effect=RuntimeError("no DATABASE_URL")):
            with mrerp_session_lock("acct|x", timeout_sec=1) as got:
                self.assertFalse(got)  # 没拿到真锁 · 但放行

    def test_trylock_exception_yields_false(self):
        fake_conn = mock.MagicMock()
        fake_conn.cursor.side_effect = RuntimeError("conn broke")
        fake_pool = mock.MagicMock()
        fake_pool.getconn.return_value = fake_conn
        with mock.patch("db.get_pool", return_value=fake_pool):
            with mrerp_session_lock("acct|x", timeout_sec=1) as got:
                self.assertFalse(got)
        # 连接必须被归还
        fake_pool.putconn.assert_called_once_with(fake_conn)


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
